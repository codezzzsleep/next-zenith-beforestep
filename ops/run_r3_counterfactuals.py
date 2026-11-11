"""Trust every newly generated rejected candidate at its original R3 view."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import numpy as np

from beforestep.generation import client as C
from run_suite_imagination import sources

ROOT = C.ROOT


def share_completed_observations(original, actual):
    """Keep all paths and exact bytes while sharing immutable replay copies.

    JSON, logs and active runs stay independent. Completed run directories are
    guarded against being simulated again at the same path by the drivers.
    """
    assert (original / 'summary.json').is_file() and (actual / 'summary.json').is_file()
    shared, byte_copies = 0, 0
    for path in actual.rglob('*'):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.png', '.jpg', '.npy', '.npz', '.obj', '.glb'):
            continue
        source = original / path.relative_to(actual)
        if not source.is_file() or source.is_symlink():
            continue
        left, right = source.stat(), path.stat()
        if left.st_dev != right.st_dev or left.st_size != right.st_size or (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino):
            continue
        if C.sha(source) != C.sha(path):
            continue
        temporary = path.with_name(path.name + '.share-' + uuid.uuid4().hex)
        os.link(source, temporary)
        os.replace(temporary, path)
        shared += 1; byte_copies += right.st_size
    return {'files': shared, 'identical_byte_copies_shared': byte_copies,
            'all_original_paths_and_bytes_preserved': True}


def prefix_check(original, actual, events, look, target):
    """Use the exact captured sensor state, not the rounded display timestamp.

    A display look time rounded to .01 s can include the first .002 s step
    after intervention. That step must differ when the new decision differs.
    Every actual sample through sensor capture remains subject to exact checks.
    """
    state = json.loads((original / 'looks' / f'look{look}' / target / 'state.json').read_text())
    sensor_time = state['t_sim']
    assert state['look'] == f'look{look}'
    before_events = [json.loads(line) for line in (original / 'events.jsonl').read_text().splitlines()]
    before_look = next(e for e in before_events if e['kind'] == 'look' and e['k'] == look)
    after_look = next(e for e in events if e['kind'] == 'look' and e['k'] == look)
    same_look = before_look['t'] == after_look['t'] and before_look['measured_pose'] == after_look['measured_pose']
    arrays = {}
    with np.load(original / 'traj.npz') as before, np.load(actual / 'traj.npz') as after:
        left, right = before['t'] <= sensor_time, after['t'] <= sensor_time
        for key in set(before.files) | set(after.files):
            arrays[key] = key in before.files and key in after.files and bool(np.array_equal(before[key][left], after[key][right]))
        sensor_pose = bool(np.array_equal(before['qpos'][left][-1], state['robot_qpos_world']) and
                           np.array_equal(after['qpos'][right][-1], state['robot_qpos_world']))
        count = int(left.sum())
    observation = {suffix: C.sha(original / 'looks' / f'look{look}_{suffix}') ==
                   C.sha(actual / 'looks' / f'look{look}_{suffix}')
                   for suffix in ('rgb.png', 'depth.npy', 'dark.npy', 'state.npy', 'zmax.npy')}
    return {'passed': same_look and sensor_pose and all(arrays.values()) and all(observation.values()),
            'look_time_and_pose_equal': same_look, 'sensor_qpos_exact': sensor_pose,
            'arrays_equal': arrays, 'observation_bytes_equal': observation,
            'through_sim_time_s': sensor_time, 'display_look_time_s': before_look['t'],
            'prefix_sample_count': count, 'boundary': 'All samples through exact sensor capture, inclusive'}


def new_rejections(original, budget):
    new_ids = {str(r['task_id']) for r in budget['tasks'].values()
               if r['new_r3_task'] and r.get('task_id')}
    candidates = []
    for path in sorted(original.glob('looks/look*/T*/decide/target_decision.json')):
        target = path.parent.parent
        state = json.loads((target / 'state.json').read_text())
        task_rows = json.loads((target / 'lux_result.json').read_text())['tasks']
        retry = target / 'retry/lux_result.json'
        if retry.exists():
            task_rows += json.loads(retry.read_text())['tasks']
        tasks = {r['id']: r for r in task_rows}
        for candidate in json.loads(path.read_text())['candidates']:
            task = tasks[candidate['id']]
            if not candidate['admitted'] and str(task['task_id']) in new_ids:
                candidates.append({'look': int(state['look'].removeprefix('look')),
                                   'target': target.name, 'candidate': candidate['id'],
                                   'task_id': task['task_id'], 'original_rejection': candidate,
                                   'source_decision': str(path.relative_to(ROOT))})
    return candidates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--real-run', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--budget', default='outputs/generation/r3-budget.json')
    ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()
    original = (ROOT / a.real_run).resolve()
    identity = json.loads((original / 'run_identity.json').read_text())
    summary = json.loads((original / 'summary.json').read_text())
    assert identity['source_sha256'] == sources()
    policy, scene = summary['policy'], summary['scene_id']
    assert policy in ('imagination', 'imagination_strict')
    budget = json.loads((ROOT / a.budget).read_text())
    candidates = new_rejections(original, budget)
    output = (ROOT / a.out).resolve()
    assert output.is_relative_to(ROOT / 'outputs')
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'counterfactuals.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-new-rejected-counterfactuals/v1', 'post_result_revision': True,
        'scene': scene, 'policy': policy, 'source_sha256': sources(),
        'original_run': a.real_run, 'candidates': candidates, 'runs': {}, 'paid_tasks': 0}
    assert report['candidates'] == candidates and report['source_sha256'] == sources()

    def run(row):
        key = f"look{row['look']}_{row['target']}_{row['candidate']}"
        container = output / key
        actual = container / 'trusted'
        if container.exists():
            raise RuntimeError(f'Unrecorded partial counterfactual exists: {container}; preserve and inspect')
        (container / policy).mkdir(parents=True)
        (container / policy / 'looks').symlink_to(original / 'looks', target_is_directory=True)
        command = [sys.executable, '-m', 'beforestep', 'run', '--scene', scene,
                   '--controller-model', 'rules', '--policy', policy, '--imagine', 'lux',
                   '--out', str(container), '--tag', 'trusted', '--reuse-lux', str(original),
                   '--trust', row['target'] + '=' + row['candidate'], '--trust-look', str(row['look'])]
        with (container / 'run.log').open('w') as log:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                     stdout=log, stderr=subprocess.STDOUT)
            C.atomic_json(container / 'process.json', {'pid': child.pid, 'command': command})
            code = child.wait()
        actual_summary = json.loads((actual / 'summary.json').read_text()) if (actual / 'summary.json').exists() else None
        events = [json.loads(line) for line in (actual / 'events.jsonl').read_text().splitlines()]
        intended = any(e['kind'] == 'counterfactual_intervention' and e['look'] == row['look'] and
                       e['target'] == row['target'] and e['candidate'] == row['candidate'] for e in events)
        prefix = prefix_check(original, actual, events, row['look'], row['target']) if intended and actual_summary else None
        shared = share_completed_observations(original, actual) if actual_summary else None
        return key, {'command': command, 'exit_code': code, 'summary': actual_summary,
                     'intervention_verified': intended, 'prefix_verification': prefix,
                     'immutable_observation_storage': shared,
                     'run': str(actual.relative_to(ROOT)),
                     'executed': code == 0 and actual_summary is not None and intended,
                     'collision': bool(actual_summary and (actual_summary['collision'] is not None or
                                       actual_summary['result'] == 'collision')) if intended else None}

    C.atomic_json(ledger, report)
    with ThreadPoolExecutor(max_workers=a.workers) as executor:
        futures = [executor.submit(run, row) for row in candidates
                   if f"look{row['look']}_{row['target']}_{row['candidate']}" not in report['runs']]
        for future in as_completed(futures):
            key, row = future.result()
            report['runs'][key] = row
            C.atomic_json(ledger, report)
            print(json.dumps({'counterfactual': key, 'exit_code': row['exit_code'],
                              'executed': row['executed'], 'collision': row['collision']}), flush=True)
    executed = [r for r in report['runs'].values() if r['executed']]
    report.update(completed=len(report['runs']) == len(candidates), rejected_candidates=len(candidates),
                  attempted=len(report['runs']), executed=len(executed),
                  collisions=sum(r['collision'] for r in executed),
                  noncollisions=sum(not r['collision'] for r in executed),
                  unexecutable=len(report['runs']) - len(executed),
                  all_executed_prefixes_verified=all(r['prefix_verification']['passed'] for r in executed))
    C.atomic_json(ledger, report)
    assert report['all_executed_prefixes_verified'], 'Counterfactual prefix differs; retain evidence and investigate'


if __name__ == '__main__':
    main()
