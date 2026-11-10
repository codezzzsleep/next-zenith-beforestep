"""Persist all-family offline chain, review and gate receipts across interruptions."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

from beforestep.generation import client as C

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--regression', required=True)
    parser.add_argument('--selection', help='Optional family -> frozen decisive scene JSON')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    frozen = json.loads((ROOT / 'config/suite/frozen.json').read_text())
    selected = json.loads((ROOT / args.selection).read_text()) if args.selection else {
        family: next(r['scene'] for r in frozen['scenes']
                     if r['family'] == family and r['classification'] == 'decisive' and not r.get('anchor'))
        for family in frozen['families']}
    assert set(selected) == set(frozen['families'])
    rows = {f: next(r for r in frozen['scenes'] if r['scene'] == scene)
            for f, scene in selected.items()}
    assert all(row['family'] == f and row['classification'] == 'decisive' for f, row in rows.items())
    output = (ROOT / args.out).resolve()
    assert output.is_relative_to(ROOT / 'outputs')
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    source = {str(p.relative_to(ROOT)): C.sha(p) for p in sorted((ROOT / 'src').rglob('*.py'))}
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-standin-processes/v1', 'selection': selected,
        'source_sha256': source, 'paid_tasks': 0, 'jobs': {}}
    assert report['source_sha256'] == source and report['selection'] == selected
    lock = threading.Lock()
    C.atomic_json(output / 'selection.json', {
        f: str((output / scene / 'imagination').relative_to(ROOT)) for f, scene in selected.items()})

    def save():
        C.atomic_json(ledger, report)

    def run(family, row):
        scene = row['scene']
        container = output / scene
        if family in report['jobs']:
            old = report['jobs'][family]
            if old['status'] == 'complete':
                return family, old['exit_code']
            pid = old.get('pid')
            if pid:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise RuntimeError(f'Stand-in child {pid} may still be live; inspect before resuming')
            chain = container / 'chain.json'
            if chain.exists():
                child = json.loads(chain.read_text()).get('live_process', {}).get('pid')
                if child:
                    try:
                        os.kill(child, 0)
                    except ProcessLookupError:
                        pass
                    else:
                        raise RuntimeError(f'Physical child {child} may still be live; inspect before resuming')
        command = [sys.executable, 'ops/run_suite_imagination.py', '--scene', scene,
                   '--mode', 'standin', '--out', str(container.relative_to(ROOT)),
                   '--regression', args.regression]
        log = output / (scene + '.log')
        with log.open('a') as stream:
            process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                       stdout=stream, stderr=subprocess.STDOUT)
            with lock:
                report['jobs'][family] = {'scene': scene, 'command': command, 'pid': process.pid,
                                         'status': 'running', 'log': str(log.relative_to(ROOT))}
                save()
            code = process.wait()
        chain = container / 'chain.json'
        result = json.loads(chain.read_text()) if chain.exists() else {}
        review_code = None
        if result.get('completed'):
            review_command = [sys.executable, 'ops/evaluate_suite_scene.py', '--scene', scene,
                              '--real-run', str((container / 'imagination').relative_to(ROOT)),
                              '--optimistic-run', row['runs']['optimistic']['run'],
                              '--out', str((container / 'review').relative_to(ROOT))]
            with (output / (scene + '-review.log')).open('a') as stream:
                review_code = subprocess.call(review_command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        with lock:
            report['jobs'][family].update(status='complete', exit_code=code, review_exit_code=review_code,
                                         summary=result.get('summary'), chain=str(chain.relative_to(ROOT)))
            save()
        print(json.dumps({'family': family, 'exit_code': code, 'review_exit_code': review_code,
                          'summary': result.get('summary')}, ensure_ascii=False), flush=True)
        return family, code

    save()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run, f, row) for f, row in rows.items()]
        for future in as_completed(futures):
            future.result()
    report['completed'] = True
    save()
    if all(r['exit_code'] == 0 and r['review_exit_code'] == 0 for r in report['jobs'].values()):
        command = [sys.executable, 'ops/check_suite_standins.py', '--selection',
                   str((output / 'selection.json').relative_to(ROOT))]
        report['gate_exit_code'] = subprocess.call(command, cwd=ROOT)
    else:
        report['gate_exit_code'] = 1
    save()
    raise SystemExit(report['gate_exit_code'])


if __name__ == '__main__':
    main()
