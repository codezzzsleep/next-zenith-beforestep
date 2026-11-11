"""Derive the showcase diagram, report additions and English summary from evidence."""
import hashlib
from collections import Counter
import json
from pathlib import Path
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]


def main():
    read = lambda p: json.loads((ROOT / p).read_text())
    original = read('evidence/suite/summary.json')
    revised = read('evidence/reviews/beforestep_r3/summary.json')
    assets = read('evidence/award/asset-iterations/manifest.json')
    tasks = {task for row in original['scenes'] for target in row['targets'].values()
             for view in target['views'] for task in view['task_ids']}
    task_rows, admitted_ids = {}, set()
    # One observed target can be associated with several rocks. Count actual
    # task identities and decisions rather than adding per-rock display rows.
    for row in original['scenes']:
        run = ROOT / row['runs']['imagination']['run']
        for path in run.glob('looks/look*/T*/lux_result.json'):
            rows = json.loads(path.read_text())['tasks']
            retry = path.parent / 'retry/lux_result.json'
            if retry.exists():
                rows += json.loads(retry.read_text())['tasks']
            for task in rows:
                old = task_rows.setdefault(task['task_id'], task['status'])
                assert old == task['status']
            decision = json.loads((path.parent / 'decide/target_decision.json').read_text())
            by_sample = {task['id']: task for task in rows}
            admitted_ids |= {by_sample[c['id']]['task_id'] for c in decision['candidates'] if c['admitted']}
    assert set(task_rows) == tasks
    generated = sum(status == 'ok' for status in task_rows.values())
    admitted = len(admitted_ids)
    facts = {'schema': 'beforestep-award-facts/v1', 'original_unique_tasks': len(tasks),
             'original_generated_glb': generated, 'original_admitted': admitted,
             'original_rejected': generated - admitted, 'original_collision_scenes': original['imagination_collision_scenes'],
             'original_counterfactuals': original['counterfactuals'],
             'frozen_revision': revised['frozen_stats'], 'heldout_revision': revised['holdout_stats'],
             'earlier_v2': revised['prior_real_v2_stats'], 'revision_paid_tasks': revised['paid_tasks'],
             'revision_new_counterfactuals_by_scope': revised['new_rejected_counterfactual_stats_by_scope'],
             'sources': ['evidence/suite/summary.json', 'evidence/reviews/beforestep_r3/summary.json',
                         'evidence/award/asset-iterations/manifest.json']}
    (ROOT / 'evidence/award/facts.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2) + '\n')
    known = revised['new_rejected_counterfactual_stats_by_scope']['known_frozen']
    held = revised['new_rejected_counterfactual_stats_by_scope']['designated_holdout']
    new_glb = sum(t['status'] == 'ok' for t in revised['new_task_provenance'])
    steps = [
        ('RGB-D', '真实观测', '机器人实际首眼与补看。太阳黑影与视线遮挡分别处理。'),
        ('AHOLO / LUX3D', '多候选生成', f"原 R1/R2 {len(tasks)} 个唯一任务、{generated} 份成功 GLB；R3 新增 {revised['paid_tasks']['new_r3']} 个任务、{new_glb} 份成功 GLB。"),
        ('REGISTER / CHECK', '配准与冻结自检', f'原批 {admitted} 份准入、{generated-admitted} 份拒绝；只检验可见证据，不能保证背面。'),
        ('OCCUPANCY', '候选进入占据', '原想象与赛后修订保持分开：修订只解释太阳黑影，视线未知仍阻塞。'),
        ('PHYSICS', '逐候选完整预演', '每个采纳世界都以同一控制器走完整条路线，包含补看与最后转向。'),
        ('INDEPENDENT ACT', '独立执行与复盘', f"原想象有 {len(original['imagination_collision_scenes'])} 场碰撞；最终 v3 已知场景碰撞 {revised['frozen_stats']['collisions']}、留出碰撞 {revised['holdout_stats']['collisions']}。oldv2 的碰撞保留。"),
        ('COUNTERFACTUAL', '被拒候选也测试', f"原批 {original['counterfactuals']['collisions']}/{original['counterfactuals']['executed']} 碰撞；修订已知批 {known['executed']} 份、{known['collisions']} 碰撞，留出批 {held['executed']} 份、{held['collisions']} 碰撞。")]
    diagram = '<section id="award-lux-pipeline"><div class="eyebrow">AHOLO / THE CORE WORKFLOW</div><h2>Lux3D 在哪一步，怎样影响行动？</h2><p>下面数字直接来自原结果和修订账本。生成与检查的原批以 R1/R2 为范围；修订单列，反事实按已知与留出分开。</p><div class="award-steps">'
    for eyebrow, title, description in steps:
        diagram += f'<article><span>{eyebrow}</span><h3>{title}</h3><p>{description}</p></article>'
    diagram += '</div><a class="textlink" href="evidence/award/facts.json">每个数字的原始出处 ↗</a></section>'
    transferred = (ROOT / 'evidence/web-assets/technical-transfer.json').exists()
    page = ROOT / ('site/report.html' if transferred else 'site/index.html')
    text = re.sub(r'<section id="award-lux-pipeline">[\s\S]*?</section>', '', page.read_text())
    text = text.replace('<section id="assets">', diagram + '\n<section id="assets">', 1)
    if 'id="award-asset-comparison"' not in text:
        section = '<section id="award-asset-comparison" class="asset-iterations"><div class="eyebrow">REAL ASSETS / SIX VERSIONS</div><h2>关键资产迭代：每一步都能核对。</h2><img src="media/award/asset-iterations.png" alt="V6、V7、V8与v0.1、v0.2、v0.3真实模型和输入的浏览器渲染截图"><p>v0.1 显示真实两图重试，v0.3 示例是实际被拒候选。不同版本并非同一输入的质量排行榜。原模型、全部输入 SHA 与冻结配置逐项公开。</p><a class="button" href="award-assets.html">旋转六个真实资产 →</a><a class="textlink" href="evidence/award/asset-iterations/manifest.json">模型、输入与配置 SHA ↗</a></section>'
        text = text.replace('<section id="evolution">', section + '<section id="evolution">', 1)
    page.write_text(text)
    pipeline_md = '## Lux3D 在完整工程链中的位置\n\n'
    for eyebrow, title, description in steps:
        pipeline_md += f'**{title}（{eyebrow}）** → {description}\n\n'
    pipeline_md += '[数字与原始来源](../evidence/award/facts.json)。仿真行程不包含云端生成与配准墙钟。\n\n'
    asset_md = '## 关键资产迭代对比\n\n![六个版本真实模型与输入，浏览器实际渲染截图](../site/media/award/asset-iterations.png)\n\n'
    asset_md += '图片由本仓库的真实 STL/GLB 在本地查看器加载后截取，没有重绘。V6 的 STL 仅做坐标轴转换后导出查看用 GLB；原件不改。v0.1 展示真实两图重试 M4，v0.3 示例为被拒候选；这不是控制变量相同的模型质量排名。\n\n'
    asset_md += '| 版本 | 真实模型与输入 | 原输入 SHA-256 | 冻结配置 |\n| --- | --- | --- | --- |\n'
    for row in assets['versions']:
        configs = '<br>'.join(f"[{Path(p['path']).name}](../{p['path']})" for p in row['frozen_config'])
        input_links = f"[输入](../{row['input']['path']})" + ''.join(f" · [另一输入](../{p['path']})" for p in row.get('additional_inputs', []))
        input_shas = '<br>'.join('`'+p['sha256']+'`' for p in [row['input'], *row.get('additional_inputs', [])])
        asset_md += f"| {row['version']} | [模型](../{row['model']['path']}) · {input_links}<br>{row['note']} | {input_shas} | {configs} |\n"
    asset_md += '\n[所有模型、输入与配置的完整 SHA 表](../evidence/award/asset-iterations/manifest.json) · [可旋转对照](../site/award-assets.html)。V6 原观测与深度从历史证据逐字节保全在本仓库；v0.1 原上传的两张 JPEG 都有独立 SHA。\n\n'
    report = ROOT / 'docs/report.md'
    body = re.sub(r'<!-- AWARD-REPORT-START -->[\s\S]*?<!-- AWARD-REPORT-END -->\n?', '', report.read_text())
    addition = '<!-- AWARD-REPORT-START -->\n' + pipeline_md + asset_md + '<!-- AWARD-REPORT-END -->\n\n'
    body = body.replace('## 迭代、训练与相关工作', addition + '## 迭代、训练与相关工作', 1)
    failure = re.search(r'<!-- R3-FAILURE-START -->[\s\S]*?<!-- R3-FAILURE-END -->', body)
    if failure:
        original_failure = failure.group(0)
        body = body.replace(original_failure, '', 1).replace('## 窄道的约束', original_failure + '\n\n## 窄道的约束', 1)
    report.write_text(body)
    from r3_presentation import render_report
    render_report(body)
    f, h = revised['frozen_stats'], revised['holdout_stats']
    decisive = [row for row in original['scenes'] if row['classification'] == 'decisive']
    known_original = Counter(row['runs']['imagination']['summary']['result'] for row in decisive)
    holdout_original = Counter(row['runs']['imagination']['summary']['result'] for row in revised['holdouts'])
    en = f'''# BeforeStep — rehearse the side you cannot see

**What.** Aholo Lux3D turns a robot's actual flat photograph into a complete 3D rock, including the unseen side. A wheel-leg robot checks and rehearses these geometry hypotheses before acting in an independent simulation.

**Why.** Solar darkness removes reliable depth; rocks also hide space from view. Changing viewpoint changes visibility, not sunlight. A plausible backside can still be wrong.

**How.** Generate multiple hypotheses → register and check them → construct occupancy → rehearse every admitted world with the same controller → execute independently → review and intervene on rejected candidates. Original R1/R2: {len(tasks)} unique tasks, {generated} successful GLBs, {admitted} admissions and {generated-admitted} rejections.

**Results.** Original imagination, {len(decisive)} preregistered decisive scenes: {known_original['arrived']} arrived / {known_original['stuck']} stopped / {known_original['collision']} collisions (F1_020, unseen C; F3_004, underestimated backside). In the {h['completed']} designated holdouts, original imagination: {holdout_original['arrived']} arrived / {holdout_original['stuck']} stopped / {holdout_original['collision']} collisions; final v3 **post-result revision**: {h['arrived']} arrived / {h['safe_stop']} stopped / {h['collisions']} collisions. The revision removed both collisions and the holdout arrival benefit. Only holdouts support out-of-sample conclusions. Across all {f['completed']} known-scene retests, final v3: {f['arrived']} arrived / {f['safe_stop']} stopped / {f['collisions']} collisions. Early oldv2 collided in F1_003 and remains separate. Imagination is useful, with a measured failure boundary.

**Evidence.** [Report and failures](../site/report.html), [machine-readable results](../evidence/reviews/beforestep_r3/summary.json), [real asset iterations](../site/award-assets.html), [complete video source index](../evidence/video/index.json). This is simulation evidence; universal navigation and hardware success are unproven.

**Links.** [Public source](https://github.com/codezzzsleep/next-zenith-beforestep) · [Playable Demo](https://codezzzsleep.github.io/next-zenith-beforestep/levels.html) · [Historical video](https://codezzzsleep.github.io/next-zenith-beforestep/media/demo.mp4). The project lead prepares the new video from the supplied real run data.
'''
    (ROOT / 'docs/report-en.md').write_text(en)
    rendered = markdown.markdown(en).replace('href="../site/', 'href="').replace('href="../evidence/', 'href="evidence/')
    (ROOT / 'site/en.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="favicon.svg"><link rel="stylesheet" href="style.css"><title>BeforeStep · English summary</title><style>section{max-width:860px}section h1{font-size:44px}</style></head><body><header><a class="brand" href="index.html">NEXT ZENITH · BEFORESTEP</a><a href="index.html">中文 ↗</a></header><main><section>' + rendered + '</section></main></body></html>')
    print(json.dumps({'original_unique_tasks': len(tasks), 'original_glb': generated,
                      'admitted': admitted, 'rejected': generated-admitted,
                      'report_addition': True, 'english_summary': True}))


if __name__ == '__main__':
    main()
