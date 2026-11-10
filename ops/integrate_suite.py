"""Integrate only completed suite results; keep the full R1 eight-part narrative."""
import argparse
import html
import json
from pathlib import Path
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]


def replace_block(text, start, end, block, before):
    framed = start + '\n' + block + '\n' + end + '\n'
    if start in text:
        return re.sub(re.escape(start)+r'[\s\S]*?'+re.escape(end)+r'\n?', lambda _: framed, text)
    assert before in text
    return text.replace(before, framed+before, 1)


def related_work_block(summary):
    d, cf = summary['decisive'], summary['counterfactuals']
    lines = ['## 项目贡献：预注册场景组的实测范围', '',
        f"R2原冻结{summary['frozen_scene_count']}个场景，完整完成{summary['completed_scene_count']}个；决定性场景中想象到达{d['arrived']}、安全终止{d['safe_stop']}、碰撞{d['collisions']}。",
        '全部分类与选择在本轮真实Lux结果之前完成，随后使用同一冻结流程、规则控制器与准入门槛；没有逐场景调参或训练新模型。逐场五种运行、任务身份、复盘与反事实见[场景组实测](suite.md)和[原始总表](../evidence/suite/summary.json)。', '']
    if summary['imagination_collision_scenes']:
        lines.append('想象执行发生碰撞：' + '、'.join(summary['imagination_collision_scenes']) + '。这些失败限定了该流程的安全适用范围，不能以候选通过自检或预演代替实际安全。')
    lines.append('满足预注册的多数决定性场景有效且无碰撞条件。' if summary['majority_effectiveness_supported']
                 else '没有满足预注册的多数决定性场景有效且无碰撞条件；贡献限于可复核的系统与逐类实测边界。')
    lines.append(f"全部可执行拒绝候选反事实中碰撞{cf['collisions']}/{cf['executed']}，另{cf['unexecutable']}份不能执行。" +
                 ('自检确实拒绝过会导致碰撞的候选，具体比例和运行身份公开。' if summary['selfcheck_collision_evidence']
                  else '该批没有证明自检挡住碰撞，仍报告自检偏保守。'))
    lines.append('真实第二眼场景：' + ('、'.join(summary['second_eye_scenes']) or '无') + '；真实6b追加场景：' +
                 ('、'.join(summary['six_b_scenes']) or '无') + '。')
    lines.extend(['', '这是有限扫描岩石、低太阳角与预注册摆放分布下的受控仿真实验。它没有比较多候选与单候选，也没有测量生成分布的覆盖率或证明任意月面的有效性；不继承上述论文的实体实验结论。', ''])
    return '\n'.join(lines).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sandbox', action='store_true', help='Include only after full browser and consistency checks')
    args = parser.parse_args()
    summary = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    levels = json.loads((ROOT / 'site/data/levels.json').read_text())
    assert not levels['anchor_only_development'] and len(levels['levels']) == summary['completed_scene_count']
    suite = (ROOT / 'docs/suite.md').read_text().strip()
    report_path = ROOT / 'docs/report.md'
    report = replace_block(report_path.read_text(), '<!-- SUITE-START -->', '<!-- SUITE-END -->', suite,
                           '## 两种影子，一个行动问题')
    report = re.sub(r'^Next Zenith · 负责人 R1 主线复核[^\n]+$',
        'Next Zenith · Aholo Lux3D。报告保留R1原窄道锚点与R2预注册场景组；R1主实验源码 `2147b2f`，R2源码身份逐场保存在原运行记录。完整结果见[R1执行记录](reviews/RESULT_BEFORESTEP_R1.md)与[R2执行记录](reviews/RESULT_BEFORESTEP_R2.md)。',
        report, flags=re.M)
    report_path.write_text(report)
    related = ROOT / 'docs/related-work.md'
    related.write_text(replace_block(related.read_text(), '<!-- SUITE-CONTRIBUTION-START -->',
        '<!-- SUITE-CONTRIBUTION-END -->', related_work_block(summary),
        '## 项目贡献：冻结窄道里的行动实证'))
    homepage_path = ROOT / 'site/index.html'
    page = homepage_path.read_text()
    page = page.replace('<a class="button" href="#experience">查看窄道里的三种选择 ↓</a>',
                        '<a class="button" href="levels.html">开始第一关 →</a>')
    game = '<section id="levels"><div class="eyebrow">PLAY / CHOOSE YOUR ROUTE</div><h2>先做选择，再揭晓。</h2><p>看机器人实际第一眼，选择直接走、多看几眼或想一想，再回放实际轨迹、翻看背面并记分。</p><a class="button" href="levels.html">进入完整关卡 →</a><iframe title="真实月面实验关卡" src="levels.html?embedded=1" loading="lazy" style="width:100%;height:1600px;border:0;margin-top:2rem"></iframe></section>'
    warning = ('<p class="suite-warning"><strong>想象策略实际发生碰撞：'+html.escape('、'.join(summary['imagination_collision_scenes']))+'。</strong>全部失败与复盘原因在总表公开。</p>') if summary['imagination_collision_scenes'] else ''
    table = markdown.markdown(suite, extensions=['tables', 'fenced_code']).replace('<h1>', '<h2>').replace('</h1>', '</h2>')
    # The Markdown paths are relative to docs/, while this is the site root.
    table = re.sub(r'href="\.\./([^\"]+)"', r'href="\1"', table)
    table = table.replace('href="decisions.md"', 'href="docs/decisions.md"').replace('href="reviews/RESULT_BEFORESTEP_R2.md"', 'href="docs/reviews/RESULT_BEFORESTEP_R2.md"')
    block = game+'\n<section id="suite-summary">'+warning+'<div class="table-wrap">'+table+'</div></section>'
    page = replace_block(page, '<!-- SUITE-HOME-START -->', '<!-- SUITE-HOME-END -->', block, '<section id="shadows">')
    resize = '<script>addEventListener("message",function(e){if(e.origin!==location.origin||!Number.isFinite(e.data?.beforestepLevelHeight))return;var f=document.querySelector("#levels iframe");if(f&&e.source===f.contentWindow)f.style.height=Math.max(700,e.data.beforestepLevelHeight)+"px";});</script>'
    if 'beforestepLevelHeight' not in page:
        page = page.replace('</body>', resize+'</body>')
    if args.sandbox:
        browser = json.loads((ROOT / 'evidence/suite/presentation/sandbox/browser.json').read_text())
        consistency = json.loads((ROOT / 'evidence/suite/presentation/sandbox/consistency.json').read_text())
        assert browser['passed'] and not consistency['development_anchor_only']
        assert consistency['scene_count'] == summary['completed_scene_count']
        sandbox = '<section id="sandbox"><div class="eyebrow">SANDBOX / YOUR MOONSCAPE</div><h2>石头，由你来放。</h2><p>拖动扫描岩石，旋转、调整太阳与月坑，查看三种策略的轻量路线，再导出到本地完整物理验证。</p><a class="button" href="sandbox.html">打开月面沙盒 →</a><p class="caption">不做物理仿真，不实时调用 Lux3D。一致性 '+str(consistency['consistent_scenes'])+'/'+str(consistency['scene_count'])+'；所有不一致在<a href="evidence/suite/presentation/sandbox/consistency.json">原始检查</a>中列出。</p></section>'
        page = replace_block(page, '<!-- SANDBOX-HOME-START -->', '<!-- SANDBOX-HOME-END -->', sandbox, '<section id="evolution">')
    homepage_path.write_text(page)
    report_html = markdown.markdown(report, extensions=['tables', 'fenced_code'])
    def document_link(match):
        attribute, url = match.groups()
        if url.startswith(('https:', 'http:', '#')):
            return match.group(0)
        path = (ROOT / 'docs' / url).resolve()
        if path.is_dir():
            return attribute+'="https://github.com/codezzzsleep/next-zenith-beforestep/tree/main/'+str(path.relative_to(ROOT))+'"'
        if path == ROOT / 'README.md':
            return attribute+'="https://github.com/codezzzsleep/next-zenith-beforestep"'
        if path.is_relative_to(ROOT / 'site'):
            relative = path.relative_to(ROOT / 'site')
        else:
            relative = path.relative_to(ROOT)
        return attribute+'="'+str(relative)+'"'
    report_html = re.sub(r'(href|src)="([^\"]+)"', document_link, report_html)
    old_html = (ROOT / 'site/report.html').read_text()
    style = re.search(r'<style>[\s\S]*?</style>', old_html).group(0)
    (ROOT / 'site/report.html').write_text('<!doctype html><html lang="zh-CN"><head><link rel="icon" href="favicon.svg"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>先见一步 · 报告</title>'+style+'</head><body>'+report_html+'</body></html>')
    print(json.dumps({'scenes': summary['completed_scene_count'], 'sandbox': args.sandbox}))


if __name__ == '__main__':
    main()
