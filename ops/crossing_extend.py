"""Extend only time-limited wheel trials to a common 240-second horizon."""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'ops'))
from crossing_calibrate import run_fixed
from experimental.crossing.runtime import OUT, write, sha
import numpy as np

ATTEMPT = 'wheel-common240-extension-v1'
OLD = OUT / 'calibration/wheel-common120-v1'
NEW = OUT / 'calibration' / ATTEMPT

def identity(row):
    return f"{row['method']}-h{row['h_m']:.3f}-d{row['d_m']:.3f}-a{row['angle_deg']:+.1f}"

def extend(row):
    name = identity(row)
    folder = NEW / name
    result = run_fixed(row['h_m'], row['d_m'], row['angle_deg'], row['method'], folder, seconds=238.)
    # Reconstructing the old prefix is necessary because its recorder did not
    # retain qvel. Assert byte-exact physical state before accepting the extension.
    with np.load(OLD / name / 'trajectory.npz') as original, np.load(folder / 'trajectory.npz') as longer:
        count = len(original['t'])
        same = all(np.array_equal(original[key], longer[key][:count]) for key in ['t', 'qpos', 'phase', 'com', 'wheel_centres'])
    proof = {'original_result_sha256': sha(OLD / name / 'result.json'),
             'original_trajectory_sha256': sha(OLD / name / 'trajectory.npz'),
             'extended_result_sha256': sha(folder / 'result.json'),
             'old_prefix_exact': same, 'original_status': row['status'],
             'new_status': result['status'], 'common_total_time_limit_s': 240.}
    write(folder / 'extension.json', proof)
    if not same:
        raise RuntimeError(f'Physical prefix changed for {name}; retain both attempts')
    return result

if __name__ == '__main__':
    NEW.mkdir(parents=True, exist_ok=True)
    source = NEW / 'source'
    source.mkdir(exist_ok=True)
    paths = [Path(__file__), ROOT / 'ops/crossing_calibrate.py', ROOT / 'experimental/crossing/runtime.py']
    for path in paths:
        target = source / path.name
        if target.exists():
            assert target.read_bytes() == path.read_bytes(), 'Changed source in extension identity'
        else:
            shutil.copy2(path, target)
    jobs_path = OUT / 'jobs.json'
    ledger = json.loads(jobs_path.read_text())
    if ledger['jobs'].get(ATTEMPT, {}).get('status') == 'complete':
        print('Already complete; preserve all terminal trials')
        sys.exit(0)
    job = {'status': 'running', 'pid': os.getpid(), 'output': str(NEW.relative_to(ROOT)),
           'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'common_total_time_limit_s': 240., 'workers': 2,
           'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in paths}}
    ledger['jobs'][ATTEMPT] = job
    write(jobs_path, ledger)
    original = json.loads((OLD / 'summary.json').read_text())['results']
    pending = [row for row in original if row['status'] == 'stuck']
    results = {identity(row): row for row in original if row['status'] != 'stuck'}
    t0 = time.monotonic()
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(extend, row): identity(row) for row in pending}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                print(json.dumps({'trial': name, 'status': results[name]['status'],
                                  'completed_extensions': len(results) - (len(original) - len(pending))}), flush=True)
        write(NEW / 'summary.json', {'trials': len(original), 'common_total_time_limit_s': 240.,
                                    'inherited_early_terminal_trials': len(original) - len(pending),
                                    'extended_time_limited_trials': len(pending),
                                    'results': [results[identity(row)] for row in original]})
        job['status'] = 'complete'
    except BaseException as error:
        job.update(status='failed', error=type(error).__name__)
        raise
    finally:
        job['wall_seconds'] = time.monotonic() - t0
        ledger = json.loads(jobs_path.read_text())
        ledger['jobs'][ATTEMPT] = job
        write(jobs_path, ledger)
