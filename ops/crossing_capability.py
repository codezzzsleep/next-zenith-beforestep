"""Derive capability and the physical gate from immutable calibration records."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import OUT, write, sha

HEIGHTS = [.04, .06, .08, .10, .12, .15, .18, .22]
DEPTHS = [.10, .20, .30, .40]
ANGLES = [0., -5., 5.]
PASS = {'clean_pass', 'wheel_contact_pass'}


def rows_in(folder):
    return [(json.loads(p.read_text()), p.parent) for p in folder.glob('*/result.json')]


def derive(preview=False, matrix='gait-v72-capability-v1', rock_attempt='true-rocks-v72-v1'):
    extension = OUT / 'calibration/wheel-common240-extension-v1'
    wheel = json.loads((extension / 'summary.json').read_text())['results']
    trials = []
    for row in wheel:
        name = f"{row['method']}-h{row['h_m']:.3f}-d{row['d_m']:.3f}-a{row['angle_deg']:+.1f}"
        folder = next(p for p in [extension / name, OUT / 'calibration/wheel-common120-v1' / name]
                      if (p / 'result.json').exists())
        if not preview:
            assert sha(folder / 'trajectory.npz') == row['trajectory_sha256']
            assert sha(folder / 'contacts.npz') == row['contacts_sha256']
        trials.append({**row, 'raw_path': str(folder.relative_to(ROOT)), 'support_compliant': None})
    assert len(trials) == 192
    for row, folder in rows_in(OUT / 'calibration/wheel-d15-common240-v1'):
        trials.append({**row, 'raw_path': str(folder.relative_to(ROOT)), 'support_compliant': None})
    for row, folder in rows_in(OUT / 'calibration' / matrix):
        support = folder / 'support-physical-audit.json'
        if not support.exists():
            if preview:
                continue
            raise RuntimeError('Missing physical support audit: ' + str(folder))
        physical = json.loads(support.read_text())
        strict = json.loads((folder / 'support-audit.json').read_text())
        assert physical['contacts_sha256'] == row['contacts_sha256']
        trials.append({**row, 'raw_path': str(folder.relative_to(ROOT)),
                       'support_compliant': physical['all_three_stance_wheels_loaded_when_commanded_wheel_unloaded'],
                       'support_missing_when_commanded_wheel_unloaded':
                           physical['steps_stance_missing_while_commanded_wheel_unloaded'],
                       'strict_phase_support_missing': strict['steps_missing_stance_support']})
    groups = []
    missing = []
    for h in HEIGHTS:
        for d in sorted(DEPTHS + ([.15] if h in [.10, .12, .15] else [])):
            for method in ['fixed', 'high', 'gait']:
                cases = sorted([r for r in trials if r['method'] == method and r['h_m'] == h and r['d_m'] == d],
                               key=lambda r: r['angle_deg'])
                assert len(cases) <= 3
                assert len({r['angle_deg'] for r in cases}) == len(cases)
                if len(cases) != 3:
                    missing.append({'method': method, 'height_m': h, 'depth_m': d, 'completed': len(cases)})
                groups.append({'method': method, 'height_m': h, 'depth_m': d, 'trial_count': len(cases),
                               'passed': sum(r['status'] in PASS for r in cases),
                               'clean': sum(r['status'] == 'clean_pass' for r in cases),
                               'support_compliant_passed': sum(r['status'] in PASS and r['support_compliant'] is not False for r in cases),
                               'trials': cases})
    if not preview:
        assert not missing, missing
        assert len(trials) == 315
    maximum = {}
    necessary = []
    for method in ['fixed', 'high', 'gait']:
        passed_heights = [r['h_m'] for r in trials if r['method'] == method and r['status'] in PASS]
        all_heights = [g['height_m'] for g in groups if g['method'] == method and g['trial_count'] == 3
                       and g['support_compliant_passed'] == 3]
        maximum[method] = {'any_pass_height_m': max(passed_heights, default=None),
                           'three_of_three_height_m': max(all_heights, default=None)}
    for h in HEIGHTS:
        eligible = []
        for gait in [g for g in groups if g['method'] == 'gait' and g['height_m'] == h
                     and g['trial_count'] == 3 and g['support_compliant_passed'] == 3]:
            baseline = [g for g in groups if g['height_m'] == h and g['depth_m'] == gait['depth_m']
                        and g['method'] in ['fixed', 'high']]
            if all(g['trial_count'] == 3 and g['passed'] == 0 for g in baseline):
                eligible.append(gait['depth_m'])
        necessary.append({'height_m': h, 'd_max_m': max(eligible, default=None), 'verified_depths_m': eligible})
    spans = []
    run = []
    for row in necessary + [{'height_m': None, 'd_max_m': None}]:
        if row['d_max_m'] is not None and row['d_max_m'] >= .15 - 1e-9:
            run.append(row)
        else:
            if run:
                spans.append({'low_m': run[0]['height_m'], 'high_m': run[-1]['height_m'],
                              'width_m': run[-1]['height_m'] - run[0]['height_m'],
                              'sampled_heights_m': [r['height_m'] for r in run],
                              'minimum_d_max_m': min(r['d_max_m'] for r in run)})
                run = []
    best = max(spans, key=lambda r: r['width_m'], default=None)
    rocks = []
    for row, folder in rows_in(OUT / 'calibration' / rock_attempt):
        physical = json.loads((folder / 'support-physical-audit.json').read_text()) if row['method'] == 'gait' else None
        rocks.append({**row, 'raw_path': str(folder.relative_to(ROOT)),
                      'support_compliant': physical['all_three_stance_wheels_loaded_when_commanded_wheel_unloaded'] if physical else None})
    if not preview:
        assert len(rocks) == 9
        jobs = json.loads((OUT / 'jobs.json').read_text())['jobs']
        assert all(jobs[name]['status'] == 'complete' for name in
                   [matrix, 'wheel-d15-common240-v1', rock_attempt])
    clean_rocks = [r['rock'] for r in rocks if r['method'] == 'gait' and r['status'] == 'clean_pass' and r['support_compliant']]
    complete = not missing and len(rocks) == 9
    gate = bool(complete and best and best['width_m'] >= .05 - 1e-9 and len(clean_rocks) >= 2)
    return {'schema': 'beforestep-crossing-capability/v1', 'status': 'complete' if complete else 'partial',
            'trial_count': len(trials) + len(rocks), 'matrix_trial_count': len(trials),
            'required_matrix_trial_count': 288, 'supplemental_d15_trial_count': 27,
            'rock_trial_count': len(rocks), 'angles_deg': ANGLES, 'heights_m': HEIGHTS, 'depths_m': DEPTHS,
            'common_total_time_limit_s': 240., 'speed_cap_m_s': .15, 'new_lux_tasks': 0,
            'maximum': maximum, 'groups': groups, 'necessary_by_height': necessary,
            'best_sampled_necessary_span': best,
            'continuous_heights_between_samples_verified': False,
            'rocks': rocks, 'clean_support_compliant_rocks': clean_rocks, 'physical_gate_passed': gate,
            'missing_groups': missing,
            'support_definition': 'At every 2 ms physical substep where the commanded wheel bears no ground normal load above 1e-5 N, the other three must each bear positive ground normal load. The stricter whole-phase audit remains separately visible.',
            'source_jobs': {'gait': matrix, 'rocks': rock_attempt,
                            'wheel': 'wheel-common240-extension-v1', 'supplement': 'wheel-d15-common240-v1'},
            'frozen_original_source': '4d53214'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--matrix', default='gait-v72-capability-v1')
    parser.add_argument('--rocks', default='true-rocks-v72-v1')
    parser.add_argument('--out')
    args = parser.parse_args()
    data = derive(args.preview, args.matrix, args.rocks)
    target = Path(args.out) if args.out else (Path('/root/3d/.memory/live/crossing-capability-preview.json') if args.preview else ROOT / 'evidence/crossing/calibration/capability.json')
    write(target, data)
    print(json.dumps({k: data[k] for k in ['status', 'trial_count', 'maximum', 'best_sampled_necessary_span',
                                         'clean_support_compliant_rocks', 'physical_gate_passed']}, ensure_ascii=False))
