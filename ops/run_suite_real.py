"""Resume the frozen real suite with bounded jobs and immediate post-run reviews."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from beforestep.generation import client as C
from run_suite_imagination import require_real_gates, sources
from suite_lux_budget import Budget

ROOT = Path(__file__).resolve().parents[1]


def assert_not_live(pid):
    if not pid:
        return
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    raise RuntimeError(f'Existing process {pid} may still be live; inspect before resuming')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--regression', required=True)
    parser.add_argument('--standins', default='evidence/suite/standins/summary.json')
    parser.add_argument('--out', default='outputs/suite/real')
    parser.add_argument('--reviews', default='outputs/suite/reviews')
    parser.add_argument('--baselines', default='outputs/suite/baselines-crater-target/pool.json')
    parser.add_argument('--budget', default='outputs/generation/r2-budget.json')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    freeze_path = ROOT / 'config/suite/frozen.json'
    frozen = json.loads(freeze_path.read_text())
    rows = [r for r in frozen['scenes'] if not r.get('anchor')]
    # Check all paid prerequisites before creating even a run directory. The
    # child repeats these checks immediately before its production invocation.
    gates = require_real_gates(rows[0]['scene'], freeze_path, ROOT / args.regression, ROOT / args.standins)
    source = sources()
    assert all(C.sha(ROOT / r['config']) == r['config_sha256'] for r in rows)
    output = (ROOT / args.out).resolve()
    assert output.is_relative_to(ROOT / 'outputs')
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    scenes = [r['scene'] for r in rows]
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-real-processes/v1', 'source_sha256': source,
        'frozen_scenes': scenes, 'gates': gates, 'budget_ledger': args.budget, 'jobs': {}}
    assert report['source_sha256'] == source and report['frozen_scenes'] == scenes
    lock, stop = threading.Lock(), threading.Event()

    def save():
        C.atomic_json(ledger, report)

    def run(row):
        scene = row['scene']
        if stop.is_set():
            return
        previous = report['jobs'].get(scene)
        if previous and previous['status'] == 'complete':
            return
        if previous:
            assert_not_live(previous.get('pid') if previous['status'] == 'running' else None)
        container = output / scene
        chain_path = container / 'chain.json'
        if chain_path.exists():
            chain = json.loads(chain_path.read_text())
            assert_not_live(chain.get('live_process', {}).get('pid'))
        command = [sys.executable, 'ops/run_suite_imagination.py', '--scene', scene,
                   '--mode', 'real', '--out', str(container.relative_to(ROOT)),
                   '--regression', args.regression, '--standins', args.standins, '--budget', args.budget]
        log = output / (scene + '.log')
        with log.open('a') as stream:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                     stdout=stream, stderr=subprocess.STDOUT)
            with lock:
                report['jobs'][scene] = {'status': 'running', 'pid': child.pid, 'command': command,
                                        'log': str(log.relative_to(ROOT))}
                save()
            code = child.wait()
        chain = json.loads(chain_path.read_text()) if chain_path.exists() else {}
        review_code = None
        if code == 0 and chain.get('completed'):
            # This scene's optimistic baseline must use the corrected source;
            # the independently running global baseline job is never replaced.
            while True:
                baseline = json.loads((ROOT / args.baselines).read_text())
                assert baseline['source_sha256'] == source
                optimistic = baseline['scenes'][scene]['runs'].get('optimistic')
                if optimistic:
                    assert optimistic['exit_code'] == 0 and optimistic['summary']
                    break
                time.sleep(5)
            review_command = [sys.executable, 'ops/evaluate_suite_scene.py', '--scene', scene,
                              '--real-run', str((container / 'imagination').relative_to(ROOT)),
                              '--optimistic-run', optimistic['run'], '--out', args.reviews + '/' + scene]
            with (output / (scene + '-review.log')).open('a') as stream:
                review_code = subprocess.call(review_command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        else:
            stop.set()
        with lock:
            report['jobs'][scene].update(status='complete' if code == 0 and review_code == 0 else 'failed',
                                       exit_code=code, review_exit_code=review_code,
                                       summary=chain.get('summary'), run_id=chain.get('run_id'),
                                       chain=str(chain_path.relative_to(ROOT)))
            save()
        print(json.dumps({'scene': scene, 'exit_code': code, 'review_exit_code': review_code,
                          'summary': chain.get('summary')}, ensure_ascii=False), flush=True)

    save()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run, r) for r in rows]
        for future in as_completed(futures):
            future.result()
    report['completed'] = len(report['jobs']) == len(rows) and all(r['status'] == 'complete' for r in report['jobs'].values())
    budget_path = ROOT / args.budget
    report['paid_tasks'] = Budget.usage(json.loads(budget_path.read_text())) if budget_path.exists() else 0
    report['budget_limit'] = 360
    save()
    raise SystemExit(0 if report['completed'] else 2 if report['paid_tasks'] >= 360 else 1)


if __name__ == '__main__':
    main()
