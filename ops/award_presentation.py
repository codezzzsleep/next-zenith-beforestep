"""Add the award showcase to the existing, preserved R1/R2/R3 presentation."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    if (ROOT / 'evidence/web-assets/technical-transfer.json').exists():
        raise RuntimeError('The preserved award design is a technical report; homepage authoring now belongs to the project lead.')
    path = ROOT / 'site/index.html'
    page = path.read_text()
    if 'id="hero-real-image"' not in page:
        match = re.search(r'<section class="hero">([\s\S]*?)</section>', page)
        content = re.sub(r'<div class="orbit"[\s\S]*?</span></div>', '', match.group(1))
        content = content.replace('<a class="button" href="levels.html">开始第一关 →</a>',
            '<div class="hero-actions"><a class="button" href="levels.html">开始第一关 →</a><a href="#shadows">拖动两种影子 ↓</a><a class="award-language" href="en.html">English ↗</a></div>')
        hero = '<section class="hero"><div class="hero-copy">' + content + '</div>' + '''<figure class="hero-evidence"><div class="hero-shot" id="hero-real-image"><img src="media/award/first.png" alt="stress_v8 第一眼的真实机器人 RGB，A 与 B 标签来自原目标掩码" fetchpriority="high" width="1600" height="1200"><img class="dark-layer" src="media/award/dark-overlay.png" alt="原观测 DARK 像素标注"></div><figcaption>机器人实际第一眼 · A 在前，B 部分可见。琥珀色标出原 DARK 像素；A 后方的视线未知见下方原始地图。<a href="evidence/award/observations.json">原图、掩码与 SHA ↗</a></figcaption></figure></section>'''
        page = page[:match.start()] + hero + page[match.end():]
        shadow = re.search(r'<section id="shadows">([\s\S]*?)</section>', page)
        lead, old = shadow.group(1).split('</h2>', 1)
        interactive = '''<div class="award-shadow-grid"><article class="shadow-card"><h3>太阳的影子：移动相机，太阳不动。</h3><div class="shadow-photo"><img src="media/award/first.png" alt="固定首眼太阳黑影参考"><img src="media/award/dark-overlay.png" alt="真实首眼 DARK 像素"></div><p>这一栏固定保留首眼画面与它的实际 DARK 掩码作参考。换位置不会照亮太阳照不到的地方；DARK 分类本身也包含暗岩面，不能等同于纯几何阴影。</p></article><article class="shadow-card"><h3>视线的影子：再看一个真实位置。</h3><div class="shadow-photo"><img src="media/award/first.png" alt="第一眼真实观测"><img id="shadow-second" class="second-view" src="media/award/second.png" alt="保守车真实第二眼观测"></div><p id="shadow-view" aria-live="polite">读取真实观测…</p><p>两张照片来自两个实际观察姿态。滑块切换已记录画面，没有虚构中间视角；下方地图同步切换为该眼的原始分类。</p></article></div><div class="shadow-controls"><label for="shadow-range">第一眼 ↔ 第二眼</label><input id="shadow-range" type="range" min="0" max="100" value="0" aria-label="切换真实第一眼和第二眼"><button id="shadow-toggle">再看一眼 →</button></div><div class="shadow-map-wrap"><canvas id="shadow-map" width="840" height="270" aria-label="真实观测地图，随第一眼和第二眼切换"></canvas><div><div class="shadow-key"><span class="dark">■ 太阳黑影分类 DARK</span><span class="hidden">■ 视线遮挡 HIDDEN</span><span>■ 未观测</span></div><p id="shadow-map-caption"></p><a class="textlink" href="evidence/award/observations.json">核对原始观测 ↗</a></div></div>'''
        section = '<section id="shadows">' + lead + '</h2>' + interactive + '<details><summary>原始第一眼说明与完整对照图</summary>' + old + '</details></section>'
        page = page[:shadow.start()] + section + page[shadow.end():]
        choices = '''<section id="award-choices"><div class="eyebrow">PLAY / SAME OBSERVATION</div><h2>如果你是这台车，怎么走？</h2><p>先点一种策略，再看它的真实终态。四栏共享同一窄道、传感器与规则控制器；黑影测深是传感器对照。</p><div class="award-choice-grid">'''
        for key, title in [('conservative', '保守：先看清'), ('see_dark', '对照：黑影测深'),
                           ('optimistic', '乐观：直接走'), ('imagination', '真实 Lux：先想象')]:
            choices += f'<button class="award-choice" data-award-choice="{key}" aria-pressed="false"><h3>{title}</h3><canvas width="260" height="110" aria-label="{title}的实际轨迹缩略图"></canvas><p class="choice-outcome">点击揭晓终态 →</p></button>'
        choices += '</div><a class="button" href="levels.html">自己选一条路，再揭晓 →</a><a class="textlink" href="#experience">逐眼回放与全部原记录 ↓</a></section>'
        page = page.replace('</section>', '</section>' + choices, 1)
        levels = re.search(r'<section id="levels">[\s\S]*?</section>', page).group(0)
        page = page.replace(levels, '')
        page = page.replace('<section id="experience">', levels + '\n<section id="experience">', 1)
        page = page.replace('</head>', '<link rel="stylesheet" href="award.css"></head>', 1)
        page = page.replace('</body>', '<script type="module" src="award.js"></script></body>', 1)
        page = page.replace('<p id="candidate-info"', '<button id="award-model-rotate" type="button">转到背面 →</button><p id="candidate-info"', 1)
    # An explicit oldv2 notice is visible even before the final R3 chapter arrives.
    if 'id="r3-collision-warning"' not in page:
        notice = '<p id="r3-collision-warning" class="hero-result-line award-warning"><strong>赛后修订早期 oldv2：suite_r2_v4_F1_003 曾在第5眼途中碰撞。</strong>最终 v3 单独统计。<a href="docs/reviews/RESULT_BEFORESTEP_R3.md">原始记录 ↗</a></p>'
        page = page.replace('<div class="hero-actions">', notice + '<div class="hero-actions">', 1)
    if 'id="award-footer-warning"' not in page:
        footer = '<p id="award-footer-warning" class="award-warning">原 R2 想象在 F1_020、F3_004 碰撞；赛后修订早期 oldv2 在 F1_003 碰撞。最终 v3 的结论只限该版与已完成场景。</p><a href="en.html">English summary ↗</a>'
        if '</footer>' in page:
            page = page.replace('</footer>', footer + '</footer>', 1)
        else:
            page = page.replace('</main>', '<footer>' + footer + '</footer></main>', 1)
    path.write_text(page)
    print('Award hero, real-view interaction, four choices and local model controls installed.')


if __name__ == '__main__':
    main()
