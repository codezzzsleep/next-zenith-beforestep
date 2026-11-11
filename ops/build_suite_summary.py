"""R2 B7/B8: traceable results and preregistered conclusions from raw artifacts."""
import argparse
import json
from pathlib import Path

import numpy as np

from beforestep import scene as S
from beforestep.evaluation import truth_footprints
from run_suite_counterfactuals import rejected_candidates

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / 'evidence/reviews/beforestep_r1'


def read(path):
    return json.loads(Path(path).read_text())


def has_collision(summary):
    return summary['collision'] is not None or summary['result'] == 'collision'


def counterfactual_outcomes(cf):
    rows = cf['runs'] if isinstance(cf['runs'], list) else [r for r in cf['runs'].values() if r['executed']]
    counts = {}
    for row in rows:
        outcome = 'collision' if has_collision(row['summary']) else row['summary']['result']
        counts[outcome] = counts.get(outcome, 0) + 1
    return counts


def require_real_provenance(actual):
    assert not (actual / 'standin_provenance.json').exists(), 'Stand-in data cannot count as real Lux'
    for result in actual.glob('looks/look*/T*/**/lux_result.json'):
        data = read(result)
        assert not data.get('not_real_lux'), 'Offline generation cannot count as real Lux'
        for task in data['tasks']:
            assert not task.get('not_real_lux'), 'Offline task cannot count as real Lux'
            if task['status'] == 'ok':
                assert isinstance(task['task_id'], int) and task['task_id'] > 0


def target_counts(actual, scene):
    definition = S.configure(scene)
    truth = truth_footprints(actual)
    intended = definition.get('suite', {}).get('target_rocks', list(definition['rocks']))
    def empty():
        return {'tasks': 0, 'succeeded': 0, 'admitted': 0, 'views': [], 'six_b': False,
                'shared_observation_target': False}
    # A target hidden throughout the run must remain visible as zero requests,
    # rather than disappear from the table precisely when it caused a failure.
    output = {rock: empty() for rock in intended}
    for state_file in sorted(actual.glob('looks/look*/T*/state.json')):
        target = state_file.parent
        if not (target / 'lux_request.json').exists():
            continue
        state = read(state_file)
        cells = np.load(target / 'cells.npy')
        associated = [rock for rock, mask in truth.items() if (mask & cells).any()]
        if not associated:
            associated = ['unassociated:' + state['look'] + '/' + target.name]
        tasks = []
        for result in (target / 'lux_result.json', target / 'retry/lux_result.json'):
            if result.exists():
                tasks.extend(read(result)['tasks'])
        decision = target / 'decide/target_decision.json'
        admitted = read(decision)['admitted_ids'] if decision.exists() else []
        for rock in associated:
            row = output.setdefault(rock, empty())
            row['tasks'] += len(tasks)
            row['succeeded'] += sum(t['status'] == 'ok' for t in tasks)
            row['admitted'] += len(admitted)
            row['six_b'] |= (target / 'retry/lux_request.json').exists()
            row['shared_observation_target'] |= len(associated) > 1
            row['views'].append({'look': state['look'], 'target': target.name,
                                 'associated_rocks': associated, 'native_px': state['crop_native_px'],
                                 'native_ok': state['native_ok'], 'mode': read(target / 'lux_request.json')['mode'],
                                 'task_ids': [t['task_id'] for t in tasks]})
    return output


def anchor_counterfactuals():
    rows = []
    for candidate in ('A1', 'B1', 'C2'):
        summary = read(R1 / 'counterfactuals' / candidate / 'summary.json')
        rows.append({'candidate': candidate, 'collision': summary['collision'] is not None, 'summary': summary})
    return {'rejected_candidates': 3, 'attempted': 3, 'executed': 3,
            'collisions': sum(r['collision'] for r in rows), 'unexecutable': 0, 'runs': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', default='config/suite/frozen.json')
    parser.add_argument('--real-root', default='outputs/suite/real')
    parser.add_argument('--counterfactual-root', default='outputs/suite/counterfactuals')
    parser.add_argument('--review-root', default='outputs/suite/reviews')
    parser.add_argument('--baseline-results', default='evidence/suite/pool/crater-target-baselines/manifest_results.json',
                        help='Corrected-source baselines; original freeze remains the selection authority')
    parser.add_argument('--out', default='evidence/suite/summary.json')
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    frozen = read(ROOT / args.freeze)
    baseline_path = ROOT / args.baseline_results
    baselines = read(baseline_path) if baseline_path.exists() else None
    if baselines:
        assert baselines['completed'], 'Corrected-source baseline suite is incomplete'
        assert set(baselines['scenes']) == {r['scene'] for r in frozen['scenes'] if not r.get('anchor')}
    rows, incomplete = [], []
    for entry in frozen['scenes']:
        scene = entry['scene']
        actual = ROOT / entry['real_run'] if entry.get('anchor') else ROOT / args.real_root / scene / 'imagination'
        if not (actual / 'summary.json').exists():
            incomplete.append(scene)
            continue
        require_real_provenance(actual)
        if not entry.get('anchor'):
            cf_path = ROOT / args.counterfactual_root / scene / 'counterfactuals.json'
            review_path = ROOT / args.review_root / scene / 'review.json'
            if not cf_path.exists() or not review_path.exists():
                incomplete.append(scene)
                continue
            cf = read(cf_path)
            if not cf.get('completed') or not cf.get('all_executed_prefixes_verified'):
                incomplete.append(scene)
                continue
        baseline_runs = baselines['scenes'][scene]['runs'] if baselines and not entry.get('anchor') else entry['runs']
        runs = {key: {'run': r['run'], 'summary': read(ROOT / r['run'] / 'summary.json'),
                      'run_id': read(ROOT / r['run'] / 'run_identity.json')['run_id']}
                for key, r in baseline_runs.items()}
        if baselines and not entry.get('anchor'):
            assert all(r['exit_code'] == 0 for r in baseline_runs.values())
            assert read(actual / 'run_identity.json')['source_sha256'] == baselines['source_sha256']
        runs['imagination'] = {'run': str(actual.relative_to(ROOT)), 'summary': read(actual / 'summary.json'),
                               'run_id': read(actual / 'run_identity.json')['run_id']}
        assert all(v['summary']['controller'] == 'rules' for v in runs.values())
        targets = target_counts(actual, scene)
        cf = anchor_counterfactuals() if entry.get('anchor') else cf
        if not entry.get('anchor'):
            expected_rejections = rejected_candidates(actual)
            expected_keys = {f"look{c['look']}_{c['target']}_{c['candidate']}" for c in expected_rejections}
            assert cf['scene'] == scene and (ROOT / cf['original_run']).resolve() == actual.resolve()
            assert cf['completed'] and cf['all_executed_prefixes_verified'], 'Counterfactual validation incomplete'
            assert set(cf['runs']) == expected_keys, 'Some original rejected candidates are missing or added'
            assert cf['attempted'] == cf['rejected_candidates'] == len(expected_keys)
            executed_cf = [r for r in cf['runs'].values() if r['executed']]
            for candidate_run in cf['runs'].values():
                if candidate_run['summary'] is not None:
                    assert candidate_run['summary'] == read(ROOT / candidate_run['run'] / 'summary.json')
            assert cf['executed'] == len(executed_cf)
            assert cf['collisions'] == sum(has_collision(r['summary']) for r in executed_cf)
            assert cf['noncollisions'] == len(executed_cf) - cf['collisions']
            assert cf['unexecutable'] == len(expected_keys) - len(executed_cf)
        if entry.get('anchor'):
            physical = read(actual / 'physical_clearance.json')
            xy = read(actual / 'eval.json')
            optimistic = read(R1 / 'section25_final_base/optimistic/eval.json')
            review = {'minimum_3d_clearance_m': min(r['minimum_signed_collision_geometry_distance_m'] for r in physical['rocks'].values()),
                      'minimum_xy_envelope_clearance_m': min(r['min_xy_rectangle_envelope_gap_m'] for r in xy['actual_clearance_by_rock'].values()),
                      'optimistic_max_intrusion_m': max(r['planned_envelope_intrusion_proxy_m'] for r in optimistic['first_departure_plan_by_rock'].values())}
        else:
            review = read(ROOT / args.review_root / scene / 'review.json')
            assert review['actual_run_id'] == runs['imagination']['run_id']
            assert review['optimistic_run_id'] == runs['optimistic']['run_id']
        events = [json.loads(line) for line in (actual / 'events.jsonl').read_text().splitlines()]
        plans = [e for e in events if e['kind'] == 'plan']
        physical_collision = has_collision(runs['imagination']['summary'])
        outcome = runs['imagination']['summary']['result']
        failure = None
        if physical_collision:
            failure = {'category': 'physical_collision',
                       'detail': runs['imagination']['summary']['collision'] or {'result': outcome},
                       'zero_request_rocks': [rock for rock, target in targets.items() if target['tasks'] == 0]}
        elif outcome != 'arrived':
            exhausted = [e for e in events if e['kind'] == 'sampling_stop']
            failure = {'category': 'zero_admission_after_retry' if exhausted else 'approach_or_observation_control' if outcome == 'stopped_short' else 'no_accepted_route',
                       'detail': exhausted[-1] if exhausted else plans[-1] if plans else {'result': outcome}}
        rows.append({**entry, 'classification_basis_runs': entry['runs'],
                     'classification_after_program_fix': baselines['scenes'][scene]['classification']
                        if baselines and not entry.get('anchor') else entry['classification'],
                     'runs': runs, 'targets': targets, 'review': review, 'failure_reason': failure,
                     'second_eye': runs['imagination']['summary']['looks'] > 1,
                     'six_b': any(t['six_b'] for t in targets.values()), 'counterfactuals': cf,
                     'counterfactual_outcomes': counterfactual_outcomes(cf),
                     'evidence': 'evidence/suite/scenes/' + scene + '/manifest.json' if not entry.get('anchor')
                     else 'evidence/reviews/beforestep_r1/lux/original_b/run_identity.json'})
    if incomplete and not args.allow_incomplete:
        raise ValueError('Incomplete frozen scenes: ' + ', '.join(incomplete))
    decisive = [r for r in rows if r['classification'] == 'decisive']
    ordinary = [r for r in rows if r['classification'] == 'ordinary']
    def outcome(row):
        return row['runs']['imagination']['summary']['result']
    arrived = sum(outcome(r) == 'arrived' and not has_collision(r['runs']['imagination']['summary']) for r in decisive)
    collisions = [r['scene'] for r in rows if has_collision(r['runs']['imagination']['summary'])]
    parked = sum(outcome(r) != 'arrived' and not has_collision(r['runs']['imagination']['summary']) for r in decisive)
    extra_eyes = [r['runs']['imagination']['summary']['looks'] - r['runs']['optimistic']['summary']['looks'] for r in ordinary]
    extra_time = [r['runs']['imagination']['summary']['sim_time_s'] - r['runs']['optimistic']['summary']['sim_time_s'] for r in ordinary]
    cf_collisions = sum(r['counterfactuals']['collisions'] for r in rows)
    cf_executed = sum(r['counterfactuals']['executed'] for r in rows)
    summary = {'schema': 'beforestep-preregistered-suite-summary/v1', 'freeze': args.freeze,
        'corrected_baseline_results': args.baseline_results if baselines else None,
        'frozen_scene_count': len(frozen['scenes']), 'completed_scene_count': len(rows),
        'incomplete_scenes': incomplete, 'scenes': rows,
        'decisive': {'completed': len(decisive), 'arrived': arrived, 'safe_stop': parked,
                     'collisions': sum(has_collision(r['runs']['imagination']['summary']) for r in decisive)},
        'ordinary': {'completed': len(ordinary), 'arrived': sum(outcome(r) == 'arrived' and not has_collision(r['runs']['imagination']['summary']) for r in ordinary),
                     'extra_eyes': extra_eyes, 'extra_sim_time_s': extra_time,
                     'mean_extra_eyes': float(np.mean(extra_eyes)) if extra_eyes else None,
                     'mean_extra_sim_time_s': float(np.mean(extra_time)) if extra_time else None},
        'imagination_collision_scenes': collisions,
        'counterfactuals': {'collisions': cf_collisions, 'executed': cf_executed,
                           'outcomes': {key: sum(r['counterfactual_outcomes'].get(key, 0) for r in rows)
                                        for key in ('arrived', 'stuck', 'stopped_short', 'collision')},
                           'unexecutable': sum(r['counterfactuals']['unexecutable'] for r in rows),
                           'collision_ratio': cf_collisions / cf_executed if cf_executed else None},
        'second_eye_scenes': [r['scene'] for r in rows if r['second_eye']],
        'six_b_scenes': [r['scene'] for r in rows if r['six_b']],
        'majority_effectiveness_supported': not incomplete and not collisions and bool(decisive) and arrived / len(decisive) >= 2/3,
        'selfcheck_collision_evidence': cf_collisions > 0,
        'scope': 'Preregistered finite scene suite; no claim of universal effectiveness. Simulation time excludes cloud waiting.'}
    output = ROOT / args.out; output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('completed_scene_count', 'incomplete_scenes', 'decisive', 'ordinary',
                                            'imagination_collision_scenes', 'counterfactuals', 'second_eye_scenes')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
