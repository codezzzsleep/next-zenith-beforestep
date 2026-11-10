"""Stream every frozen scene's rejected counterfactuals after its real review."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from beforestep.generation.client import atomic_json
from run_suite_imagination import sources

ROOT = Path(__file__).resolve().parents[1]


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--producer-pid', type=int, required=True)
    parser.add_argument('--real-root', default='outputs/suite/real')
    parser.add_argument('--out', default='outputs/suite/counterfactuals')
    args = parser.parse_args()
    frozen = json.loads((ROOT / 'config/suite/frozen.json').read_text())
    scenes = [r['scene'] for r in frozen['scenes'] if not r.get('anchor')]
    real_root, output = ROOT / args.real_root, ROOT / args.out
    assert output.resolve().is_relative_to(ROOT / 'outputs')
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    source = sources()
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-counterfactual-processes/v1', 'source_sha256': source,
        'scenes': scenes, 'producer_pid': args.producer_pid, 'paid_tasks': 0, 'jobs': {}}
    assert report['source_sha256'] == source and report['scenes'] == scenes
    for row in report['jobs'].values():
        if row['status'] == 'running' and alive(row['pid']):
            raise RuntimeError('Counterfactual child still running; do not duplicate it')
    while True:
        assert sources() == source, 'Source changed during frozen suite postprocessing'
        real = json.loads((real_root / 'processes.json').read_text())
        assert real['source_sha256'] == source
        ready = [s for s in scenes if report['jobs'].get(s, {}).get('status') != 'complete'
                 and real['jobs'].get(s, {}).get('status') == 'complete']
        if not ready:
            report['completed'] = all(report['jobs'].get(s, {}).get('status') == 'complete' for s in scenes)
            report['status'] = 'complete' if report['completed'] else 'waiting_for_real'
            atomic_json(ledger, report)
            if report['completed']:
                return
            if not alive(args.producer_pid):
                raise SystemExit('Real producer ended with unfinished scenes; preserve the ledger and inspect')
            time.sleep(10)
            continue
        scene = ready[0]
        workers = 3 if real.get('completed') else 1
        command = [sys.executable, 'ops/run_suite_counterfactuals.py', '--scene', scene,
                   '--real-run', str((real_root / scene / 'imagination').relative_to(ROOT)),
                   '--out', str((output / scene).relative_to(ROOT)), '--workers', str(workers)]
        with (output / (scene + '.log')).open('a') as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            report['jobs'][scene] = {'status': 'running', 'pid': child.pid, 'command': command}
            report['status'] = 'running'
            atomic_json(ledger, report)
            code = child.wait()
        result_path = output / scene / 'counterfactuals.json'
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        passed = code == 0 and result.get('completed') and result.get('all_executed_prefixes_verified')
        report['jobs'][scene].update(status='complete' if passed else 'failed', exit_code=code,
                                    result=str(result_path.relative_to(ROOT)),
                                    rejected_candidates=result.get('rejected_candidates'),
                                    collisions=result.get('collisions'), executed=result.get('executed'))
        atomic_json(ledger, report)
        print(json.dumps({'scene': scene, 'exit_code': code, 'passed': bool(passed),
                          'executed': result.get('executed'), 'collisions': result.get('collisions')}), flush=True)
        if not passed:
            raise SystemExit('Counterfactuals failed validation; preserve outputs and inspect before resuming')


if __name__ == '__main__':
    main()
