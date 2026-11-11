"""Separate the known-scene revision reruns from held-out evidence."""
import json
import argparse
from pathlib import Path

from beforestep.generation import client as C
from r3_lux_budget import R3Budget

ROOT = C.ROOT


def details(run, scene):
    directory = ROOT / run
    identity = json.loads((directory / 'run_identity.json').read_text())
    events = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
    targets = []
    for decision in sorted(directory.glob('looks/look*/T*/decide/target_decision.json')):
        target = decision.parent.parent
        state = json.loads((target / 'state.json').read_text())
        tasks = json.loads((target / 'lux_result.json').read_text())['tasks']
        retry = target / 'retry/lux_result.json'
        if retry.exists():
            tasks += json.loads(retry.read_text())['tasks']
        candidates = json.loads(decision.read_text())['candidates']
        targets.append({'look': state['look'], 'target': target.name,
                        'crop_native_px': state['crop_native_px'], 'native_ok': state['native_ok'],
                        'task_ids': [t['task_id'] for t in tasks], 'tasks': len(tasks),
                        'succeeded': sum(t['status'] == 'ok' for t in tasks),
                        'provider_failed': sum(t['status'] == 'failed' for t in tasks),
                        'admitted': sum(c['admitted'] for c in candidates),
                        'rejected': sum(not c['admitted'] for c in candidates),
                        'retry_6b': retry.exists(), 'source_decision': str(decision.relative_to(ROOT))})
    manifest = ROOT / 'evidence/reviews/beforestep_r3/scenes' / scene / 'manifest.json'
    sidecar = ROOT / 'outputs/video/r3/reviews' / identity['run_id']
    return {'targets': targets, 'source_sha256': identity['source_sha256'],
            'trajectory_sha256': C.sha(directory / 'traj.npz'),
            'shadow_explanations': [e for e in events if e['kind'] == 'shadow_explanation'],
            'observation_moves': [e for e in events if e['kind'] == 'second_look_plan'],
            'last_plan': next((e for e in reversed(events) if e['kind'] == 'plan'), None),
            'terminal_events': [e for e in events[-5:] if e['kind'] != 'result'],
            'public_manifest': str(manifest.relative_to(ROOT)) if manifest.exists() else None,
            'postmortem': {name: json.loads((sidecar / name).read_text())
                          for name in ('eval.json', 'physical_clearance.json') if (sidecar / name).exists()}}


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
    ap = argparse.ArgumentParser()
    ap.add_argument('--frozen', default='outputs/r3/v3/frozen/processes.json')
    ap.add_argument('--holdouts', default='outputs/r3/v3/holdouts/processes.json')
    ap.add_argument('--counterfactuals', default='outputs/r3/v3/counterfactuals')
    a = ap.parse_args()
    original = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    frozen = json.loads((ROOT / a.frozen).read_text())
    plan = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    rows = []
    for row in original['scenes']:
        runs = {key: row['runs'][key] for key in ('conservative', 'see_dark', 'optimistic', 'truth', 'imagination')}
        strict = frozen['jobs'].get(row['scene'], {})
        if strict.get('summary'):
            actual = (ROOT / strict['chain']).parent / 'imagination_strict'
            chain = json.loads((actual.parent / 'chain.json').read_text())
            assert chain['first_view_verification']['passed']
            runs['imagination_strict'] = {'summary': strict['summary'], 'run_id': strict['run_id'],
                                          'run': str(actual.relative_to(ROOT)), 'completed': True,
                                          'first_view_verification': chain['first_view_verification'],
                                          **details(str(actual.relative_to(ROOT)), row['scene'])}
        else:
            runs['imagination_strict'] = {'completed': False}
        rows.append({'scene': row['scene'], 'family': row['family'], 'classification': row['classification'],
                     'sample_scope': 'known_scene_post_result_rerun', 'runs': runs})
    holdouts_path = ROOT / a.holdouts
    holdouts = json.loads(holdouts_path.read_text()) if holdouts_path.exists() else {'jobs': {}}
    held_rows = []
    for row in plan['holdouts']:
        job = holdouts['jobs'].get(row['scene'], {})
        held_runs = job.get('runs', {})
        for policy, run in held_runs.items():
            if run.get('summary') and policy in ('imagination', 'imagination_strict'):
                run.update(details(run['run'], row['scene']))
                chain = json.loads((ROOT / run['chain']).read_text())
                run['first_view_verification'] = chain.get('first_view_verification')
        held_rows.append({'scene': row['scene'], 'sample_scope': 'designated_holdout',
                          'budget_optional': row['budget_optional'], 'status': job.get('status', 'not_started'),
                          'runs': held_runs})
    budget = json.loads((ROOT / 'outputs/generation/r3-budget.json').read_text())
    previous = json.loads((ROOT / 'outputs/r3/frozen/processes.json').read_text())
    prior_rows = []
    for row in original['scenes']:
        job = previous['jobs'][row['scene']]
        prior_run = {'completed': False, 'status': job['status']}
        if job.get('summary'):
            actual = (ROOT / job['chain']).parent / 'imagination_strict'
            prior_run.update(summary=job['summary'], run_id=job['run_id'],
                             run=str(actual.relative_to(ROOT)), completed=True)
        prior_rows.append({'scene': row['scene'], 'sample_scope': 'earlier_v2_same_scene_integration_attempt',
                           'runs': {'imagination_strict': prior_run}})
    cf = []
    for path in sorted((ROOT / a.counterfactuals).rglob('counterfactuals.json')):
        result = json.loads(path.read_text())
        cf.append({**{k: result[k] for k in ('scene', 'policy', 'completed', 'rejected_candidates', 'executed',
                                           'collisions', 'noncollisions', 'unexecutable', 'all_executed_prefixes_verified')},
                   'ledger': str(path.relative_to(ROOT))})
    report = {'schema': 'beforestep-r3-suite-summary/v1', 'post_result_revision': True,
              'original_preregistered_primary_results': 'evidence/suite/summary.json',
              'frozen': rows, 'holdouts': held_rows, 'frozen_stats': strict_stats(rows),
              'holdout_stats': strict_stats(held_rows), 'all_run_stats': strict_stats(rows + held_rows),
              'prior_real_v2': prior_rows, 'prior_real_v2_stats': strict_stats(prior_rows),
              'f1_unused_decisive_available': False, 'new_rejected_counterfactuals': cf,
              'new_rejected_counterfactual_stats': {
                  'executed': sum(r['executed'] for r in cf),
                  'collisions': sum(r['collisions'] for r in cf),
                  'noncollisions': sum(r['noncollisions'] for r in cf),
                  'unexecutable': sum(r['unexecutable'] for r in cf)},
              'paid_tasks': {'new_r3': R3Budget.usage(budget), 'r2': 168,
                             'cumulative_r2_r3': 168 + R3Budget.usage(budget), 'r3_limit': 170, 'original_limit': 360},
              'new_task_provenance': [{key: task[key] for key in (
                  'scene', 'sample', 'request', 'request_sha256', 'input_sha256', 'identity', 'status', 'task_id')}
                  for task in budget['tasks'].values() if task['new_r3_task']],
              'scope': 'Known-scene reruns are a post-result revision. Only the prescribed held-out scenes can support an out-of-sample claim. All outcomes are retained.'}
    C.atomic_json(ROOT / 'evidence/reviews/beforestep_r3/summary.json', report)
    print(json.dumps({key: report[key] for key in ('frozen_stats', 'holdout_stats', 'paid_tasks')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
