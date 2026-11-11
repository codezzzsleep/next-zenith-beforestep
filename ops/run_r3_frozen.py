"""Execute the fixed twelve R3 reruns after both offline gates pass."""
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
from run_suite_imagination import sources

ROOT = C.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regression', required=True)
    ap.add_argument('--standins', default='evidence/reviews/beforestep_r3/standins/summary.json')
    ap.add_argument('--out', default='outputs/r3/frozen')
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    frozen = json.loads((ROOT / 'config/suite/frozen.json').read_text())
    originals = {r['scene']: r for r in json.loads((ROOT / 'evidence/suite/summary.json').read_text())['scenes']}
    plan = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    scenes = [r['scene'] for r in frozen['scenes']]
    assert scenes == [r['scene'] for r in plan['frozen']]
    output = ROOT / a.out
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-frozen-processes/v1', 'source_sha256': sources(),
        'scenes': scenes, 'jobs': {}, 'status': 'waiting_offline_gates', 'post_result_revision': True}
    assert report['source_sha256'] == sources() and report['scenes'] == scenes
    C.atomic_json(ledger, report)
    while not (ROOT / a.standins).exists():
        time.sleep(5)
    standins = json.loads((ROOT / a.standins).read_text())
    assert standins['all_passed'] and standins['source_sha256'] == sources(), 'Offline strict chains failed; no paid experiments'
    regression = json.loads((ROOT / a.regression).read_text())
    assert regression['passed'] and regression['source_sha256'] == sources()
    # Expectations and code must be visible to the owner before real execution.
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    plan_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--',
                                           'evidence/reviews/beforestep_r3/experiment-plan.json'], cwd=ROOT, text=True).strip()
    assert plan_commit
    subprocess.run(['git', 'merge-base', '--is-ancestor', plan_commit, remote], cwd=ROOT, check=True)
    lock, stop = threading.Lock(), threading.Event()
    report.update(status='running', plan_commit=plan_commit, remote_main_at_start=remote)
    C.atomic_json(ledger, report)

    def run(scene):
        if stop.is_set():
            return
        previous = report['jobs'].get(scene)
        if previous and previous['status'] == 'complete':
            return
        if previous and previous.get('status') == 'running':
            try:
                os.kill(previous['pid'], 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError(f'Existing scene process still exists: {previous["pid"]}')
        folder = output / scene
        original = originals[scene]['runs']['imagination']['run']
        reuse = str((ROOT / a.regression).parent.relative_to(ROOT) / 'replay') if scene == 'stress_v8' else original
        command = [sys.executable, 'ops/run_r3_chain.py', '--scene', scene, '--mode', 'real',
                   '--out', str(folder.relative_to(ROOT)), '--regression', a.regression,
                   '--standins', a.standins, '--first-reuse', reuse]
        with (output / (scene + '.log')).open('a') as log:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                     stdout=log, stderr=subprocess.STDOUT)
            with lock:
                report['jobs'][scene] = {'status': 'running', 'pid': child.pid, 'command': command,
                                         'original_r1_r2_run': original}
                C.atomic_json(ledger, report)
            code = child.wait()
        chain_path = folder / 'chain.json'
        chain = json.loads(chain_path.read_text()) if chain_path.exists() else {}
        if code != 0:
            stop.set()
        with lock:
            report['jobs'][scene].update(status='complete' if code == 0 and chain.get('completed') else 'failed',
                                         exit_code=code, summary=chain.get('summary'), run_id=chain.get('run_id'),
                                         chain=str(chain_path.relative_to(ROOT)))
            C.atomic_json(ledger, report)
        print(json.dumps({'scene': scene, 'exit_code': code, 'summary': chain.get('summary')}, ensure_ascii=False), flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as executor:
        futures = [executor.submit(run, scene) for scene in scenes]
        for future in as_completed(futures):
            future.result()
    report['completed'] = len(report['jobs']) == len(scenes) and all(r['status'] == 'complete' for r in report['jobs'].values())
    report['status'] = 'complete' if report['completed'] else 'needs_inspection'
    C.atomic_json(ledger, report)
    raise SystemExit(0 if report['completed'] else 1)


if __name__ == '__main__':
    main()
