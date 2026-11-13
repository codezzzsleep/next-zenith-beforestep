"""Apply Addendum 1 to frozen v72 task outcomes; retain support diagnostics."""
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def longest(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return int(max(np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1), default=0))

def derive():
    source = ROOT / 'evidence/crossing/calibration/capability-v72.json'
    frozen_sha = digest(source)
    data = json.loads(source.read_text()); groups = data['groups']
    necessary, eligible_groups = [], []
    for height in data['heights_m']:
        depths = []
        for gait in [g for g in groups if g['method'] == 'gait' and g['height_m'] == height]:
            wheels = [g for g in groups if g['method'] in ('fixed', 'high')
                      and g['height_m'] == height and g['depth_m'] == gait['depth_m']]
            if (gait['trial_count'] == 3 and gait['passed'] == 3 and len(wheels) == 2
                    and all(g['trial_count'] == 3 and g['passed'] == 0 for g in wheels)):
                depths.append(gait['depth_m']); eligible_groups.append(gait)
        necessary.append({'height_m': height, 'd_max_m': max(depths, default=None), 'verified_depths_m': depths})
    runs, run = [], []
    for row in necessary + [{'d_max_m': None}]:
        if row['d_max_m'] is not None and row['d_max_m'] >= .15 - 1e-9:
            run.append(row)
        else:
            if run:
                runs.append({'low_m': run[0]['height_m'], 'high_m': run[-1]['height_m'],
                             'width_m': run[-1]['height_m'] - run[0]['height_m'],
                             'sampled_heights_m': [r['height_m'] for r in run],
                             'minimum_d_max_m': min(r['d_max_m'] for r in run)})
            run = []
    best = max(runs, key=lambda r: r['width_m'])
    band_groups = [g for g in eligible_groups if g['height_m'] in best['sampled_heights_m']]
    support = []
    for group in band_groups:
        for trial in group['trials']:
            folder = ROOT / trial['raw_path']; contacts_path = folder / 'contacts.npz'
            assert digest(contacts_path) == trial['contacts_sha256']
            with np.load(contacts_path) as contacts, np.load(folder / 'trajectory.npz') as trajectory:
                indices = np.minimum(np.searchsorted(trajectory['t'], contacts['t'] - 1e-7), len(trajectory['t']) - 1)
                phases = trajectory['phase'][indices]
                loaded = contacts['loaded_support']
                active_unloaded = np.zeros(len(loaded), dtype=bool)
                for stage in trial['stages']:
                    if stage.get('swing_leg'):
                        leg = ['FR', 'FL', 'RR', 'RL'].index(stage['swing_leg'])
                        active_unloaded |= (phases == stage['phase']) & (loaded[:, leg] == 0)
                two = (loaded.sum(axis=1) == 2) & active_unloaded
                dt = float(np.median(np.diff(contacts['t'])))
            audit = json.loads((folder / 'support-physical-audit.json').read_text())
            support.append({'height_m': group['height_m'], 'depth_m': group['depth_m'],
                'angle_deg': trial['angle_deg'], 'raw_path': trial['raw_path'], 'task_status': trial['status'],
                'contacts_sha256': trial['contacts_sha256'], 'two_loaded_wheels_total_s': round(float(two.sum()) * dt, 6),
                'two_loaded_wheels_longest_s': round(longest(two) * dt, 6),
                'max_tilt_deg': trial['contact']['max_tilt_deg'],
                'missing_stance_steps_when_commanded_wheel_unloaded': audit['steps_stance_missing_while_commanded_wheel_unloaded'],
                'support_compliant': trial['support_compliant']})
    clean_rocks = [r['rock'] for r in data['rocks'] if r['method'] == 'gait' and r['status'] == 'clean_pass']
    conditions = [
        {'criterion': 'sampled necessary span >= 0.05 m', 'measured_m': best['width_m'], 'passed': best['width_m'] >= .05 - 1e-9},
        {'criterion': 'd_max at each sampled band height >= 0.15 m', 'measured_m': best['minimum_d_max_m'], 'passed': best['minimum_d_max_m'] >= .15 - 1e-9},
        {'criterion': 'at least two of three real rock fixtures cleanly passed', 'clean_rocks': clean_rocks, 'count': len(clean_rocks), 'passed': len(clean_rocks) >= 2}]
    action = ROOT / 'outputs/crossing/calibration/gait-v72-capability-v1/source/action.py'
    assert digest(action).startswith('488401d8')
    result = {'schema': 'beforestep-crossing-gate/v1', 'authority': 'docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM1.md',
        'frozen_capability': str(source.relative_to(ROOT)), 'frozen_capability_sha256': frozen_sha,
        'frozen_original_gate_value': data['physical_gate_passed'], 'action_version': 'v72', 'action_sha256': digest(action),
        'pass_definition': 'SPEC 5.2 task outcomes, identical for all three abilities; support is diagnostic',
        'conditions': conditions, 'physical_gate_passed': all(c['passed'] for c in conditions),
        'necessary_by_height': necessary, 'best_sampled_necessary_span': best, 'continuous_heights_between_samples_verified': False,
        'band_gait_groups': len(band_groups), 'band_gait_trials': len(support),
        'band_gait_clean_trials': sum(r['task_status'] == 'clean_pass' for r in support),
        'wheel_trials_at_band_heights': sum(g['trial_count'] for g in groups if g['method'] in ('fixed', 'high') and g['height_m'] in best['sampled_heights_m']),
        'wheel_passes_at_band_heights': sum(g['passed'] for g in groups if g['method'] in ('fixed', 'high') and g['height_m'] in best['sampled_heights_m']),
        'gait_three_of_three_height_m': max(g['height_m'] for g in groups if g['method'] == 'gait' and g['passed'] == 3),
        'support_diagnostic': {'counted_in_gate_or_passes': False, 'load_threshold_n': 1e-5,
            'maximum_trial_total_two_loaded_wheels_s': max(r['two_loaded_wheels_total_s'] for r in support),
            'longest_two_loaded_wheels_s': max(r['two_loaded_wheels_longest_s'] for r in support),
            'maximum_tilt_deg': max(r['max_tilt_deg'] for r in support), 'trials': support}}
    assert digest(source) == frozen_sha
    (ROOT / 'evidence/crossing/calibration/gate.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['physical_gate_passed', 'best_sampled_necessary_span', 'band_gait_trials', 'wheel_trials_at_band_heights']}))
    print(json.dumps({k: v for k, v in result['support_diagnostic'].items() if k != 'trials'}))
if __name__ == '__main__':
    derive()
