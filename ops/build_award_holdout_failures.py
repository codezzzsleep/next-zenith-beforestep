"""Explain each actual held-out original-policy collision from frozen evidence."""
import hashlib
from collections import Counter
import json
from pathlib import Path
import re

import markdown
import numpy as np

from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.evaluation import truth_footprints

ROOT = S.ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary_path = ROOT / 'evidence/reviews/beforestep_r3/summary.json'
    summary = json.loads(summary_path.read_text())
    rows = []
    for scene in summary['holdouts']:
        record = scene['runs']['imagination']
        if record['summary']['result'] != 'collision':
            continue
        run = ROOT / record['run']
        S.configure(scene['scene'])
        truth = truth_footprints(run)
        evaluation = record['postmortem']['eval.json']
        panes = [pane for rehearsal in evaluation['execution_rehearsals'] for pane in rehearsal['panes']]
        candidates = []
        for item in record['targets']:
            path = ROOT / item['source_decision']
            target = path.parent.parent
            cells = np.load(target / 'cells.npy')
            rocks = [name for name, mask in truth.items() if (mask & cells).any()]
            actual = np.logical_or.reduce([truth[name] for name in rocks])
            state = json.loads((target / 'state.json').read_text())
            yaw = state['local_frame']['yaw0']
            projection = N.GX * np.cos(yaw) + N.GY * np.sin(yaw)
            tasks = {task['id']: task for task in json.loads((target / 'lux_result.json').read_text())['tasks']}
            decision = json.loads(path.read_text())
            for candidate in decision['candidates']:
                if not candidate['admitted']:
                    continue
                footprint = path.parent / ('footprint_' + candidate['id'] + '.npy')
                occupied = np.load(footprint)
                candidates.append({'target': target.name, 'sample': candidate['id'],
                    'task_id': tasks[candidate['id']]['task_id'], 'associated_true_rocks': rocks,
                    'contour_iou': candidate['contour_iou'],
                    'back_error_m': float(projection[occupied].max() - projection[actual].max()),
                    'decision': str(path.relative_to(ROOT)), 'decision_sha256': sha(path),
                    'footprint': str(footprint.relative_to(ROOT)), 'footprint_sha256': sha(footprint)})
        contact = record['summary']['collision']
        contact_rock = list(S.ROCKS)[int(contact['body'].removeprefix('obstacle'))]
        relevant = [row for row in candidates if contact_rock in row['associated_true_rocks']]
        assert relevant
        rows.append({'scene': scene['scene'], 'run_id': record['run_id'],
            'trajectory_sha256': record['trajectory_sha256'], 'contact': contact,
            'contact_rock': contact_rock, 'sim_time_s': record['summary']['sim_time_s'],
            'all_rehearsals_passed': all(p['completed'] and not p['collided'] for p in panes),
            'completed_rehearsals': len(panes),
            'planned_envelope_intrusion_proxy_m': evaluation['first_departure_plan_by_rock'][contact_rock]['planned_envelope_intrusion_proxy_m'],
            'contact_rock_candidates': relevant, 'all_admitted_candidates': candidates,
            'public_manifest': record['public_manifest']})
    output = ROOT / 'evidence/award/holdout-collisions.json'
    output.write_text(json.dumps({'schema': 'beforestep-award-heldout-collision-explanations/v1',
        'scope': 'Original imagination in designated holdouts; post-run truth diagnostics only, no production input and no rerun.',
        'source_summary': str(summary_path.relative_to(ROOT)), 'source_summary_sha256': sha(summary_path),
        'back_error_definition': '5cm footprint farthest minus associated true-union farthest along the recorded observation forward axis; same definition as the original back-error diagnostic.',
        'rows': rows}, ensure_ascii=False, indent=2)+'\n')
    chapter = '## 指定留出的两次原想象碰撞\n\n'
    for row in rows:
        errors = [candidate['back_error_m'] for candidate in row['contact_rock_candidates']]
        direction = '采纳几何的背面偏短' if all(error < 0 for error in errors) else '采纳几何未可靠覆盖真实通行边缘'
        chapter += f"- **{row['scene']}**：{direction}，正面自检通过、{row['completed_rehearsals']}个候选世界完整预演全部通过，原路线仍在真实{row['contact_rock']}旁发生接触（{row['sim_time_s']}s）；沿原观测前进轴的准入候选背面误差为 `{errors}` m，计划二维包络侵入代理为 `{row['planned_envelope_intrusion_proxy_m']}` m。\n"
    chapter += '\n背面误差和二维包络代理均为赛后真值诊断，不是生产输入，也不替代实际接触；不从它们推导三维穿透深度。只描述这两次原方法失败，最终v3修订停车的结果另列。[原身份、任务、候选及数值](../evidence/award/holdout-collisions.json)。\n\n'
    report = ROOT / 'docs/report.md'
    body = re.sub(r'<!-- AWARD-HOLDOUT-FAILURES-START -->[\s\S]*?<!-- AWARD-HOLDOUT-FAILURES-END -->\n?', '', report.read_text())
    body = body.replace('## 窄道的约束', '<!-- AWARD-HOLDOUT-FAILURES-START -->\n'+chapter+'<!-- AWARD-HOLDOUT-FAILURES-END -->\n\n## 窄道的约束', 1)
    report.write_text(body)
    from r3_presentation import render_report
    render_report(body)
    page = ROOT / 'site/report.html'
    base = re.sub(r'<section id="award-holdout-failures">[\s\S]*?</section>\n?', '', page.read_text())
    match = re.search(r'<section id="failure-analysis">[\s\S]*?</section>', base)
    assert match
    rendered = markdown.markdown(chapter).replace('href="../evidence/', 'href="evidence/')
    page.write_text(base[:match.end()]+'\n<section id="award-holdout-failures">'+rendered+'</section>\n'+base[match.end():].lstrip('\n'))
    transfer = ROOT / 'evidence/web-assets/technical-transfer.json'
    meta = json.loads(transfer.read_text())
    meta.setdefault('base_technical_page_sha256', meta['technical_page_sha256'])
    meta['technical_page_sha256'] = sha(page)
    meta['new_section'] = {'id': 'award-holdout-failures', 'source': str(output.relative_to(ROOT)), 'source_sha256': sha(output)}
    transfer.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
    related = ROOT / 'docs/related-work.md'
    text = re.sub(r'<!-- AWARD-HOLDOUT-CONTRIBUTION-START -->[\s\S]*?<!-- AWARD-HOLDOUT-CONTRIBUTION-END -->\n?', '', related.read_text())
    original = Counter(row['runs']['imagination']['summary']['result'] for row in summary['holdouts'])
    strict = summary['holdout_stats']
    comparison = (f"指定留出原想象：{original['arrived']}到达、{original['stuck']}停车、{original['collision']}碰撞；最终v3修订：{strict['arrived']}到达、{strict['safe_stop']}停车、{strict['collisions']}碰撞。修订消掉碰撞，也消掉这批留出中的到达收益。两次原想象碰撞的准入B背面偏短、全部候选预演通过与实际接触并列在[新增复盘](../evidence/award/holdout-collisions.json)；仍不据此宣称普遍安全或重建准确。")
    text = text.replace('<!-- R3-CONTRIBUTION-END -->', '<!-- AWARD-HOLDOUT-CONTRIBUTION-START -->\n'+comparison+'\n<!-- AWARD-HOLDOUT-CONTRIBUTION-END -->\n<!-- R3-CONTRIBUTION-END -->', 1)
    related.write_text(text)
    print(json.dumps({'collision_explanations': len(rows), 'rows': [{k:v for k,v in r.items() if k not in ('all_admitted_candidates','contact_rock_candidates')} for r in rows]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
