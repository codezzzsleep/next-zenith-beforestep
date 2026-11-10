"""Verify preserved R1 bytes, run identities and replay without running physics/API.

Use --originals on the execution machine to compare every preserved source file
with outputs/. Without it, the check is self-contained in a fresh checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/reviews/beforestep_r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify(originals=False):
    counts = {'manifests': 0, 'preserved_files': 0, 'original_files': 0,
              'source_files': 0, 'logs': 0}
    for manifest in sorted(BASE.rglob('*preservation.json')):
        data = read(manifest)
        if 'files_sha256' not in data:
            continue
        counts['manifests'] += 1
        for relative, digest in data['files_sha256'].items():
            assert sha(manifest.parent / relative) == digest, str(manifest / relative)
            counts['preserved_files'] += 1
            if originals:
                assert sha(ROOT / data['original_output'] / relative) == digest, relative
                counts['original_files'] += 1
    runs = [BASE / 'section25_final_base' / name
            for name in ('conservative', 'see_dark', 'optimistic', 'truth')]
    runs += [BASE / 'lux' / name for name in ('original_b', 'replay')]
    runs += [BASE / 'counterfactuals' / name for name in ('A1', 'B1', 'C2')]
    runs += [BASE / 'standins/registration_fixed']
    for run in runs:
        identity = read(run / 'run_identity.json')
        assert len(identity['source_sha256']) == 52
        for path, digest in identity['source_sha256'].items():
            frozen = subprocess.check_output(['git', 'show', '2147b2f:' + path], cwd=ROOT)
            assert hashlib.sha256(frozen).hexdigest() == digest, path
            assert sha(ROOT / path) == digest, path
            counts['source_files'] += 1
        if (run / 'eval.json').exists():
            audit = read(run / 'eval.json')
            assert audit['run_id'] == identity['run_id']
            assert audit['summary_sha256'] == sha(run / 'summary.json')
    if originals:
        candidates = list((ROOT / 'outputs/reviews/r1').rglob('*.log'))
        for log in (BASE / 'logs').glob('*.log'):
            matches = [p for p in candidates if p.name == log.name and sha(p) == sha(log)]
            assert matches, str(log)
            counts['logs'] += 1
        failed = BASE / 'failed_calls/replay_parent_directory'
        assert sha(failed / 'command.log') == sha(ROOT / 'outputs/reviews/r1/section25_lux_replay.log')
        for path in (failed / 'imagination').rglob('*'):
            if path.is_file():
                original = ROOT / 'outputs/reviews/r1/section25_lux_replay/imagination' / path.relative_to(failed / 'imagination')
                assert sha(path) == sha(original)
    original, replay = BASE / 'lux/original_b', BASE / 'lux/replay'
    validation = read(BASE / 'replay_validation.json')
    assert validation['original_run_id'] == read(original / 'run_identity.json')['run_id']
    assert validation['replay_run_id'] == read(replay / 'run_identity.json')['run_id']
    assert validation['original_trajectory_sha256'] == sha(original / 'traj.npz')
    assert validation['replay_trajectory_sha256'] == sha(replay / 'traj.npz')
    a, b = np.load(original / 'traj.npz'), np.load(replay / 'traj.npz')
    assert a.files == b.files == validation['arrays']
    assert all(np.array_equal(a[key], b[key]) for key in a.files)
    sa, sb = read(original / 'summary.json'), read(replay / 'summary.json')
    assert {k: v for k, v in sa.items() if k != 'wall_s'} == {k: v for k, v in sb.items() if k != 'wall_s'}
    collisions = sum(read(BASE / 'counterfactuals' / name / 'summary.json')['collision'] is not None
                     for name in ('A1', 'B1', 'C2'))
    assert collisions == validation['counterfactual_collisions'] == 0
    assert validation['self_check_collision_prevention_demonstrated'] is False
    physical = read(original / 'physical_clearance.json')
    assert physical['run_id'] == validation['original_run_id']
    assert physical['trajectory_sha256'] == sha(original / 'traj.npz')
    assert physical['sample_count'] == len(a['qpos'])
    assert physical['rocks']['B']['minimum_signed_collision_geometry_distance_m'] == validation['physical_clearance_B_m']
    for run in (original, replay):
        rehearsals = read(run / 'eval.json')['execution_rehearsals']
        assert len(rehearsals) == 1
        event = rehearsals[0]
        assert len(event['panes']) == 12
        assert all(p['completed'] and not p['collided'] for p in event['panes'])
        for pane in event['panes']:
            assert (run / 'rehearsal' / 'look1' / ('pane' + str(pane['pane'])) / 'traj.npz').exists()
    return {'schema': 'beforestep-r1-integrity-check/v1', 'passed': True,
            'compare_original_outputs': originals, **counts,
            'trajectory_arrays_equal': a.files, 'counterfactual_collisions': collisions,
            'source_commit': validation['source_commit']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--originals', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.originals), indent=2))
