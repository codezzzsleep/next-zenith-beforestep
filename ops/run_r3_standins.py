"""Wait for the exact source regression, then check both R3 offline chains."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from beforestep.generation import client as C
from run_suite_imagination import sources

ROOT = C.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regression', required=True)
    ap.add_argument('--out', default='outputs/qa/r3/S2/standins')
    a = ap.parse_args()
    output = ROOT / a.out
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-standins/v1', 'source_sha256': sources(),
        'regression': a.regression, 'paid_tasks': 0, 'jobs': {}, 'status': 'waiting_regression'}
    assert report['source_sha256'] == sources()
    C.atomic_json(ledger, report)
    while True:
        regression = json.loads((ROOT / a.regression).read_text())
        assert regression['source_sha256'] == report['source_sha256']
        if 'passed' in regression:
            assert regression['passed'], 'R1 regression did not pass; no stand-in experiments started'
            break
        time.sleep(5)
    report['status'] = 'running'
    C.atomic_json(ledger, report)
    jobs = [(scene, mode) for scene in ('stress_v8', 'suite_r2_v4_F1_020') for mode in ('truth', 'registered')]

    def run(scene, mode):
        key = scene + '-' + mode
        folder = output / key
        policy_run = folder / 'imagination_strict'
        if (policy_run / 'summary.json').exists():
            return key, {'exit_code': 0, 'run': str(policy_run.relative_to(ROOT)),
                         'summary': json.loads((policy_run / 'summary.json').read_text())}
        if folder.exists():
            raise RuntimeError(f'Partial stand-in exists: {folder}; inspect and preserve before retry')
        folder.mkdir()
        if mode == 'truth':
            command = [sys.executable, '-m', 'beforestep', 'run', '--scene', scene,
                       '--controller-model', 'rules', '--policy', 'imagination_strict',
                       '--imagine', 'truth', '--out', str(folder)]
        else:
            command = [sys.executable, 'ops/run_r3_chain.py', '--scene', scene, '--mode', 'standin',
                       '--regression', a.regression, '--out', str(folder.relative_to(ROOT))]
        with (folder / 'driver.log').open('w') as log:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                     stdout=log, stderr=subprocess.STDOUT)
            C.atomic_json(folder / 'process.json', {'pid': child.pid, 'command': command})
            code = child.wait()
        summary = json.loads((policy_run / 'summary.json').read_text()) if (policy_run / 'summary.json').exists() else None
        return key, {'command': command, 'exit_code': code, 'run': str(policy_run.relative_to(ROOT)),
                     'summary': summary}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, *job) for job in jobs if '-'.join(job) not in report['jobs']]
        for future in as_completed(futures):
            key, row = future.result()
            summary = row['summary']
            row['passed'] = bool(row['exit_code'] == 0 and summary and summary['collision'] is None and
                                 (summary['result'] == 'arrived' if key.startswith('stress_v8-') else summary['result'] != 'collision'))
            report['jobs'][key] = row
            C.atomic_json(ledger, report)
            print(json.dumps({'job': key, 'passed': row['passed'], 'summary': summary}), flush=True)
    report['status'] = 'complete'
    report['all_passed'] = len(report['jobs']) == 4 and all(r['passed'] for r in report['jobs'].values())
    C.atomic_json(ledger, report)
    public = ROOT / 'evidence/reviews/beforestep_r3/standins/summary.json'
    C.atomic_json(public, report)
    raise SystemExit(0 if report['all_passed'] else 1)


if __name__ == '__main__':
    main()
