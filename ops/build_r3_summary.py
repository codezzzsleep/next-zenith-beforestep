"""Separate the known-scene revision reruns from held-out evidence."""
import json
from pathlib import Path

from beforestep.generation import client as C
from r3_lux_budget import R3Budget

ROOT = C.ROOT


def strict_stats(rows):
    completed = [r for r in rows if r['runs'].get('imagination_strict', {}).get('summary')]
    summaries = [r['runs']['imagination_strict']['summary'] for r in completed]
    collisions = [s['scene_id'] for s in summaries if s['collision'] is not None or s['result'] == 'collision']
    see_dark_arrived = [r for r in rows if r['runs'].get('see_dark', {}).get('summary', {}).get('result') == 'arrived']
    paired = []
    for row in see_dark_arrived:
        before = row['runs']['see_dark']['summary']
        after = row['runs'].get('imagination_strict', {}).get('summary')
        paired.append({'scene': row['scene'], 'see_dark': {'looks': before['looks'], 'sim_time_s': before['sim_time_s']},
                       'imagination_strict': None if not after else {'result': after['result'], 'looks': after['looks'],
                                                                    'sim_time_s': after['sim_time_s']}})
    return {'completed': len(completed), 'incomplete': [r['scene'] for r in rows if r not in completed],
            'arrived': sum(s['result'] == 'arrived' and s['collision'] is None for s in summaries),
            'safe_stop': sum(s['result'] != 'arrived' and s['result'] != 'collision' and s['collision'] is None for s in summaries),
            'collisions': len(collisions), 'collision_scenes': collisions,
            'see_dark_arrived_scenes': len(see_dark_arrived),
            'strict_arrived_among_see_dark_arrived': sum(p['imagination_strict'] is not None and
                                                       p['imagination_strict']['result'] == 'arrived' for p in paired),
            'see_dark_pairwise_looks_and_sim_time': paired}


def main():
    original = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    frozen = json.loads((ROOT / 'outputs/r3/frozen/processes.json').read_text())
    plan = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    rows = []
    for row in original['scenes']:
        runs = {key: row['runs'][key] for key in ('conservative', 'see_dark', 'optimistic', 'truth', 'imagination')}
        strict = frozen['jobs'].get(row['scene'], {})
        if strict.get('summary'):
            actual = ROOT / 'outputs/r3/frozen' / row['scene'] / 'imagination_strict'
            chain = json.loads((actual.parent / 'chain.json').read_text())
            assert chain['first_view_verification']['passed']
            runs['imagination_strict'] = {'summary': strict['summary'], 'run_id': strict['run_id'],
                                          'run': str(actual.relative_to(ROOT)), 'completed': True,
                                          'first_view_verification': chain['first_view_verification']}
        else:
            runs['imagination_strict'] = {'completed': False}
        rows.append({'scene': row['scene'], 'family': row['family'], 'classification': row['classification'],
                     'sample_scope': 'known_scene_post_result_rerun', 'runs': runs})
    holdouts_path = ROOT / 'outputs/r3/holdouts/processes.json'
    holdouts = json.loads(holdouts_path.read_text()) if holdouts_path.exists() else {'jobs': {}}
    held_rows = []
    for row in plan['holdouts']:
        job = holdouts['jobs'].get(row['scene'], {})
        held_rows.append({'scene': row['scene'], 'sample_scope': 'designated_holdout',
                          'budget_optional': row['budget_optional'], 'status': job.get('status', 'not_started'),
                          'runs': job.get('runs', {})})
    budget = json.loads((ROOT / 'outputs/generation/r3-budget.json').read_text())
    cf = []
    for path in sorted((ROOT / 'outputs/r3/counterfactuals').rglob('counterfactuals.json')):
        result = json.loads(path.read_text())
        cf.append({**{k: result[k] for k in ('scene', 'policy', 'completed', 'rejected_candidates', 'executed',
                                           'collisions', 'noncollisions', 'unexecutable', 'all_executed_prefixes_verified')},
                   'ledger': str(path.relative_to(ROOT))})
    report = {'schema': 'beforestep-r3-suite-summary/v1', 'post_result_revision': True,
              'original_preregistered_primary_results': 'evidence/suite/summary.json',
              'frozen': rows, 'holdouts': held_rows, 'frozen_stats': strict_stats(rows),
              'holdout_stats': strict_stats(held_rows), 'all_run_stats': strict_stats(rows + held_rows),
              'f1_unused_decisive_available': False, 'new_rejected_counterfactuals': cf,
              'paid_tasks': {'new_r3': R3Budget.usage(budget), 'r2': 168,
                             'cumulative_r2_r3': 168 + R3Budget.usage(budget), 'r3_limit': 170, 'original_limit': 360},
              'scope': 'Known-scene reruns are a post-result revision. Only the prescribed held-out scenes can support an out-of-sample claim. All outcomes are retained.'}
    C.atomic_json(ROOT / 'evidence/reviews/beforestep_r3/summary.json', report)
    print(json.dumps({key: report[key] for key in ('frozen_stats', 'holdout_stats', 'paid_tasks')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
