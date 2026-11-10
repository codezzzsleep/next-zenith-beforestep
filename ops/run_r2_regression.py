"""R2 §2.2: immutable legacy files, unit tests, four baselines and exact Lux replay.

Completed jobs are resumed from the report rather than rerun. An interrupted
job with an existing output is refused; inspect it and choose a fresh --out.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / 'evidence/reviews/beforestep_r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'regression.json'
    sources = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'src').rglob('*.py'))}
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r2-regression/v1', 'source_sha256': sources, 'jobs': {}}
    if report['source_sha256'] != sources:
        raise ValueError('Source changed since this regression started; keep it and use a fresh --out')

    def save():
        temporary = ledger.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(ledger)

    frozen = ['config/admission.json', 'config/protocol.json',
              *[str(p.relative_to(ROOT)) for p in sorted((ROOT / 'config/scenes').glob('*.json'))
                if p.stem in ('stress_v8', 'gate_passage_001', 'blind_tail_001', 'dual_passage_001')]]
    report['frozen_files'] = {}
    for name in frozen:
        original = subprocess.check_output(['git', 'show', f'40044b4:{name}'], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == sha(ROOT / name), name
        report['frozen_files'][name] = sha(ROOT / name)
    save()
    environment = {**os.environ, 'MUJOCO_GL': 'egl', 'PYTHONDONTWRITEBYTECODE': '1'}
    if 'tests' not in report:
        with (output / 'tests.log').open('w') as log:
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                    cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
        report['tests'] = {'exit_code': result.returncode, 'log': str(output / 'tests.log')}
        save()
    assert report['tests']['exit_code'] == 0, 'Unit tests failed'
    jobs = [('conservative', ['--policy', 'conservative'], 'stuck'),
            ('see_dark', ['--policy', 'conservative', '--see-dark'], 'arrived'),
            ('optimistic', ['--policy', 'optimistic'], 'collision'),
            ('truth', ['--policy', 'imagination', '--imagine', 'truth'], 'arrived'),
            ('replay', ['--policy', 'imagination', '--imagine', 'lux', '--reuse-lux',
                        str(R1 / 'lux/original_b')], 'arrived')]

    def run(name, arguments, expected):
        run_dir = output / name
        if run_dir.exists():
            raise ValueError(f'Unrecorded partial run exists: {run_dir}; do not overwrite')
        command = [sys.executable, '-m', 'beforestep', 'run', '--scene', 'stress_v8',
                   '--controller-model', 'rules', '--out', str(output), '--tag', name, *arguments]
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
        summary = json.loads((run_dir / 'summary.json').read_text()) if (run_dir / 'summary.json').exists() else None
        row = {'command': command, 'exit_code': result.returncode, 'expected': expected, 'summary': summary}
        row['passed'] = result.returncode == 0 and summary is not None and summary['result'] == expected
        if name == 'replay' and row['passed']:
            with np.load(R1 / 'lux/original_b/traj.npz') as before, np.load(run_dir / 'traj.npz') as after:
                row['trajectory_arrays_equal'] = {k: bool(np.array_equal(before[k], after[k])) for k in before.files}
                row['trajectory_keys_equal'] = set(before.files) == set(after.files)
            row['passed'] &= row['trajectory_keys_equal'] and all(row['trajectory_arrays_equal'].values())
            row['trajectory_sha256'] = sha(run_dir / 'traj.npz')
            row['original_trajectory_sha256'] = sha(R1 / 'lux/original_b/traj.npz')
        return name, row

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        pending = [executor.submit(run, *job) for job in jobs if job[0] not in report['jobs']]
        for future in as_completed(pending):
            name, row = future.result()
            report['jobs'][name] = row
            save()
            print(json.dumps({'job': name, 'exit_code': row['exit_code'], 'passed': row['passed'],
                              'summary': row['summary']}, ensure_ascii=False), flush=True)
    report['passed'] = all(row['passed'] for row in report['jobs'].values()) and len(report['jobs']) == 5
    save()
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
