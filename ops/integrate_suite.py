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
    report_path.write_text(report)
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
