"""Draw the four vector figures of report v4 with the report's own palette and fonts.

Values are copied from kept records (see SOURCES.md); nothing is fitted or estimated here.
lanes.svg is a schematic of one route, labelled as such; the three others are plain bar charts."""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets'
# v3 report palette: navy / cream / gold, teal = passed or arrived, red = failed, gold = stopped
INK, MUT, LINE, TINT, PAPER = '#172033', '#667085', '#e3e0d6', '#f5f2ea', '#ffffff'
GOOD, BAD, MID, DARK, ACC = '#1f9d8a', '#d9483b', '#e0a030', '#13213a', '#13213a'
SANS = "'Noto Sans CJK SC','Source Han Sans SC',sans-serif"
SERIF = "'Noto Serif CJK SC','Source Han Serif SC',serif"


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{SANS}">{body}</svg>')


def t(x, y, s, size=17, fill=INK, anchor='start', weight=400, family=None):
    fam = f' font-family="{family}"' if family else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{fam}>{s}</text>'


def lanes():
    W, H = 1000, 404
    x0, xr, xs, xg = 268, 500, 742, 934          # start, tall rocks, sill, goal
    b = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
    # landmark strip
    b += f'<rect x="{x0-18}" y="78" width="{xg-x0+52}" height="4" fill="{LINE}"/>'
    b += f'<path d="M{xr-52} 80 L{xr-44} 44 L{xr-22} 26 L{xr+6} 34 L{xr+16} 80 Z" fill="#8b93a3"/>'
    b += f'<path d="M{xr+22} 80 L{xr+30} 52 L{xr+52} 40 L{xr+70} 56 L{xr+76} 80 Z" fill="#aab1bf"/>'
    b += f'<rect x="{xs-26}" y="68" width="52" height="12" rx="3" fill="#8b93a3"/>'
    b += f'<ellipse cx="{xg}" cy="80" rx="22" ry="7" fill="none" stroke="{GOOD}" stroke-width="3"/>'
    b += f'<circle cx="{x0}" cy="74" r="6" fill="{INK}"/>'
    b += t(x0, 108, '起点', 17.5, MUT, 'middle')
    b += t(xr + 12, 108, '高石头 · 背面看不见', 17.5, INK, 'middle')
    b += t(xs + 8, 108, '门槛石 · 轮子滚不上', 17.5, INK, 'middle')
    b += t(xg + 18, 108, '终点', 17.5, MUT, 'middle')
    for x in (xr + 12, xs, xg):
        b += f'<line x1="{x}" y1="118" x2="{x}" y2="{H-14}" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="4 5"/>'
    rows = [(168, '只有轮子和相机', '把没看见的地方当空地', BAD),
            (262, '加上 Lux3D，只用轮子', '12 个模型世界先走一遍', MID),
            (356, 'Lux3D + 轮腿', '先想象、再预演、再抬腿', GOOD)]
    for y, a, s, c in rows:
        b += f'<rect x="0" y="{y-40}" width="236" height="76" rx="6" fill="{TINT}"/>'
        b += f'<rect x="0" y="{y-40}" width="6" height="76" fill="{c}"/>'
        b += t(20, y - 8, a, 20, INK, weight=700) + t(20, y + 19, s, 16.5, MUT)
        b += f'<circle cx="{x0}" cy="{y}" r="6" fill="{c}"/>'
    # lane 1: straight into the back of the tall rock
    y = rows[0][0]
    b += f'<path d="M{x0} {y} L{xr+4} {y}" stroke="{BAD}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    b += (f'<path d="M{xr-2} {y-11} L{xr+22} {y+11} M{xr+22} {y-11} L{xr-2} {y+11}" stroke="{BAD}" stroke-width="5" '
          'stroke-linecap="round"/>')
    b += t(xr + 40, y - 3, '56 秒', 23, BAD, weight=700, family=SERIF) + t(xr + 104, y - 3, '碰上高石头', 18, INK, weight=700)
    b += t(xr + 40, y + 21, '门槛石没能走到', 16.5, MUT)
    detour = lambda y: f'M{x0} {y} L{xr-74} {y} C{xr-40} {y} {xr-30} {y-30} {xr+12} {y-30} C{xr+54} {y-30} {xr+64} {y} {xr+98} {y}'
    # lane 2: round the rock, stuck at the sill
    y = rows[1][0]
    b += f'<path d="{detour(y)} L{xs-24} {y}" stroke="{MID}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    b += f'<rect x="{xs-24}" y="{y-12}" width="24" height="24" rx="3" fill="{MID}"/>'
    b += t(xr + 12, y + 28, '绕过去了', 16.5, MUT, 'middle')
    b += t(xs + 16, y - 3, '门前轮行 60 秒', 18.5, '#b86a0c', weight=700, family=SERIF)
    b += t(xs + 16, y + 21, '仍未过线（局部试验）', 16.5, MUT)
    # lane 3: round the rock, step over the sill, stop in the ring
    y = rows[2][0]
    b += (f'<path d="{detour(y)} L{xs-34} {y} C{xs-20} {y-34} {xs+20} {y-34} {xs+34} {y} L{xg-4} {y}" stroke="{GOOD}" '
          'stroke-width="5" fill="none" stroke-linecap="round"/>')
    b += f'<circle cx="{xg}" cy="{y}" r="15" fill="{GOOD}"/>'
    b += f'<path d="M{xg-7} {y} L{xg-2} {y+6} L{xg+8} {y-6}" stroke="#fff" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    b += t(xr + 12, y + 28, '绕过去了', 16.5, MUT, 'middle') + t(xs, y + 28, '12 个抬腿动作', 16.5, MUT, 'middle')
    b += t(xg - 26, y - 22, '174 秒 到达', 21, GOOD, 'end', 700, SERIF)
    (OUT / 'lanes.svg').write_text(svg(W, H, b), encoding='utf-8')


def iou():
    W, H = 470, 292
    vals = [0.4325, 0.8459, 0.2715, 0.7108, 0.63]; thr = 0.7068
    L, R, T, B = 46, 458, 26, 232
    y = lambda v: B - (B - T) * v
    b = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
    for v in (0, .2, .4, .6, .8, 1):
        b += f'<line x1="{L}" y1="{y(v)}" x2="{R}" y2="{y(v)}" stroke="{LINE}" stroke-width="1"/>' + t(L - 8, y(v) + 5, f'{v:.1f}', 13.5, MUT, 'end')
    step = (R - L) / 5
    for i, v in enumerate(vals):
        ok = v >= thr; c = GOOD if ok else BAD; cx = L + step * (i + .5)
        b += f'<rect x="{cx-27}" y="{y(v)}" width="54" height="{B-y(v)}" rx="2" fill="{c}"/>'
        b += t(cx, y(v) + 21, '通过' if ok else '丢弃', 15, '#fff', 'middle', 700)
        b += t(cx, B + 21, f'第 {i+1} 份', 14.5, INK, 'middle') + t(cx, B + 41, f'{v:.2f}', 14, MUT, 'middle')
    b += f'<line x1="{L}" y1="{y(thr)}" x2="{R}" y2="{y(thr)}" stroke="{INK}" stroke-width="1.6" stroke-dasharray="6 4"/>'
    b += f'<rect x="{L+2}" y="{y(thr)-25}" width="92" height="21" fill="{PAPER}"/>' + t(L + 6, y(thr) - 9, '及格线 0.71', 14, INK, 'start', 700)
    (OUT / 'chart-iou.svg').write_text(svg(W, H, b), encoding='utf-8')


def eight():
    W, H = 1000, 232
    rows = [('当它不存在（直接走）', [(8, BAD, '撞车 8')]),
            ('当它很危险（保守）', [(8, MID, '停车 8')]),
            ('让 Lux3D 想象再检验', [(3, GOOD, '到达 3'), (3, MID, '停车 3'), (2, BAD, '撞车 2')])]
    L, R = 262, 986; u = (R - L) / 8
    b = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
    for i, (name, segs) in enumerate(rows):
        yy = 14 + i * 64
        b += t(L - 16, yy + 30, name, 19, INK, 'end', 700 if i == 2 else 400)
        x = L
        for n, c, lab in segs:
            b += f'<rect x="{x+1.5}" y="{yy}" width="{n*u-3}" height="46" rx="3" fill="{c}"/>'
            b += t(x + n * u / 2, yy + 30, lab, 18.5, '#fff', 'middle', 700)
            x += n * u
    for k in range(9):
        b += f'<line x1="{L+k*u}" y1="204" x2="{L+k*u}" y2="210" stroke="{MUT}" stroke-width="1"/>'
        b += t(L + k * u, 227, str(k), 14, MUT, 'middle')
    b += t(L - 16, 227, '场景数（共 8 个难场景）', 14, MUT, 'end')
    (OUT / 'chart-eight.svg').write_text(svg(W, H, b), encoding='utf-8')


def gap():
    W, H = 560, 186
    rows = [('石头 B', 47.541, '4.8 厘米'), ('石头 A', 256.109, '25.6 厘米')]
    L, R = 82, 468; x = lambda v: L + (R - L) * v / 300
    b = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
    for v in (0, 100, 200, 300):
        b += f'<line x1="{x(v)}" y1="14" x2="{x(v)}" y2="128" stroke="{LINE}" stroke-width="1"/>' + t(x(v), 148, str(v), 13.5, MUT, 'middle')
    for i, (name, v, lab) in enumerate(rows):
        yy = 24 + i * 54; c = MID if i == 0 else ACC
        b += t(L - 12, yy + 24, name, 17, INK, 'end') + f'<rect x="{L}" y="{yy}" width="{x(v)-L}" height="36" rx="2" fill="{c}"/>'
        b += t(x(v) + 10, yy + 24, lab, 17, INK, weight=700)
    b += t(L, 174, '全程最小间隙（毫米）', 13.5, MUT)
    (OUT / 'chart-gap.svg').write_text(svg(W, H, b), encoding='utf-8')


for f in (lanes, iou, eight, gap):
    f()
print('charts written')
