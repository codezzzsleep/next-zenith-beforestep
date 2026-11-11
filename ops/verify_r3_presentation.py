"""Audit R3 claims against raw runs, task ledgers and original byte identities."""
import hashlib
import json
from pathlib import Path

from beforestep.generation import client as C
from r3_lux_budget import R3Budget
from run_r3_counterfactuals import new_rejections
from run_suite_imagination import sources

ROOT = C.ROOT


def read(path):
    return json.loads(path.read_text())


def check():
    data = read(ROOT / 'evidence/reviews/beforestep_r3/summary.json')
    original = read(ROOT / 'evidence/suite/summary.json')
    plan = read(ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json')
    budget = read(ROOT / 'outputs/generation/r3-budget.json')
    assert data['post_result_revision']
    assert [r['scene'] for r in data['frozen']] == [r['scene'] for r in original['scenes']]
    assert [r['scene'] for r in data['holdouts']] == [r['scene'] for r in plan['holdouts']]
    assert R3Budget.usage(budget) == data['paid_tasks']['new_r3'] <= 170
    assert data['paid_tasks']['cumulative_r2_r3'] == 168 + R3Budget.usage(budget)
    assert all(t['status'] in ('ok', 'failed', 'not_submitted') for t in budget['tasks'].values())
    assert {row['identity'] for row in data['new_task_provenance']} == {
        row['identity'] for row in budget['tasks'].values() if row['new_r3_task']}
    for row in data['new_task_provenance']:
        assert all(value == budget['tasks'][row['identity']][key] for key, value in row.items())
    checked = []
    for row, old in zip(data['frozen'], original['scenes']):
        for policy in ('conservative', 'see_dark', 'optimistic', 'truth', 'imagination'):
            assert row['runs'][policy] == old['runs'][policy]
    for row in data['frozen'] + data['holdouts']:
        for policy, record in row['runs'].items():
            if not record.get('summary'):
                continue
            current = policy == 'imagination_strict' or row['sample_scope'] == 'designated_holdout'
            if not current:
                continue
            run = ROOT / record['run']
            summary, identity = read(run / 'summary.json'), read(run / 'run_identity.json')
            assert record['summary'] == summary and record['run_id'] == identity['run_id']
            assert identity['source_sha256'] == sources()
            assert summary['controller'] == 'rules'
            assert summary['looks'] <= (5 if policy != 'imagination' else 2)
            if policy in ('imagination', 'imagination_strict'):
                assert record['trajectory_sha256'] == hashlib.sha256((run / 'traj.npz').read_bytes()).hexdigest()
                first = record.get('first_view_verification')
                if policy == 'imagination_strict':
                    assert first and first['passed']
                    for name in ('rgb.png', 'depth.npy', 'dark.npy', 'state.npy', 'zmax.npy'):
                        filename = 'look1_' + name
                        assert C.sha(ROOT / first['source'] / 'looks' / filename) == C.sha(run / 'looks' / filename)
                for target in record['targets']:
                    decision = read(ROOT / target['source_decision'])
                    assert target['admitted'] == sum(c['admitted'] for c in decision['candidates'])
                    assert target['rejected'] == sum(not c['admitted'] for c in decision['candidates'])
                assert record['public_manifest'] and (ROOT / record['public_manifest']).exists()
            checked.append({'scene': row['scene'], 'policy': policy, 'run_id': identity['run_id']})

    def stats(rows):
        summaries = [r['runs']['imagination_strict']['summary'] for r in rows
                     if r['runs'].get('imagination_strict', {}).get('summary')]
        collisions = [s['scene_id'] for s in summaries if s['collision'] is not None or s['result'] == 'collision']
        return {'completed': len(summaries), 'arrived': sum(s['result'] == 'arrived' and s['collision'] is None for s in summaries),
                'safe_stop': sum(s['result'] != 'arrived' and s['result'] != 'collision' and s['collision'] is None for s in summaries),
                'collisions': len(collisions), 'collision_scenes': collisions}
    for key, rows in (('frozen_stats', data['frozen']), ('holdout_stats', data['holdouts']),
                      ('all_run_stats', data['frozen'] + data['holdouts'])):
        for field, expected in stats(rows).items():
            assert data[key][field] == expected, (key, field)
        sd = [r for r in rows if r['runs'].get('see_dark', {}).get('summary', {}).get('result') == 'arrived']
        assert data[key]['see_dark_arrived_scenes'] == len(sd)
        assert data[key]['strict_arrived_among_see_dark_arrived'] == sum(
            r['runs'].get('imagination_strict', {}).get('summary', {}).get('result') == 'arrived' for r in sd)
    cf_count, cf_collisions = 0, 0
    for record in data['new_rejected_counterfactuals']:
        cf = read(ROOT / record['ledger'])
        assert cf['completed'] and cf['all_executed_prefixes_verified']
        assert cf['candidates'] == new_rejections(ROOT / cf['original_run'], budget)
        assert cf['executed'] + cf['unexecutable'] == len(cf['candidates'])
        assert cf['collisions'] == sum(r['collision'] for r in cf['runs'].values() if r['executed'])
        cf_count += cf['executed']; cf_collisions += cf['collisions']
    report = (ROOT / 'docs/report.md').read_text()
    assert report.count('<!-- R3-METHOD-START -->') == 1
    assert report.count('<!-- R3-METHOD-END -->') == 1
    chapter = report.split('<!-- R3-METHOD-START -->')[1].split('<!-- R3-METHOD-END -->')[0]
    for row in data['frozen'] + data['holdouts']:
        lines = [line for line in chapter.splitlines() if line.startswith('| ' + row['scene'] + ' |')]
        assert lines
        cells = lines[0].split('|')[2:-1]
        for cell, policy in zip(cells, ('conservative', 'see_dark', 'optimistic', 'imagination', 'imagination_strict')):
            summary = row['runs'].get(policy, {}).get('summary')
            if summary:
                assert f"{summary['looks']}眼" in cell and f"{summary['sim_time_s']:.2f}s" in cell
                expected = '碰撞' if summary['collision'] is not None or summary['result'] == 'collision' else {'arrived': '到达', 'stuck': '停车', 'stopped_short': '未到达停车'}[summary['result']]
                assert expected in cell
            else:
                assert '未完成' in cell
    page = (ROOT / 'site/index.html').read_text()
    assert page.count('id="post-result-revision"') == 1
    if data['all_run_stats']['collisions']:
        assert 'id="r3-collision-warning"' in page
        for scene in data['all_run_stats']['collision_scenes']:
            assert scene in page.split('id="r3-collision-warning"')[1].split('</p>')[0]
    result = {'passed': True, 'checked_current_runs': checked,
              'first_view_original_bytes_verified': True,
              'original_five_policy_records_unchanged': True,
              'fixed_scene_order_verified': True, 'r3_paid_tasks': R3Budget.usage(budget),
              'new_counterfactual_executed': cf_count, 'new_counterfactual_collisions': cf_collisions}
    C.atomic_json(ROOT / 'evidence/reviews/beforestep_r3/presentation-audit.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False))
