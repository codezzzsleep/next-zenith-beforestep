"""Coordinate resumable development probes and their durable task ledger."""
import argparse
import concurrent.futures
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import OUT, sha, write
from ops.crossing_audit import audit, physical_audit


def event(attempt, **fields):
    path = OUT / 'jobs.json'
    with (OUT / '.jobs.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(path.read_text())
        job = ledger['jobs'].setdefault(attempt, {})
        job.update(fields, updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        write(path, ledger)


def trial(attempt, case, variant='default', control_hz=100):
    h, d, angle = case
    folder = OUT / 'calibration' / attempt / f'gait-h{h:.3f}-d{d:.3f}-a{angle:+.1f}'
    folder.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT / 'ops/crossing_gait.py'), '--attempt', attempt,
               '--height', str(h), '--depth', str(d), '--angle', str(angle), '--variant', variant,
               '--control-hz', str(control_hz)]
    if not (folder / 'result.json').exists():
        with (folder / 'run.log').open('a') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            write(folder / 'process.json', {'pid': process.pid, 'command': command,
                                           'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            code = process.wait()
        if code:
            write(folder / f'failure-{time.time_ns()}.json', {'exit_code': code, 'command': command})
            return {'case': case, 'status': 'runner_failed', 'exit_code': code}
    result = json.loads((folder / 'result.json').read_text())
    target = folder / 'support-audit.json'
    if not target.exists():
        write(target, audit(folder))
    support = json.loads(target.read_text())
    physical_path = folder / 'support-physical-audit.json'
    if not physical_path.exists():
        write(physical_path, physical_audit(folder))
    physical = json.loads(physical_path.read_text())
    return {**{key: result[key] for key in ['h_m', 'd_m', 'angle_deg', 'status', 'sim_seconds', 'last_phase']},
            'missing_support_steps': support['steps_missing_stance_support'],
            'missing_support_steps_when_commanded_wheel_unloaded':
                physical['steps_stance_missing_while_commanded_wheel_unloaded']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--case', action='append', required=True, help='height,depth,angle in m,m,deg')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--variant', choices=['default','force','fullframe','heading'], default='default')
    parser.add_argument('--control-hz', type=int, choices=[50,100,250,500], default=100)
    args = parser.parse_args()
    cases = [tuple(map(float, case.split(','))) for case in args.case]
    assert all(len(case) == 3 for case in cases)
    assert len(cases) == len(set(cases))
    folder = OUT / 'calibration' / args.attempt
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / '.coordinator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        action_path=ROOT/'experimental/crossing'/('action.py' if args.variant=='default' else 'action_'+args.variant+'.py')
        identity = {str(path.relative_to(ROOT)): sha(path) for path in [
            action_path, ROOT / 'experimental/crossing/runtime.py',
            ROOT / 'ops/crossing_gait.py']}
        registration = {'attempt': args.attempt, 'cases': cases, 'source_sha256': identity,
                        'variant': args.variant, 'control_hz': args.control_hz,
                        'kind': 'development calibration, excluded from registered test statistics'}
        if (folder / 'identity.json').exists():
            assert json.loads((folder / 'identity.json').read_text()) == json.loads(json.dumps(registration))
        else:
            write(folder / 'identity.json', registration)
        event(args.attempt, status='running', pid=os.getpid(), output=str(folder.relative_to(ROOT)),
              cases=cases, source_sha256=identity, workers=args.workers)
        started = time.monotonic()
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            tasks = [pool.submit(trial, args.attempt, case, args.variant, args.control_hz) for case in cases]
            for task in concurrent.futures.as_completed(tasks):
                result = task.result()
                results.append(result)
                event(args.attempt, results=results)
                if len(cases) <= 6:
                    print(json.dumps(result), flush=True)
                elif len(results) % 12 == 0 or len(results) == len(cases):
                    print(json.dumps({'completed': len(results), 'total': len(cases),
                                      'status_counts': {status: sum(r['status'] == status for r in results)
                                                        for status in sorted({r['status'] for r in results})}}), flush=True)
        assert all(sha(ROOT / path) == value for path, value in identity.items()), 'Source changed during run'
        event(args.attempt, status='complete' if all(r['status'] != 'runner_failed' for r in results) else 'failed',
              results=results, wall_seconds=time.monotonic() - started)


if __name__ == '__main__':
    main()
