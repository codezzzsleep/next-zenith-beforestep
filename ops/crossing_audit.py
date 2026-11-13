"""Audit recorded support without changing a trial or its task outcome."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

LEGS = ['FR', 'FL', 'RR', 'RL']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(folder):
    folder = Path(folder)
    result = json.loads((folder / 'result.json').read_text())
    with np.load(folder / 'trajectory.npz') as trajectory, np.load(folder / 'contacts.npz') as contacts:
        times = trajectory['t']
        phases = trajectory['phase']
        # The recorded frame is the end of its control command. Each physics
        # substep therefore belongs to the next recorded control-frame phase.
        indices = np.minimum(np.searchsorted(times, contacts['t'] - 1e-7), len(times) - 1)
        step_phases = phases[indices]
        rows = []
        seen = set()
        for stage in result['stages']:
            phase = stage['phase']
            if not stage.get('swing_leg') or phase in seen:
                continue
            seen.add(phase)
            mask = step_phases == phase
            keep = [j for j, leg in enumerate(LEGS) if leg != stage['swing_leg']]
            support = contacts['loaded_support'][mask][:, keep]
            missing = ~np.all(support, axis=1)
            ids = np.where(missing)[0]
            runs = np.split(ids, np.where(np.diff(ids) != 1)[0] + 1) if len(ids) else []
            rows.append({'phase': phase, 'swing_leg': stage['swing_leg'],
                         'physics_steps': int(mask.sum()),
                         'steps_missing_stance_support': int(missing.sum()),
                         'longest_missing_steps': max(map(len, runs), default=0),
                         'missing_by_leg': {LEGS[j]: int((support[:, k] == 0).sum()) for k, j in enumerate(keep)}})
        missing_steps = sum(row['steps_missing_stance_support'] for row in rows)
        return {'schema': 'beforestep-crossing-support-audit/v1',
                'task_status_unchanged': result['status'],
                'trajectory_sha256': digest(folder / 'trajectory.npz'),
                'contacts_sha256': digest(folder / 'contacts.npz'),
                'recorded_max_frame_interval_s': float(np.diff(times).max()),
                'loaded_threshold_n': 1e-5,
                'all_three_stance_wheels_loaded_during_scripted_swing': missing_steps == 0,
                'steps_missing_stance_support': missing_steps,
                'phases': rows}


def physical_audit(folder):
    """Distinguish load transfer on four wheels from an unloaded swing wheel.

    Preserve the stricter phase-based audit separately. During unloading and
    landing, the commanded wheel can still bear weight: the three other wheels
    become the required support set once its measured normal load is zero.
    """
    folder = Path(folder)
    result = json.loads((folder / 'result.json').read_text())
    with np.load(folder / 'trajectory.npz') as trajectory, np.load(folder / 'contacts.npz') as contacts:
        indices = np.minimum(np.searchsorted(trajectory['t'], contacts['t'] - 1e-7),
                             len(trajectory['t']) - 1)
        phases = trajectory['phase'][indices]
        rows = []
        seen = set()
        for stage in result['stages']:
            phase = stage['phase']
            if not stage.get('swing_leg') or phase in seen:
                continue
            seen.add(phase)
            leg = LEGS.index(stage['swing_leg'])
            mask = phases == phase
            loaded = contacts['loaded_support'][mask]
            unloaded = loaded[:, leg] == 0
            stance_missing = ~np.all(np.delete(loaded, leg, axis=1), axis=1)
            missing = stance_missing & unloaded
            ids = np.flatnonzero(missing)
            runs = np.split(ids, np.where(np.diff(ids) != 1)[0] + 1) if len(ids) else []
            rows.append({'phase': phase, 'swing_leg': LEGS[leg],
                         'physics_steps': int(mask.sum()),
                         'steps_commanded_wheel_unloaded': int(unloaded.sum()),
                         'steps_stance_missing_while_commanded_wheel_unloaded': int(missing.sum()),
                         'longest_missing_steps': max(map(len, runs), default=0),
                         'steps_stance_missing_while_commanded_wheel_still_loaded':
                             int((stance_missing & ~unloaded).sum())})
        missing_steps = sum(row['steps_stance_missing_while_commanded_wheel_unloaded'] for row in rows)
        return {'schema': 'beforestep-crossing-physical-support-audit/v1',
                'audit_source_sha256': digest(Path(__file__)),
                'task_status_unchanged': result['status'],
                'trajectory_sha256': digest(folder / 'trajectory.npz'),
                'contacts_sha256': digest(folder / 'contacts.npz'),
                'loaded_threshold_n': 1e-5,
                'definition': 'Whenever the commanded swing wheel bears no measured ground normal load, all other three must bear positive ground normal load. Four-wheel unloading and landing transitions are reported separately.',
                'all_three_stance_wheels_loaded_when_commanded_wheel_unloaded': missing_steps == 0,
                'steps_stance_missing_while_commanded_wheel_unloaded': missing_steps,
                'phases': rows}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--physical', action='store_true')
    args = parser.parse_args()
    target = args.folder / ('support-physical-audit.json' if args.physical else 'support-audit.json')
    if target.exists():
        value = json.loads(target.read_text())
        assert value['trajectory_sha256'] == digest(args.folder / 'trajectory.npz')
        assert value['contacts_sha256'] == digest(args.folder / 'contacts.npz')
    else:
        value = physical_audit(args.folder) if args.physical else audit(args.folder)
        target.write_text(json.dumps(value, indent=2) + '\n')
    keys = (['task_status_unchanged', 'steps_stance_missing_while_commanded_wheel_unloaded',
             'all_three_stance_wheels_loaded_when_commanded_wheel_unloaded'] if args.physical else
            ['task_status_unchanged', 'steps_missing_stance_support',
             'all_three_stance_wheels_loaded_during_scripted_swing'])
    print(json.dumps({key: value[key] for key in keys}))
