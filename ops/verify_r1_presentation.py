"""Compare R1 website/report numbers and playback with original evidence.

This is a read-only audit; it does not rebuild presentation or run an experiment.
The numeric inventory rejects untraceable literal numbers in the R1 narrative.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

import markdown
import numpy as np

from verify_r1_evidence import ROOT, BASE, read, sha


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('head', 'script', 'style', 'code'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('head', 'script', 'style', 'code'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def visible(html):
    parser = VisibleText()
    parser.feed(html)
    return ' '.join(' '.join(parser.parts).split())


def check():
    data = read(ROOT / 'site/data/demo.json')
    index = read(ROOT / 'site/data/scenes.json')
    assert index['default'] == 'stress_v8_r1'
    assert data['review_id'] == 'R1' and data['scene_id'] == 'stress_v8'
    assert data['goal'] == read(BASE / 'lux/original_b/scene.json')['goal']
    checks = []
    numbers = {}

    def fact(value, source, multiplier=1):
        for precision in (0, 1, 2, 3, 4, 5, 6):
            token = f'{value * multiplier:.{precision}f}'
            numbers.setdefault(token, []).append(source)
        numbers.setdefault(str(value * multiplier), []).append(source)

    # Explicit source inventory, rather than arbitrary numbers from unrelated JSON.
    for key, row in data['runs'].items():
        run = ROOT / row['evidence']
        summary, identity = read(run / 'summary.json'), read(run / 'run_identity.json')
        assert all(row[field] == value for field, value in summary.items()), key
        assert row['run_id'] == identity['run_id']
        assert identity['arguments']['controller_model'] == 'rules'
        assert identity['arguments']['pose_model'] is None
        assert summary['goal'] == [10.5, 0.0]
        events = [json.loads(line) for line in (run / 'events.jsonl').read_text().splitlines()]
        panes = [p for e in events if e['kind'] == 'rehearsal' for p in e['panes']]
        assert row['rehearsals'] == len(panes)
        assert row['rehearsals_passed'] == sum(p['completed'] and not p['collided'] for p in panes)
        track = dict(np.load(run / 'traj.npz'))
        for t, x, y, yaw in row['trajectory']:
            i = int(np.argmin(abs(track['t'] - t)))
            q = track['qpos'][i]
            expected_yaw = np.arctan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
            assert abs(track['t'][i] - t) <= .000051
            assert abs(q[0]-x) <= .0000051 and abs(q[1]-y) <= .0000051
            assert abs(expected_yaw-yaw) <= .00000051
        fact(summary['sim_time_s'], row['evidence'] + '/summary.json#/sim_time_s')
        fact(summary['looks'], row['evidence'] + '/summary.json#/looks')
        checks.append({'run': key, 'run_id': row['run_id'], 'trajectory_points': len(row['trajectory'])})
    tasks = []
    for target in ('T1', 'T2'):
        run = BASE / 'lux/original_b/looks/look1' / target
        raw = read(run / 'lux_result.json')['tasks']
        tasks.extend(raw)
        decision = read(run / 'decide/target_decision.json')
        state = read(run / 'state.json')
        assert data['target_states'][target] == state
        fact(state['crop_native_px'], str(run.relative_to(ROOT)) + '/state.json#/crop_native_px')
        for task in raw:
            fact(task['task_id'], str(run.relative_to(ROOT)) + '/lux_result.json')
            rows = [c for c in data['candidates'] if c['task_id'] == task['task_id']]
            if task['status'] != 'ok':
                assert not rows
                continue
            assert len(rows) == 1
            row = rows[0]
            original = next(c for c in decision['candidates'] if c['id'] == task['id'])
            for field in ('contour_iou', 'scale_ratio', 'admitted'):
                assert row[field] == original[field]
            assert row['native_px'] == state['crop_native_px'] and row['native_ok'] == state['native_ok']
            assert row['thresholds'] == decision['thresholds']
            assert row['glb'] == task['glb'] and (ROOT / row['glb']).exists()
            fact(row['contour_iou'], str(run.relative_to(ROOT)) + '/decide/target_decision.json')
            fact(row['scale_ratio'], str(run.relative_to(ROOT)) + '/decide/target_decision.json')
    assert data['generation']['tasks'] == len(tasks) == 12
    assert data['generation']['succeeded'] == sum(t['status'] == 'ok' for t in tasks) == 11
    assert data['generation']['failed'] == 1
    assert data['generation']['admitted'] == sum(c['admitted'] for c in data['candidates']) == 8
    original = BASE / 'lux/original_b'
    evaluation = read(original / 'eval.json')
    physical = read(original / 'physical_clearance.json')
    optimistic = read(BASE / 'section25_final_base/optimistic/eval.json')
    xy = evaluation['actual_clearance_by_rock']['B']
    audit = data['audit']
    assert audit['physical_clearance_B_m'] == physical['rocks']['B']['minimum_signed_collision_geometry_distance_m']
    assert audit['xy_envelope_clearance_B_m'] == xy['min_xy_rectangle_envelope_gap_m']
    assert audit['xy_center_minus_half_width_B_m'] == xy['min_center_minus_half_width_m']
    assert audit['cold_wall_s'] == read(original / 'summary.json')['wall_s']
    assert audit['optimistic_intrusion_m'] == optimistic['first_departure_plan_by_rock']['B']['planned_envelope_intrusion_proxy_m']
    assert audit['counterfactual_collisions'] == sum(data['runs']['trust_' + c]['collision'] is not None for c in ('A1', 'B1', 'C2')) == 0
    assert audit['replay_trajectory_sha256'] == sha(original / 'traj.npz') == sha(BASE / 'lux/replay/traj.npz')
    panes = evaluation['execution_rehearsals'][0]['panes']
    assert len(data['gallery']) == len(panes) == 12
    for row, pane in zip(data['gallery'], panes):
        assert row['pane'] == pane['pane'] and row['completed'] == pane['completed'] and row['collided'] == pane['collided']
        track = dict(np.load(original / 'rehearsal/look1' / ('pane' + str(pane['pane'])) / 'traj.npz'))
        for t, x, y, _ in row['trajectory']:
            i = np.argmin(abs(track['t'] - t))
            assert abs(track['qpos'][i, 0] - x) <= .0000051 and abs(track['qpos'][i, 1] - y) <= .0000051
    # Narrative literals: specific source values plus the registered R1 rules.
    for value in (len(tasks), len(data['candidates']), len(panes), 6, 2, 3, 8):
        fact(value, 'lux/original_b: task/admission/rehearsal counts')
    for value in data['goal']:
        fact(value, 'lux/original_b/scene.json#/goal')
    threshold = read(original / 'looks/look1/T2/decide/target_decision.json')['thresholds']
    for value in (threshold['contour_iou_min'], threshold['scale_ratio']['min'], threshold['scale_ratio']['max']):
        fact(value, 'lux/original_b/looks/look1/T2/decide/target_decision.json#/thresholds')
    fact(read(ROOT / 'config/protocol.json')['inputs']['min_native_px'], 'config/protocol.json#/inputs/min_native_px')
    for key in ('A', 'B'):
        fact(physical['rocks'][key]['minimum_signed_collision_geometry_distance_m'], 'lux/original_b/physical_clearance.json', 1000)
    fact(audit['xy_center_minus_half_width_B_m'], 'lux/original_b/eval.json', 1000)
    fact(audit['xy_center_minus_half_width_B_m'], 'lux/original_b/eval.json')
    fact(audit['xy_envelope_clearance_B_m'], 'lux/original_b/eval.json')
    fact(audit['cold_wall_s'], 'lux/original_b/summary.json#/wall_s')
    fact(audit['optimistic_intrusion_m'], 'section25_final_base/optimistic/eval.json', 100)
    fact(5, 'REVIEW_BEFORESTEP_R1.md: frozen 5 cm planning rule')
    for field in ('half_len', 'half_wid'):
        fact(evaluation['robot_envelope'][field], 'lux/original_b/eval.json#/robot_envelope', 2)
    standin = BASE / 'standins/registration_fixed'
    event = next(json.loads(l) for l in (standin / 'events.jsonl').read_text().splitlines() if json.loads(l)['kind'] == 'second_look_plan')
    fact(event['target_native_px_expected'], 'standins/registration_fixed/events.jsonl#/second_look_plan')
    fact(read(standin / 'looks/look2/T2/state.json')['crop_native_px'], 'standins/registration_fixed/looks/look2/T2/state.json')
    fact(read(standin / 'looks/look2/T2/decide/target_decision.json')['candidates'][0]['contour_iou'], 'standins/registration_fixed/looks/look2/T2/decide/target_decision.json')
    for candidate in data['candidates']:
        if candidate['target'] == 'T2' and candidate['admitted']:
            fact(abs(candidate['back_error_m']), 'lux/original_b: registered footprint vs post-run truth')
    training = np.load(ROOT / 'assets/training/goal_controller_v4/demonstrations.npz')
    fact(len(training[training.files[0]]), 'assets/training/goal_controller_v4/demonstrations.npz')
    training_eval = read(ROOT / 'evidence/learning/held_out_v4/summary.json')['controllers']['v4']
    for field in ('successes', 'episodes'):
        fact(training_eval[field], 'evidence/learning/held_out_v4/summary.json#/controllers/v4')
    fact(5.7, 'historical trained gate goal (retained data/history/trained_gate_v03.json)')
    fact(-.5, 'historical trained gate goal (retained data/history/trained_gate_v03.json)')
    assert 'Ran 40 tests' in (BASE / 'logs/r1_registration_fix_tests.log').read_text()
    fact(40, 'logs/r1_registration_fix_tests.log')
    report = (ROOT / 'docs/report.md').read_text()
    report_html = (ROOT / 'site/report.html').read_text()
    assert visible(markdown.markdown(report, extensions=['tables', 'fenced_code'])) == visible(report_html)
    # Check table columns and exact key claims, so unrelated valid numbers cannot mask drift.
    for key in ('conservative', 'see_dark', 'optimistic', 'imagination', 'truth'):
        row = data['runs'][key]
        assert f"| {data['labels'][key]} |" in report
        assert f"| {row['looks']} | {row['sim_time_s']} s | [原始身份](../{row['evidence']}/run_identity.json) |" in report
    for cid in ('A1', 'B1', 'C2'):
        row = data['runs']['trust_' + cid]
        assert f"| B/{cid} | 到达、无碰撞 | {row['sim_time_s']} s | [原始身份](../{row['evidence']}/run_identity.json) |" in report
    for row in data['candidates']:
        if row['target'] == 'T2':
            assert f"| B/{row['sample_id']} | {row['task_id']} | {row['contour_iou']} | {row['scale_ratio']} |" in report
    for literal in (f"B {audit['physical_clearance_B_m']*1000:.3f} mm", f"中心减半宽={audit['xy_center_minus_half_width_B_m']:.6f} m", f"墙钟 {audit['cold_wall_s']} s", '0/3', 'native_ok=false'):
        assert literal in report, literal
    inventory = {}
    suite_audit = None
    if (ROOT / 'evidence/suite/summary.json').exists():
        from verify_suite_presentation import check as check_suite
        suite_audit = check_suite()
        def suite_facts(value, source):
            if isinstance(value, dict):
                for key, child in value.items():
                    suite_facts(child, source + '/' + key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    suite_facts(child, source + '/' + str(index))
            elif isinstance(value, (float, int)) and not isinstance(value, bool):
                fact(value, source)
                fact(value, source, 1000)
        suite_facts(read(ROOT / 'evidence/suite/summary.json'), 'evidence/suite/summary.json#')
        for row in read(ROOT / 'evidence/suite/summary.json')['scenes']:
            diagnostic = (row.get('failure_reason') or {}).get('diagnostic_evidence')
            if diagnostic:
                value = read(ROOT / diagnostic)
                fact(value['rehearsal_combinations'], diagnostic + '#/rehearsal_combinations')
                for index, comparison in enumerate(value['admitted_B_candidates']):
                    fact(comparison['truth_B_covered_fraction'],
                         diagnostic + '#/admitted_B_candidates/' + str(index) + '/truth_B_covered_fraction', 100)
        frozen = read(ROOT / 'config/suite/frozen.json')
        for pool in frozen['pool_sources']:
            suite_facts(read(ROOT / pool['path']), pool['path'] + '#')
        for value in (1, 2, 3, 4, 5, 6, 8, 12, 150, 360):
            fact(value, 'docs/reviews/SPEC_BEFORESTEP_R2.md: preregistered rules')
        revision = ROOT / 'evidence/reviews/beforestep_r3/summary.json'
        if revision.exists():
            from verify_r3_presentation import check as check_revision
            check_revision()
            suite_facts(read(revision), 'evidence/reviews/beforestep_r3/summary.json#')
            for value in (0.05, 5.00, 170, 338):
                fact(value, 'docs/reviews/SPEC_BEFORESTEP_R3.md: fixed revision rules')
            prior = ROOT / 'evidence/reviews/beforestep_r3/prior-real-v2/F1_003-collision.json'
            if prior.exists():
                suite_facts(read(prior), str(prior.relative_to(ROOT)) + '#')
        for path in ('evidence/reviews/beforestep_r3/back-error/stats.json',
                     'evidence/reviews/beforestep_r3/failure-facts.json',
                     'evidence/reviews/beforestep_r3/sun-diagnostic/diagnostic.json'):
            if (ROOT / path).exists():
                suite_facts(read(ROOT / path), path + '#')
                def centimeters(value, source):
                    if isinstance(value, dict):
                        for key, child in value.items(): centimeters(child, source+'/'+key)
                    elif isinstance(value, list):
                        for index, child in enumerate(value): centimeters(child, source+'/'+str(index))
                    elif isinstance(value, (int, float)) and not isinstance(value, bool): fact(value, source, 100)
                centimeters(read(ROOT / path), path + '#')
        award = ROOT / 'evidence/award/facts.json'
        if award.exists():
            values = read(award)
            primary = read(ROOT / 'evidence/suite/summary.json')
            task_ids = {task for row in primary['scenes'] for target in row['targets'].values()
                        for view in target['views'] for task in view['task_ids']}
            assert values['original_unique_tasks'] == len(task_ids)
            assert values['original_generated_glb'] == suite_audit['candidate_footprints']
            assert values['original_admitted'] == read(ROOT / 'evidence/reviews/beforestep_r3/back-error/stats.json')['candidate_count']
            assert values['original_rejected'] == primary['counterfactuals']['executed']
            suite_facts(values, 'evidence/award/facts.json#')
            # Selected asset task IDs come from the original asset manifest,
            # rather than being admitted just because they appear in captions.
            asset_rows = read(ROOT / 'assets/manifest.json')['entries']
            selected = read(ROOT / 'evidence/award/asset-iterations/manifest.json')['versions']
            for version in selected:
                model = version['model']
                assert sha(ROOT / model['path']) == model['sha256']
                for index, entry in enumerate(asset_rows):
                    if entry['path'] == model['path'] and entry.get('task_id'):
                        fact(entry['task_id'], f'assets/manifest.json#/entries/{index}/task_id')
                if version.get('source_result'):
                    result = read(ROOT / version['source_result'])
                    for index, task in enumerate(result['tasks']):
                        if task.get('glb') == model['path']:
                            assert task['glb_sha256'] == model['sha256']
                            assert task['task_id'] == version['task_id']
                            fact(task['task_id'], version['source_result'] + f'#/tasks/{index}/task_id')
    for name, html in [('site/index.html', (ROOT / 'site/index.html').read_text()), ('docs/report.md', markdown.markdown(report, extensions=['tables', 'fenced_code']))]:
        tokens = re.findall(r'(?<![A-Za-z0-9_.])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9_])', visible(html))
        inventory[name] = {}
        for token in tokens:
            if token in ('01', '02', '03', '04', '05', '06', '07', '08', '2.4'):
                continue  # Story section numbering, not an experimental claim.
            assert token in numbers, (name, 'untraceable literal', token)
            inventory[name][token] = sorted(set(numbers[token]))
    return {'schema': 'beforestep-r1-presentation-audit/v1', 'passed': True,
            'runs_checked': checks, 'candidate_metrics_checked': len(data['candidates']),
            'rehearsal_trajectories_checked': len(panes), 'report_html_matches_markdown': True,
            'numeric_literal_sources': inventory, 'suite_audit': suite_audit}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
