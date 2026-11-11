"""Add separate R3 result tables after the preserved primary R1/R2 material."""
import html
import json
from pathlib import Path
import re

import markdown
import r3_presentation

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'arrived': '到达', 'stuck': '停车', 'stopped_short': '未到达停车', 'collision': '碰撞'}
POLICIES = ('conservative', 'see_dark', 'optimistic', 'imagination', 'imagination_strict')


def outcome(run):
    summary = run.get('summary')
    if not summary:
        return '未完成'
    result = 'collision' if summary.get('collision') is not None else summary['result']
    return f"{LABELS.get(result, result)} · {summary['looks']}眼 · {summary['sim_time_s']:.2f}s"


def table(rows):
    header = '| 场景 | 保守 | see-dark | 乐观 | 原想象 | 修订想象（赛后） |\n| --- | --- | --- | --- | --- | --- |\n'
    return header + '\n'.join('| ' + row['scene'] + ' | ' + ' | '.join(
        outcome(row['runs'].get(key, {})) for key in POLICIES) + ' |' for row in rows)


def stats_line(stats):
    return f"已完成 {stats['completed']} 场：到达 {stats['arrived']}、停车 {stats['safe_stop']}、碰撞 {stats['collisions']}；未完成 {len(stats['incomplete'])} 场。"


def chapter(data):
    frozen, held = data['frozen'], data['holdouts']
    aggregate = data['all_run_stats']
    if aggregate['collisions']:
        conclusion = '**修订想象仍有碰撞：' + '、'.join(aggregate['collision_scenes']) + '。** 原因与运行身份逐场公开，不能声称修订后没有碰撞。'
    else:
        conclusion = f"**修订后在全部已完成的 {aggregate['completed']} 场中没有碰撞**：到达 {aggregate['arrived']}、停车 {aggregate['safe_stop']}。未完成场景不计入安全或到达数。"
    paired = aggregate['see_dark_pairwise_looks_and_sim_time']
    comparison = '| 场景 | see-dark眼数 / 仿真s | 修订想象结果 / 眼数 / 仿真s |\n| --- | --- | --- |\n'
    for row in paired:
        before, after = row['see_dark'], row['imagination_strict']
        current = '未完成' if after is None else f"{LABELS.get(after['result'], after['result'])} / {after['looks']} / {after['sim_time_s']:.2f}"
        comparison += f"| {row['scene']} | {before['looks']} / {before['sim_time_s']:.2f} | {current} |\n"
    anchor = next(r for r in frozen if r['scene'] == 'stress_v8')
    cfs = data['new_rejected_counterfactuals']
    executed = sum(r['executed'] for r in cfs)
    collided = sum(r['collisions'] for r in cfs)
    unexecutable = sum(r['unexecutable'] for r in cfs)
    cf_line = f'只对本轮新生成且被拒的候选逐份干预：已执行 {executed} 份，其中 {collided} 份碰撞；{unexecutable} 份未完成干预，不当作安全结果。每份都保留原观测、移动前缀及全部 5 个轨迹数组的核验。复用 R1/R2 的旧拒绝候选不再重复计数。'
    substitute = ('修订想象没有在全部黑影测深可到达的场景中替代缺失深度。'
                  if aggregate['strict_arrived_among_see_dark_arrived'] < aggregate['see_dark_arrived_scenes']
                  else '这一对应关系仅在已完成的场景中成立。')
    return f"""## 赛后修订：想象只解释太阳的影子

**想象只解释太阳的影子；视线的影子，再看一眼。** `imagination_strict` 出现在看过 R2 结果之后，始终标为赛后修订，不替换原 `imagination` 或预注册主结果。

同一 5 cm 栅格，以已知地形、所有实际观测可见高度、通过自检的世界网格逐格最高点预测 0.05–5.00 m 的太阳阴影；方向取同一个渲染太阳函数。只有被解释的 DARK 可以通行，HIDDEN/UNSEEN 继续阻塞。补看和目标路线统一用这个占据定义，移动与最后转向都先在全部采纳世界完整预演。新方法最多 5 眼，第一眼的观测和真实任务逐字节复用。

### 已知冻结场景复测

这 12 场是看过原结果后的修订复测，**不是样本外证据**。{stats_line(data['frozen_stats'])}

{table(frozen)}

### 指定留出场景

只有这一表提供本轮样本外证据。固定取 F0_002、F2_011、F3_005，预算剩余依次 F0_003、F3_006；F1 没有未使用的决定性场景。每场四个当前源码基线和两种真实想象都保留，不按基线或 Lux 结果筛选。{stats_line(data['holdout_stats'])}

{table(held)}

### 修订结果与黑影测深对照

{conclusion}

see-dark 到达的 {aggregate['see_dark_arrived_scenes']} 场中，修订想象到达 {aggregate['strict_arrived_among_see_dark_arrived']} 场。眼数和仿真时间一起比较；停车导致的较短时间不当作速度收益。它检验的是能否在这些场景替代黑影里缺失的深度，不能写成对任意场景有效。

{substitute}

{comparison}

{cf_line}

本轮新增真实任务 **{data['paid_tasks']['new_r3']}**，R2 与 R3 累计 **{data['paid_tasks']['cumulative_r2_r3']}/360**，R3 上限 170。原输入、全部成功与失败任务、候选自检、预演和独立执行都有保留；每场唯一 SHA 清单在 `evidence/reviews/beforestep_r3/scenes/<scene>/manifest.json`，完整外包位置也写在清单中。视频指定三个修订运行的全部渲染数据均在公开仓库可取。

锚点在修订方法下：**{outcome(anchor['runs'].get('imagination_strict', {}))}**。视频仍使用 R1 原一眼到达运行。早期 v2 整合失败也保留：F1_003 去第 5 眼途中在 134.486s 接触 C，轨迹全部 5 个数组与原保守车相同；它是原观察路线的风险，不是一次新的模型生成失败。

原 R1/R2 数字、结果、冻结名单及证据保持原字节。完整六种运行、身份和复盘见 [R3 数据](../evidence/reviews/beforestep_r3/summary.json)，执行与失败判断见 [R3 执行记录](reviews/RESULT_BEFORESTEP_R3.md)。
"""


def main():
    data = json.loads((ROOT / 'evidence/reviews/beforestep_r3/summary.json').read_text())
    # Rebuild P0 from its protected R2 source before injecting R3, so reruns
    # cannot accidentally duplicate or replace the original result blocks.
    r3_presentation.main()
    text = chapter(data)
    report = ROOT / 'docs/report.md'
    report.write_text(report.read_text().replace('## 沙盒\n', '<!-- R3-METHOD-START -->\n' + text + '\n<!-- R3-METHOD-END -->\n\n## 沙盒\n', 1))
    r3_presentation.render_report(report.read_text())
    page = ROOT / 'site/index.html'
    rendered = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    rendered = rendered.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    rendered = rendered.replace('href="../evidence/', 'href="evidence/').replace('href="reviews/', 'href="docs/reviews/')
    section = '<section id="post-result-revision"><div class="eyebrow">POST-RESULT REVISION / SEPARATE EVIDENCE</div>' + rendered + '</section>'
    content = page.read_text().replace('<section id="sandbox"', section + '\n<section id="sandbox"', 1)
    if data['all_run_stats']['collisions']:
        names = html.escape('、'.join(data['all_run_stats']['collision_scenes']))
        notice = '<p id="r3-collision-warning" class="hero-result-line"><strong>赛后修订仍有碰撞：' + names + '。</strong> <a href="#post-result-revision">查看修订结果与原因 ↓</a></p>'
        content = content.replace('</section>', notice + '</section>', 1)
    page.write_text(content)
    (ROOT / 'docs/reviews/R3-method-tables.md').write_text(text)
    related = ROOT / 'docs/related-work.md'
    contribution = f"""<!-- R3-CONTRIBUTION-START -->
## 项目贡献：赛后修订与指定留出验证

R1/R2 预注册主结果保留。看过两次碰撞后增加 `imagination_strict`：只放行由已知太阳方向、地形、可见高度与准入候选解释的太阳阴影，视线遮挡与未见空间继续等待观察；补看和目标路线在全部准入世界预演，预算统一为最多 5 眼。规则、实现和阴影方向诊断见 [R3 执行记录](reviews/RESULT_BEFORESTEP_R3.md)。

已知 12 场复测：{stats_line(data['frozen_stats'])}这不是样本外证据。指定留出：{stats_line(data['holdout_stats'])}F1 已无未使用的决定性场景，固定留出顺序与失败都公开，不按结果选换。

在 see-dark 到达的 {data['all_run_stats']['see_dark_arrived_scenes']} 场中，修订想象到达 {data['all_run_stats']['strict_arrived_among_see_dark_arrived']} 场；眼数与仿真时间并列在 [修订五栏比较](reviews/R3-method-tables.md)。这些数据限定了想象替代缺失深度的实际范围，不能从避免碰撞推导成功通行，也没有证明生成分布覆盖真值或实机有效。

只有固定留出表支持本轮样本外判断；锚点视频与原一眼到达仍取 R1 原运行。所有新生成拒绝候选的反事实、任务来源、完整物理数据及原输入 SHA 都保留在 [分组原始数据](../evidence/reviews/beforestep_r3/summary.json)。
<!-- R3-CONTRIBUTION-END -->
"""
    original_related = re.sub(r'<!-- R3-CONTRIBUTION-START -->[\s\S]*?<!-- R3-CONTRIBUTION-END -->\n?', '', related.read_text())
    related.write_text(original_related.rstrip() + '\n\n' + contribution)
    print(json.dumps({'frozen_rows': len(data['frozen']), 'holdout_rows': len(data['holdouts']),
                      'revision_collisions': data['all_run_stats']['collision_scenes']}))


if __name__ == '__main__':
    main()
