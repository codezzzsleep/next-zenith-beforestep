"""Offline full-chain check: a look-two intervention must preserve its prefix."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--regression', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    gate = json.loads((ROOT / args.regression).read_text())
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'src').rglob('*.py'))}
    assert gate['passed'] and gate['source_sha256'] == sources
    original = ROOT / 'evidence/reviews/beforestep_r1/standins/registration_fixed'
    output = (ROOT / args.out).resolve()
    if output.exists():
        raise ValueError('Choose a fresh output; keep any previous failed call')
    output.mkdir(parents=True)
    shutil.copytree(original / 'looks', output / 'imagination/looks')
    (output / 'trust_look2').mkdir()
    shutil.copy2(original / 'standin_provenance.json', output / 'trust_look2/standin_provenance.json')
    command = [sys.executable, '-m', 'beforestep', 'run', '--scene', 'stress_v8',
               '--policy', 'imagination', '--imagine', 'lux', '--controller-model', 'rules',
               '--reuse-lux', str(original), '--out', str(output), '--tag', 'trust_look2',
               '--trust', 'T2=A1', '--trust-look', '2']
    with (output / 'run.log').open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                   stdout=log, stderr=subprocess.STDOUT)
        (output / 'process.json').write_text(json.dumps({'pid': process.pid, 'command': command}) + '\n')
        code = process.wait()
    assert code == 0, f'Counterfactual exit {code}; inspect the original log'
    run = output / 'trust_look2'
    events = [json.loads(line) for line in (run / 'events.jsonl').read_text().splitlines()]
    before_events = [json.loads(line) for line in (original / 'events.jsonl').read_text().splitlines()]
    intervention = [e for e in events if e['kind'] == 'counterfactual_intervention']
    assert len(intervention) == 1 and intervention[0]['look'] == 2
    assert intervention[0]['source_look'] == 'look2' and intervention[0]['candidate'] == 'A1'
    look2 = next(e for e in events if e['kind'] == 'look' and e['k'] == 2)
    before2 = next(e for e in before_events if e['kind'] == 'look' and e['k'] == 2)
    assert look2['t'] == before2['t'] and look2['measured_pose'] == before2['measured_pose']
    prefix = {}
    with np.load(run / 'traj.npz') as after, np.load(original / 'traj.npz') as before:
        a, b = after['t'] <= look2['t'] + 1e-9, before['t'] <= before2['t'] + 1e-9
        assert set(before.files) == set(after.files)
        for name in before.files:
            prefix[name] = bool(np.array_equal(before[name][b], after[name][a]))
    assert all(prefix.values()), prefix
    result = {'schema': 'beforestep-r2-look2-counterfactual-check/v1', 'passed': True,
              'not_real_lux': True, 'paid_tasks': 0, 'command': command, 'exit_code': code,
              'original_run_id': json.loads((original / 'run_identity.json').read_text())['run_id'],
              'run_id': json.loads((run / 'run_identity.json').read_text())['run_id'],
              'intervention': intervention[0], 'prefix_arrays_equal': prefix,
              'source_sha256': sources, 'summary': json.loads((run / 'summary.json').read_text())}
    (output / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
