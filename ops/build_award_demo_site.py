"""Expose the labelled demonstration as a complete recorded workflow."""
import hashlib
import json
from pathlib import Path
import re
import shutil

import markdown
import numpy as np
from beforestep.navigation.controller import yaw_of
from beforestep.navigation import map as N

ROOT = Path(__file__).resolve().parents[1]
LABEL = '赛后补充演示运行，不参与结论、不作为泛化证据'


def track(path, count=700):
    with np.load(path) as z:
        t, q = z['t'], z['qpos']
        indices = np.unique(np.r_[np.arange(0, len(t), max(1, len(t)//count)), len(t)-1])
        return [[float(t[i]), float(q[i, 0]), float(q[i, 1]), float(yaw_of(q[i]))] for i in indices]


def main():
    result = json.loads((ROOT / 'evidence/award/demo/result.json').read_text())
    plan = json.loads((ROOT / 'evidence/award/demo/plan.json').read_text())
    budget = json.loads((ROOT / 'outputs/generation/award-budget.json').read_text())
    from award_lux_budget import AwardBudget
    scene = result['scene']
    main_run = ROOT / result['runs']['imagination']['run']
    media = ROOT / 'site/media/award/demo'
    media.mkdir(parents=True, exist_ok=True)
    first = main_run / 'looks/look1_rgb.png'
    shutil.copy2(first, media / 'first.png')
    state = np.load(main_run / 'looks/look1_state.npy')
    data = {'schema': 'beforestep-award-recorded-demo/v1', 'label': LABEL, 'scene': scene,
            'status': result['status'], 'goal': json.loads((main_run / 'scene.json').read_text())['goal'],
            'image': 'media/award/demo/first.png', 'image_source': str(first.relative_to(ROOT)),
            'image_source_sha256': hashlib.sha256(first.read_bytes()).hexdigest(),
            'map': {'shape': list(state.shape), 'origin': [N.X0, N.Y0], 'resolution': N.RES, 'values': state.ravel().tolist()},
            'runs': {}, 'candidates': [], 'rehearsals': [], 'counterfactuals': [],
            'manifest': f'evidence/award/demo/scenes/{scene}/manifest.json',
            'paid_tasks': AwardBudget.usage(budget),
            'cumulative_tasks': budget['prior_r2_tasks'] + budget['prior_r3_tasks'] + AwardBudget.usage(budget)}
    for policy in plan['policies']:
        row = result['runs'].get(policy, {})
        if row.get('summary'):
            run = ROOT / row['run']
            data['runs'][policy] = {'summary': row['summary'], 'run_id': row['run_id'],
                                   'trajectory': track(run / 'traj.npz'), 'source': row['run']}
        else:
            data['runs'][policy] = {'summary': None, 'reason': '配额或已记录的未完成状态；不计为到达或安全结果。'}
    candidates = []
    for path in main_run.glob('looks/look*/T*/decide/target_decision.json'):
        result_rows = json.loads((path.parent.parent / 'lux_result.json').read_text())['tasks']
        retry = path.parent.parent / 'retry/lux_result.json'
        if retry.exists():
            result_rows += json.loads(retry.read_text())['tasks']
        tasks = {r['id']: r for r in result_rows}
        for candidate in json.loads(path.read_text())['candidates']:
            task = tasks[candidate['id']]
            candidates.append({'task_id': task['task_id'], 'sample': candidate['id'], 'admitted': candidate['admitted'],
                               'contour_iou': candidate.get('contour_iou'), 'source_glb': task['glb'],
                               'source_decision': str(path.relative_to(ROOT))})
    selected = []
    for admitted in [True, False]:
        row = next((r for r in candidates if r['admitted'] == admitted), None)
        if row:
            glb = ROOT / row['source_glb']
            target = media / (str(row['task_id']) + '.glb')
            shutil.copy2(glb, target)
            selected.append({**row, 'glb': str(target.relative_to(ROOT / 'site')),
                             'glb_sha256': hashlib.sha256(glb.read_bytes()).hexdigest()})
    data['candidates'] = selected
    data['all_candidate_checks'] = candidates
    events = [json.loads(line) for line in (main_run / 'events.jsonl').read_text().splitlines()]
    for event in events:
        if event['kind'] != 'rehearsal':
            continue
        for pane in event['panes']:
            run = main_run / 'rehearsal' / f"look{event['look']}" / ('pane' + str(pane['pane']))
            if (run / 'traj.npz').exists():
                data['rehearsals'].append({'label': f"look{event['look']} / pane{pane['pane']}",
                    'completed': pane['completed'], 'collided': pane['collided'], 'trajectory': track(run / 'traj.npz')})
    cf_root = ROOT / 'outputs/award/demo/counterfactuals' / scene
    for path in cf_root.glob('*/counterfactuals.json'):
        cf = json.loads(path.read_text())
        for key, row in cf['runs'].items():
            if row.get('summary'):
                data['counterfactuals'].append({'label': path.parent.name + ' / ' + key, 'summary': row['summary'],
                    'trajectory': track(ROOT / row['run'] / 'traj.npz'), 'prefix_verified': (row.get('prefix_verification') or {}).get('passed'),
                    'source': row['run']})
    (ROOT / 'site/data/award-demo.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'))+'\n')
    rows = '| 方法 | 真实终态 | 眼数 | 仿真总时长 |\n| --- | --- | --- | --- |\n'
    names = {'conservative': '保守', 'see_dark': '黑影测深对照', 'optimistic': '乐观', 'truth': '真实形状检验',
             'imagination': '原想象', 'imagination_strict': '修订想象'}
    for policy, row in data['runs'].items():
        s = row['summary']
        rows += f"| {names[policy]} | {s['result'] if s else '未完成'} | {s['looks'] if s else '—'} | {str(s['sim_time_s'])+'s' if s else '—'} |\n"
    chapter = f'## 赛后补充演示：{scene}\n\n**{LABEL}。** 按运行前固定计划选择种子 {plan["seed"]}，不看结果换场景。新增任务 {data["paid_tasks"]}，R2/R3/补充演示累计 {data["cumulative_tasks"]}/360，最新累计上限316。\n\n' + rows + f'\n[逐步可点的真实记录流程](../site/award-demo.html) · [预期与选择规则](../evidence/award/demo/plan.json) · [原始结果](../evidence/award/demo/result.json) · [完整保全清单](../{data["manifest"]})。\n\n'
    report = ROOT / 'docs/report.md'
    body = re.sub(r'<!-- AWARD-DEMO-START -->[\s\S]*?<!-- AWARD-DEMO-END -->\n?', '', report.read_text())
    body = body.replace('## 沙盒\n', '<!-- AWARD-DEMO-START -->\n'+chapter+'<!-- AWARD-DEMO-END -->\n\n## 沙盒\n', 1)
    report.write_text(body)
    from r3_presentation import render_report
    render_report(body)
    html = markdown.markdown(chapter, extensions=['tables']).replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>').replace('href="../site/', 'href="').replace('href="../evidence/', 'href="evidence/')
    page = ROOT / 'site/index.html'
    content = re.sub(r'<section id="award-demonstration">[\s\S]*?</section>', '', page.read_text())
    content = content.replace('<section id="sandbox">', '<section id="award-demonstration">'+html+'</section><section id="sandbox">', 1)
    page.write_text(content)
    print(json.dumps({'scene': scene, 'new_tasks': data['paid_tasks'], 'columns': len(data['runs']),
                      'rehearsals': len(data['rehearsals']), 'counterfactuals': len(data['counterfactuals']), 'label': LABEL}))


if __name__ == '__main__':
    main()
