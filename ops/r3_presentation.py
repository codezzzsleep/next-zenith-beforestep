"""R3 P0 presentation, preserving the original registered result blocks."""
import html
import json
from pathlib import Path
import re
import shutil
import subprocess

import markdown

from beforestep import scene as S

ROOT = S.ROOT


def facts():
    suite = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    one = next(row for row in suite['scenes'] if row['scene'] == 'suite_r2_v4_F1_020')
    three = next(row for row in suite['scenes'] if row['scene'] == 'suite_r2_v4_F3_004')
    run = ROOT / three['runs']['imagination']['run']
    decision = json.loads((run / 'looks/look1/T2/decide/target_decision.json').read_text())
    ious = {row['id']: row['contour_iou'] for row in decision['candidates'] if row['admitted']}
    assert ious == {'A1': .8429, 'A2': .8588}
    value = {'schema': 'beforestep-r3-original-failure-facts/v1',
        'scope': 'Post-run explanation; original R1/R2 results and evidence remain unchanged',
        'anchor': S.configure('stress_v8'), 'similar_scene': S.configure(three['scene']),
        'F1_020_C_tasks': one['targets']['C']['tasks'],
        'F1_020_run_id': one['runs']['imagination']['run_id'],
        'F3_004_run_id': three['runs']['imagination']['run_id'],
        'F3_004_B_contour_ious': ious,
        'F3_004_plan_B_intrusion_m': three['review']['optimistic_max_intrusion_m'],
        'anchor_clearance_3d_mm': 47.541, 'anchor_xy_envelope_clearance_mm': 0,
        'sources': ['evidence/suite/summary.json', str((run / 'looks/look1/T2/decide/target_decision.json').relative_to(ROOT))]}
    for key in ('anchor', 'similar_scene'):
        definition = value[key]
        definition['terrain'] = S.terrain_settings(definition)
        definition['sun'] = S.sun_settings(definition)
    assert value['F1_020_C_tasks'] == 0
    out = ROOT / 'evidence/reviews/beforestep_r3'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'failure-facts.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return value


def failure_chapter(data, stats):
    def rock(value):
        return f"{value['rock']}，{value['height']:.2f} m，({value['x']:.2f}, {value['y']:.2f})，{value['yaw']:.0f}°"
    a, b = data['anchor'], data['similar_scene']
    return f"""## 失败分析：想象只能检验看得见的一面

### F1_020：从没被看见的石头

C 完全藏在 A 后面，没有形成观测目标，任务数为 0；原计划路线侵入 C 的真实占地。原想象占据规则是乐观占据加候选占地，视线遮挡 HIDDEN 与未观测 UNSEEN 只要不落在候选中就可通行。**这是方法设计的缺陷，不是 Lux3D 没有生成 C 的问题。**

### F3_004：背面想错，正面仍通过自检

| 场景 | A | B | 地形 | 太阳高度 / 方位 |
| --- | --- | --- | --- | --- |
| stress_v8 | {rock(a['rocks']['A'])} | {rock(a['rocks']['B'])} | 窄道 | {a['sun']['elevation_deg']:.1f}° / {a['sun']['azimuth_deg']:.1f}° |
| F3_004 | {rock(b['rocks']['A'])} | {rock(b['rocks']['B'])} | 开阔月面 + {len(b['terrain']['craters'])} 个坑 | {b['sun']['elevation_deg']:.1f}° / {b['sun']['azimuth_deg']:.1f}° |

B 的 A1、A2 轮廓 IoU 分别为 {data['F3_004_B_contour_ious']['A1']}、{data['F3_004_B_contour_ious']['A2']}，通过冻结自检；原计划路线却按真值压入 B {data['F3_004_plan_B_intrusion_m']*100:.1f} cm，实际发生碰撞。自检只约束可见的一面，不能证明不可见背面的假设正确。

锚点的三维最小间隙 **47.541 mm** 与二维包络间隙 **0 mm** 必须一起理解：同一块扁平石板、几乎相同的摆放换到开阔地形就撞了。**锚点的成功不稳健。** R1 原锚点仍是一眼到达的预注册结果，视频继续使用它，不替换成赛后修订结果。

### 全部准入候选的背面误差

![原R1和R2全部准入候选的赛后背面误差分布](../site/media/r3-back-error.png)

原 R1 + R2 共 **{stats['candidate_count']}** 份通过自检的候选，其中 **{stats['shorter_than_five_cm']}** 份的背面比关联真值短 **5 cm 以上**。误差为每次观测时沿机器人前进轴的候选占地最远端减真值最远端；图中的负 **5 cm** 线是冻结余量。联合观测对关联真值并集统计，所有准入候选逐份入列，真值仅用于赛后诊断，不能证明阴影中的几何已经还原。

[原始统计与每份候选身份](../evidence/reviews/beforestep_r3/back-error/stats.json) · [两次失败的原始数值](../evidence/reviews/beforestep_r3/failure-facts.json) · [给负责人渲染视频的数据索引](../evidence/video/index.json)
"""


def main():
    data = facts()
    stats = json.loads((ROOT / 'evidence/reviews/beforestep_r3/back-error/stats.json').read_text())
    chapter = failure_chapter(data, stats)
    suite = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    summary = '锚点场景中，想象车是三台车里唯一安全到达的；12 个预注册场景中，决定性 8 个：到达 3、安全停车 3、碰撞 2（原因已查明）。'
    folder = ROOT / 'site/media'
    shutil.copy2(ROOT / 'evidence/reviews/beforestep_r3/back-error/figure.png', folder / 'r3-back-error.png')
    old_report = (ROOT / 'evidence/reviews/beforestep_r3/pre-revision/report-r2.md').read_text()
    original_suite = old_report.split('<!-- SUITE-START -->', 1)[1].split('<!-- SUITE-END -->', 1)[0]
    anchor_body = old_report.split('<!-- SUITE-END -->', 1)[1]
    narrative, appendix = anchor_body.split('## 迭代、训练与相关工作', 1)
    introduction = old_report.split('<!-- SUITE-START -->', 1)[0]
    report = introduction + summary + '\n\n' + narrative + '\n## 关卡：先选，再揭晓\n\n每关先看真实第一眼，选策略，回放原物理轨迹，再看真值与全部候选、记分。[进入12关](../site/levels.html)。\n\n<!-- SUITE-START -->' + original_suite + '<!-- SUITE-END -->\n\n<!-- R3-FAILURE-START -->\n' + chapter + '\n<!-- R3-FAILURE-END -->\n\n## 沙盒\n\n[自由摆石头](../site/sandbox.html)是轻量几何规划，不实时调用Lux3D或执行物理仿真。原12场首眼几何8/12一致，全部不一致公开。\n\n## 迭代、训练与相关工作' + appendix
    (ROOT / 'docs/report.md').write_text(report)
    page = subprocess.check_output(['git', 'show', 'dae2b58:site/index.html'], cwd=ROOT, text=True)
    start, end = page.index('<main>') + len('<main>'), page.index('</main>')
    sections = {}
    for match in re.finditer(r'<section\b([^>]*)>[\s\S]*?</section>', page[start:end]):
        name = re.search(r'id="([^"]+)"', match.group(1))
        sections[name.group(1) if name else 'hero'] = match.group(0)
    hero = re.sub(r'<!-- SUITE-HERO-WARNING-START -->[\s\S]*?<!-- SUITE-HERO-WARNING-END -->',
        '<p id="suite-hero-warning" class="hero-result-line">'+summary+' <a href="#failure-analysis">查看原因 ↓</a></p>', sections['hero'])
    warning = sections['suite-collision-alert'].replace('<section ', '<div ', 1).removesuffix('</section>') + '</div>'
    warning = warning.replace('未进入想象世界。', '未进入想象世界；原策略把视线的影子当作可走，这是方法设计缺陷。')
    failure_html = markdown.markdown(chapter, extensions=['tables', 'fenced_code'])
    failure_html = failure_html.replace('src="../site/', 'src="').replace('href="../evidence/', 'href="evidence/')
    failure_html = failure_html.replace('<img ', '<img class="comparison" ')
    failure_html = failure_html.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    failure = '<section id="failure-analysis">'+failure_html+'</section>'
    aggregate = '<div class="eyebrow">PREREGISTERED / ALL OUTCOMES</div><h2>先看结论，再展开全部原记录。</h2><p>决定性：到达3、安全停车3、碰撞2；普通：到达3、停车1、碰撞0。全部拒绝反事实17/102碰撞；真实第二眼5次：1到达、4安全终止、0碰撞。</p>'
    table_body = re.sub(r'^<section[^>]*>|</section>$', '', sections['suite-summary'])
    result = '<section id="suite-summary">'+aggregate+warning+'<details id="suite-details"><summary>展开完整预注册结果与逐场身份</summary>'+table_body+'</details></section>'
    ordered = [hero, sections['shadows'], *[sections[name] for name in ('experience','decision-effect','assets','observation-rule','rehearsal-gallery','truth-audit','counterfactual')], sections['levels'], result, failure, sections['sandbox'], sections['evolution']]
    (ROOT / 'site/index.html').write_text(page[:start]+'\n'+'\n'.join(ordered)+'\n'+page[end:])
    body = markdown.markdown(report, extensions=['tables', 'fenced_code'])
    def url(match):
        attr, value = match.groups()
        if value.startswith(('http:', 'https:', '#')):
            return match.group(0)
        path = (ROOT / 'docs' / value).resolve()
        if path == ROOT / 'config/suite/frozen.json':
            value = 'evidence/suite/frozen.json'
        elif path.is_dir():
            value = 'https://github.com/codezzzsleep/next-zenith-beforestep/tree/main/'+str(path.relative_to(ROOT))
        else:
            value = str(path.relative_to(ROOT / 'site')) if path.is_relative_to(ROOT / 'site') else str(path.relative_to(ROOT))
        return attr+'="'+value+'"'
    body = re.sub(r'(href|src)="([^\"]+)"', url, body)
    previous = (ROOT / 'site/report.html').read_text()
    style = re.search(r'<style>[\s\S]*?</style>', previous).group(0)
    (ROOT / 'site/report.html').write_text('<!doctype html><html lang="zh-CN"><head><link rel="icon" href="favicon.svg"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>先见一步 · 报告</title>'+style+'</head><body>'+body+'</body></html>')
    print(json.dumps({'candidate_count': stats['candidate_count'], 'shorter_than_five_cm': stats['shorter_than_five_cm'], 'original_result_blocks_preserved': True}))


if __name__ == '__main__':
    main()
