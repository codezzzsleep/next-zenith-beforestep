#!/usr/bin/env python3
"""程序化插画：纯 SVG，跟随调色板，固定种子可复现，不需要任何外部图片。

    import art
    svg = art.make('ridges', 1000, 560, pal, seed=3)            # pal 来自 core.resolve_palette
    svg = art.make('contours', 800, 800, pal, bg='none')        # bg: cover | dark | paper | none | '#hex'

七种风格（选择见 references/choose.md）：
  ridges    层叠山脊 + 月/日 + 雾      自然、文旅、人文、生态
  contours  等高线地形                  研究、地理、规划、数据、严谨
  network   节点网络 + 高亮路径         AI、系统、基础设施、数据流
  waves     流动线带                    金融、音频、增长、AI 产品
  orbits    同心轨道 + 行星             科学、体系、平台、愿景
  blocks    包豪斯几何拼贴              设计、教育、品牌、产品
  halftone  半调网点渐变                编辑、社会议题、手作、复古印刷
命令行：python3 art.py --demo out_dir   生成七种风格 × 默认调色板的预览。
"""
import math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

_gid = [0]


def gid(p='g'):
    _gid[0] += 1
    return f'{p}{_gid[0]}'


def f1(x):
    return f'{x:.1f}'.rstrip('0').rstrip('.') if abs(x) < 1e5 else str(int(x))


# ───────────── 噪声 ─────────────
def _smooth(t):
    return t * t * (3 - 2 * t)


def fbm2(nx, ny, seed, scale=3.0, octaves=4, persist=.5):
    r = np.random.default_rng(seed)
    z, amp, tot = np.zeros((ny, nx)), 1.0, 0.0
    for o in range(octaves):
        gy = max(2, int(scale * 2 ** o))
        gx = max(2, int(gy * nx / ny))
        G = r.random((gy + 2, gx + 2))
        u = np.linspace(0, gx, nx, endpoint=False)
        v = np.linspace(0, gy, ny, endpoint=False)
        i, j = u.astype(int), v.astype(int)
        fu, fv = _smooth(u - i)[None, :], _smooth(v - j)[:, None]
        a = G[np.ix_(j, i)] * (1 - fu) + G[np.ix_(j, i + 1)] * fu
        b = G[np.ix_(j + 1, i)] * (1 - fu) + G[np.ix_(j + 1, i + 1)] * fu
        z += (a * (1 - fv) + b * fv) * amp
        tot += amp
        amp *= persist
    z /= tot
    return (z - z.min()) / (z.max() - z.min() + 1e-9)


def _fbm1(n, seed, scale=4.0, octaves=4, persist=.5):
    r = np.random.default_rng(seed)
    z, amp, tot = np.zeros(n), 1.0, 0.0
    for o in range(octaves):
        g = max(2, int(scale * 2 ** o))
        G = r.random(g + 2)
        u = np.linspace(0, g, n, endpoint=False)
        i = u.astype(int)
        f = _smooth(u - i)
        z += (G[i] * (1 - f) + G[i + 1] * f) * amp
        tot += amp
        amp *= persist
    z /= tot
    return (z - z.min()) / (z.max() - z.min() + 1e-9)


# ───────────── 背景与外壳 ─────────────
def _shell(W, H, body, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'width="100%" height="100%" style="display:block">' + (f'<defs>{defs}</defs>' if defs else '') + body + '</svg>')


def _bg(W, H, pal, bg):
    """返回 (背景 svg 片段, defs, dark?)。"""
    if bg == 'none':
        return '', '', pal['cover_mode'] == 'dark'
    if bg == 'cover':
        a, b, dark = pal['cover_bg'], pal['cover_bg2'], pal['cover_mode'] == 'dark'
    elif bg == 'dark':
        a, b, dark = pal['dark'], pal['dark2'], True
    elif bg == 'paper':
        a, b, dark = pal['paper'], pal['tint'], False
    else:
        a = b = bg
        dark = core.lum(bg) < .4
    g = gid('bg')
    return (f'<rect width="{W}" height="{H}" fill="url(#{g})"/>',
            f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>',
            dark)


def _poly(xs, ys, close_to=None):
    d = 'M' + ' L'.join(f'{f1(x)} {f1(y)}' for x, y in zip(xs, ys))
    if close_to is not None:
        d += f' L{f1(xs[-1])} {f1(close_to)} L{f1(xs[0])} {f1(close_to)}Z'
    return d


# ───────────── 1 ridges ─────────────
def ridges(W, H, pal, seed=1, bg='cover', peaks='rolling', layers=6, sun=True, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    out = [bgs]
    base_bg = pal['cover_bg'] if bg in ('cover', 'none') else (pal['dark'] if bg == 'dark' else pal['paper'])
    glow = A[0]
    if sun:
        sx, sy = W * r.uniform(.62, .84), H * r.uniform(.14, .26)
        gg = gid('gl')
        defs += f'<radialGradient id="{gg}"><stop offset="0" stop-color="{glow}" stop-opacity=".55"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>'
        out.append(f'<circle cx="{f1(sx)}" cy="{f1(sy)}" r="{f1(H * .3)}" fill="url(#{gg})"/>')
        out.append(f'<circle cx="{f1(sx)}" cy="{f1(sy)}" r="{f1(H * .045)}" fill="{"#ffffff" if dark else glow}" opacity="{.92 if dark else .85}"/>')
    n = 220
    xs = np.linspace(0, W, n)
    if dark:
        far, near = core.mix(base_bg, A[1], .42), core.mix(base_bg, '#000000', .55)
    else:
        far, near = core.mix(pal['paper'], A[1], .20), core.mix(A[1], pal['ink'], .42)
    for k in range(layers):
        t = k / max(1, layers - 1)
        col = core.mix(far, near, t ** .85)
        top = H * (.38 + .5 * t * .62) - H * .06
        amp = H * (.22 - .07 * t) * (1.1 if peaks == 'karst' else 1.0)
        if peaks == 'karst':
            y = np.zeros(n)
            for _ in range(int(5 + 3 * (1 - t))):
                c = r.uniform(-.05, 1.05) * W
                w = r.uniform(.035, .09) * W * (1.2 - .4 * t)
                h = r.uniform(.45, 1.0)
                y = np.maximum(y, h * np.exp(-(np.abs(xs - c) / w) ** 2.6))
            y = y * .93 + .07 * _fbm1(n, seed * 31 + k, 6, 3)
        else:
            y = _fbm1(n, seed * 17 + k * 5, 2.2 + k * .6, 4, .5)
        ys = top + (H * 1.0 - top) * .0 + (1 - y) * amp
        out.append(f'<path d="{_poly(xs, ys, H)}" fill="{col}"/>')
        if k < layers - 1:  # 雾
            mg = gid('mist')
            mc = '#ffffff' if dark else pal['paper']
            defs += (f'<linearGradient id="{mg}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{mc}" stop-opacity="0"/>'
                     f'<stop offset=".6" stop-color="{mc}" stop-opacity="{.15 if dark else .55}"/><stop offset="1" stop-color="{mc}" stop-opacity="0"/></linearGradient>')
            out.append(f'<rect x="0" y="{f1(top + amp * .35)}" width="{W}" height="{f1(amp * 1.1)}" fill="url(#{mg})"/>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 2 contours ─────────────
def _marching(z, level):
    """简易 marching squares，返回折线列表 [[(x,y),...]]（网格坐标）。端点按边缝合。"""
    ny, nx = z.shape
    segs = {}

    def pt(i, j, side):
        # side: 0 上边(i,j)-(i+1,j)  1 右边(i+1,j)-(i+1,j+1)  2 下边  3 左边
        if side == 0:
            a, b, ka, kb = z[j, i], z[j, i + 1], (i, j), (i + 1, j)
        elif side == 1:
            a, b, ka, kb = z[j, i + 1], z[j + 1, i + 1], (i + 1, j), (i + 1, j + 1)
        elif side == 2:
            a, b, ka, kb = z[j + 1, i], z[j + 1, i + 1], (i, j + 1), (i + 1, j + 1)
        else:
            a, b, ka, kb = z[j, i], z[j + 1, i], (i, j), (i, j + 1)
        t = (level - a) / (b - a + 1e-12)
        key = (min(ka, kb), max(ka, kb))
        return key, (ka[0] + (kb[0] - ka[0]) * t, ka[1] + (kb[1] - ka[1]) * t)

    table = {1: [(3, 2)], 2: [(2, 1)], 3: [(3, 1)], 4: [(0, 1)], 5: [(3, 0), (2, 1)], 6: [(0, 2)], 7: [(3, 0)],
             8: [(3, 0)], 9: [(0, 2)], 10: [(3, 2), (0, 1)], 11: [(0, 1)], 12: [(3, 1)], 13: [(2, 1)], 14: [(3, 2)]}
    adj, pos = {}, {}
    B = (z > level)
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = (int(B[j, i]) << 3) | (int(B[j, i + 1]) << 2) | (int(B[j + 1, i + 1]) << 1) | int(B[j + 1, i])
            if c in (0, 15):
                continue
            for s1, s2 in table[c]:
                k1, p1 = pt(i, j, s1)
                k2, p2 = pt(i, j, s2)
                pos[k1], pos[k2] = p1, p2
                adj.setdefault(k1, []).append(k2)
                adj.setdefault(k2, []).append(k1)
    seen, lines = set(), []
    starts = [k for k, v in adj.items() if len(v) == 1] + list(adj)
    for s in starts:
        if s in seen:
            continue
        line, cur, prev = [s], s, None
        seen.add(s)
        while True:
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            line.append(cur)
        lines.append([pos[k] for k in line])
    return lines


def contours(W, H, pal, seed=1, bg='cover', levels=16, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    nx = 84
    ny = max(30, int(nx * H / W))
    z = fbm2(nx, ny, seed, 2.4, 4, .52)
    # 加一个偏心的山丘，让中心构图更明确
    yy, xx = np.mgrid[0:ny, 0:nx]
    cx, cy = nx * np.random.default_rng(seed).uniform(.55, .8), ny * np.random.default_rng(seed + 1).uniform(.3, .55)
    z = z * .72 + .6 * np.exp(-(((xx - cx) / (nx * .33)) ** 2 + ((yy - cy) / (ny * .4)) ** 2))
    z = (z - z.min()) / (z.max() - z.min())
    out = [bgs]
    sx, sy = W / (nx - 1), H / (ny - 1)
    for k in range(levels):
        lv = .08 + .86 * k / (levels - 1)
        idx = (k % 5 == 0)
        col = A[0] if idx else (A[1] if k % 2 else A[2])
        op = (.95 if idx else .55) * (.55 + .45 * lv)
        paths = []
        for ln in _marching(z, lv):
            if len(ln) < 4:
                continue
            pts = ln[::2] + ([ln[-1]] if len(ln) % 2 == 0 else [])
            paths.append('M' + ' L'.join(f'{f1(x * sx)} {f1(y * sy)}' for x, y in pts))
        if paths:
            out.append(f'<path d="{" ".join(paths)}" fill="none" stroke="{col}" stroke-width="{2.2 if idx else 1.1}" stroke-opacity="{op:.2f}" stroke-linejoin="round" stroke-linecap="round"/>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 3 network ─────────────
def network(W, H, pal, seed=1, bg='cover', n=62, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    cols, rows = int(math.sqrt(n * W / H)) + 1, int(math.sqrt(n * H / W)) + 1
    pts = []
    for i in range(cols):
        for j in range(rows):
            pts.append(((i + .5 + r.uniform(-.38, .38)) * W / cols, (j + .5 + r.uniform(-.38, .38)) * H / rows))
    P = np.array(pts)
    out = [bgs]
    base = '#ffffff' if dark else pal['ink']
    # 背景点阵
    step = W / 24
    dots = ''.join(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="1.3"/>' for x in np.arange(step / 2, W, step) for y in np.arange(step / 2, H, step))
    out.append(f'<g fill="{base}" fill-opacity=".10">{dots}</g>')
    d = np.linalg.norm(P[:, None] - P[None], axis=2)
    edges = set()
    for i in range(len(P)):
        for j in np.argsort(d[i])[1:4]:
            edges.add((min(i, int(j)), max(i, int(j))))
    hubs = set(r.choice(len(P), size=max(4, len(P) // 9), replace=False).tolist())
    # 高亮路径：从一个中心附近的 hub 走几跳
    path = [int(np.argmin(np.linalg.norm(P - [W * .25, H * .7], axis=1)))]
    for _k in range(6):
        cur = path[-1]
        cand = [j for j in np.argsort(d[cur])[1:5] if int(j) not in path and P[j][0] > P[cur][0] - W * .02]
        if not cand:
            break
        path.append(int(cand[0]))
    pe = {(min(a, b), max(a, b)) for a, b in zip(path, path[1:])}
    lines = ''.join(f'<line x1="{f1(P[a][0])}" y1="{f1(P[a][1])}" x2="{f1(P[b][0])}" y2="{f1(P[b][1])}"/>' for a, b in edges if (a, b) not in pe)
    out.append(f'<g stroke="{base}" stroke-opacity=".22" stroke-width="1.2">{lines}</g>')
    out.append(f'<g stroke="{A[0]}" stroke-width="3.4" stroke-linecap="round" stroke-opacity=".95">' + ''.join(
        f'<line x1="{f1(P[a][0])}" y1="{f1(P[a][1])}" x2="{f1(P[b][0])}" y2="{f1(P[b][1])}"/>' for a, b in pe) + '</g>')
    for i, (x, y) in enumerate(P):
        if i in path:
            gg = gid('gl')
            defs += f'<radialGradient id="{gg}"><stop offset="0" stop-color="{A[0]}" stop-opacity=".5"/><stop offset="1" stop-color="{A[0]}" stop-opacity="0"/></radialGradient>'
            out.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="26" fill="url(#{gg})"/><circle cx="{f1(x)}" cy="{f1(y)}" r="6.5" fill="{A[0]}"/>')
        elif i in hubs:
            out.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="9" fill="none" stroke="{A[1]}" stroke-width="1.6" stroke-opacity=".8"/><circle cx="{f1(x)}" cy="{f1(y)}" r="4" fill="{A[1]}"/>')
        else:
            out.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="2.8" fill="{base}" fill-opacity=".55"/>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 4 waves ─────────────
def waves(W, H, pal, seed=1, bg='cover', lines=34, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    out = [bgs]
    n = 160
    xs = np.linspace(-W * .05, W * 1.05, n)
    k1, k2 = r.uniform(1.4, 2.4), r.uniform(3.2, 5.0)
    ph = r.uniform(0, 6.28, 3)
    env = .35 + .65 * _fbm1(n, seed, 2.0, 2)
    gg = gid('wg')
    defs += f'<linearGradient id="{gg}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{A[1]}"/><stop offset=".55" stop-color="{A[0]}"/><stop offset="1" stop-color="{A[2] if dark else A[1]}"/></linearGradient>'
    cy = H * r.uniform(.42, .58)
    for i in range(lines):
        t = i / (lines - 1)
        shift = (t - .5)
        y = cy + shift * H * .55 + env * H * .13 * np.sin(k1 * xs / W * 6.28 + ph[0] + t * 3.2) \
            + H * .045 * np.sin(k2 * xs / W * 6.28 + ph[1] - t * 5.4) * (1 - abs(shift))
        op = .18 + .72 * (1 - abs(shift) * 1.6) if abs(shift) < .62 else .12
        out.append(f'<path d="{_poly(xs, y)}" fill="none" stroke="url(#{gg})" stroke-width="{1.0 + 1.3 * (1 - abs(shift) * 2):.2f}" stroke-opacity="{max(.1, op):.2f}" stroke-linecap="round"/>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 5 orbits ─────────────
def orbits(W, H, pal, seed=1, bg='cover', rings=9, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    out = [bgs]
    cx, cy = W * r.uniform(.62, .8), H * r.uniform(.3, .55)
    base = '#ffffff' if dark else pal['ink']
    R0 = min(W, H) * .09
    gg = gid('gl')
    defs += f'<radialGradient id="{gg}"><stop offset="0" stop-color="{A[0]}" stop-opacity=".6"/><stop offset="1" stop-color="{A[0]}" stop-opacity="0"/></radialGradient>'
    out.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(R0 * 3.2)}" fill="url(#{gg})"/>')
    out.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(R0)}" fill="{A[0]}"/>')
    for i in range(1, rings + 1):
        R = R0 * (1.6 + i * 1.18)
        dash = ' stroke-dasharray="2 7"' if i % 3 == 0 else ''
        out.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(R)}" fill="none" stroke="{base}" stroke-opacity="{.30 - i * .018:.2f}" stroke-width="{1.4 if i % 4 else 2.2}"{dash}/>')
        if i in (2, 4, 5, 7, 8):
            a = r.uniform(0, 6.28)
            px, py = cx + R * math.cos(a), cy + R * math.sin(a)
            col = A[1] if i % 2 else A[2] if not dark else A[1]
            out.append(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="{f1(R0 * (.22 + .05 * (i % 3)))}" fill="{col}"/>')
            if i == 5:
                out.append(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="{f1(R0 * .5)}" fill="none" stroke="{col}" stroke-width="1.6" stroke-opacity=".7"/>')
    # 刻度
    Rt = R0 * (1.6 + rings * 1.18) + 16
    ticks = ''.join(f'<line x1="{f1(cx + Rt * math.cos(a))}" y1="{f1(cy + Rt * math.sin(a))}" x2="{f1(cx + (Rt + (12 if k % 6 == 0 else 6)) * math.cos(a))}" y2="{f1(cy + (Rt + (12 if k % 6 == 0 else 6)) * math.sin(a))}"/>'
                    for k, a in enumerate(np.linspace(0, 6.2832, 72, endpoint=False)))
    out.append(f'<g stroke="{base}" stroke-opacity=".28" stroke-width="1.2">{ticks}</g>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 6 blocks ─────────────
def blocks(W, H, pal, seed=1, bg='cover', cols=6, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    cell = W / cols
    rows = int(math.ceil(H / cell))
    pool = [A[0], A[1], A[2], pal['paper'] if not dark else pal['dark3'], pal['ink'] if not dark else '#ffffff']
    out = [bgs]
    for j in range(rows):
        for i in range(cols):
            x, y, s = i * cell, j * cell, cell
            if r.random() < .22:
                continue
            c = pool[int(r.integers(0, len(pool)))]
            k = int(r.integers(0, 7))
            o = .92
            if k == 0:   # 四分之一圆
                q = int(r.integers(0, 4))
                cxq, cyq = x + (s if q in (1, 2) else 0), y + (s if q in (2, 3) else 0)
                a0 = [0, 90, 180, 270][q]
                x1, y1 = cxq + s * math.cos(math.radians(a0)), cyq + s * math.sin(math.radians(a0))
                x2, y2 = cxq + s * math.cos(math.radians(a0 + 90)), cyq + s * math.sin(math.radians(a0 + 90))
                # 以角点为圆心的四分之一扇形
                sx = 1 if q in (0, 3) else -1
                sy = 1 if q in (0, 1) else -1
                out.append(f'<path d="M{f1(cxq)} {f1(cyq)} L{f1(cxq + sx * s)} {f1(cyq)} A{f1(s)} {f1(s)} 0 0 {1 if sx * sy > 0 else 0} {f1(cxq)} {f1(cyq + sy * s)}Z" fill="{c}" opacity="{o}"/>')
            elif k == 1:  # 圆
                out.append(f'<circle cx="{f1(x + s / 2)}" cy="{f1(y + s / 2)}" r="{f1(s * .42)}" fill="{c}" opacity="{o}"/>')
            elif k == 2:  # 半圆
                if r.random() < .5:
                    out.append(f'<path d="M{f1(x)} {f1(y + s)} A{f1(s / 2)} {f1(s / 2)} 0 0 1 {f1(x + s)} {f1(y + s)}Z" fill="{c}" opacity="{o}"/>')
                else:
                    out.append(f'<path d="M{f1(x)} {f1(y)} A{f1(s / 2)} {f1(s / 2)} 0 0 0 {f1(x + s)} {f1(y)}Z" fill="{c}" opacity="{o}"/>')
            elif k == 3:  # 方块
                out.append(f'<rect x="{f1(x + s * .1)}" y="{f1(y + s * .1)}" width="{f1(s * .8)}" height="{f1(s * .8)}" fill="{c}" opacity="{o}"/>')
            elif k == 4:  # 三角
                if r.random() < .5:
                    out.append(f'<path d="M{f1(x)} {f1(y)} L{f1(x + s)} {f1(y + s)} L{f1(x)} {f1(y + s)}Z" fill="{c}" opacity="{o}"/>')
                else:
                    out.append(f'<path d="M{f1(x + s)} {f1(y)} L{f1(x + s)} {f1(y + s)} L{f1(x)} {f1(y + s)}Z" fill="{c}" opacity="{o}"/>')
            elif k == 5:  # 同心圆环
                out.append(f'<circle cx="{f1(x + s / 2)}" cy="{f1(y + s / 2)}" r="{f1(s * .4)}" fill="none" stroke="{c}" stroke-width="{f1(s * .12)}" opacity="{o}"/>')
            else:         # 竖条纹
                for t in range(4):
                    out.append(f'<rect x="{f1(x + s * (.08 + t * .24))}" y="{f1(y + s * .1)}" width="{f1(s * .13)}" height="{f1(s * .8)}" fill="{c}" opacity="{o}"/>')
    return _shell(W, H, ''.join(out), defs)


# ───────────── 7 halftone ─────────────
def halftone(W, H, pal, seed=1, bg='cover', pitch=None, **_):
    bgs, defs, dark = _bg(W, H, pal, bg)
    A = pal['art']
    r = np.random.default_rng(seed)
    out = [bgs]
    pitch = pitch or W / 34
    fld = fbm2(90, max(30, int(90 * H / W)), seed, 1.8, 3)
    ny, nx = fld.shape
    cx, cy = W * r.uniform(.15, .85), H * r.uniform(.1, .55)
    maxd = math.hypot(W, H) * .75
    col = A[0]
    col2 = A[1]
    items = []
    row = 0
    y = pitch / 2
    while y < H + pitch:
        x = pitch / 2 + (pitch / 2 if row % 2 else 0)
        while x < W + pitch:
            d = math.hypot(x - cx, y - cy) / maxd
            v = max(0.0, 1 - d) ** 1.4 * .7 + .55 * fld[min(ny - 1, int(y / H * (ny - 1))), min(nx - 1, int(x / W * (nx - 1)))] * max(0, 1 - d) ** .5
            rad = pitch * .52 * min(1.0, max(0.0, v - .12) * 1.45)
            if rad > .7:
                items.append((x, y, rad, d))
            x += pitch
        y += pitch * .866
        row += 1
    NB = 6
    for b in range(NB):
        grp = ''.join(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="{f1(rad)}"/>' for x, y, rad, d in items
                      if min(NB - 1, int(max(0, d - .1) / .6 * NB)) == b)
        out.append(f'<g fill="{core.mix(col, col2, b / (NB - 1))}">{grp}</g>')
    return _shell(W, H, ''.join(out), defs)


KINDS = {'ridges': ridges, 'contours': contours, 'network': network, 'waves': waves, 'orbits': orbits,
         'blocks': blocks, 'halftone': halftone}


def make(kind, W, H, pal, seed=1, bg='cover', **opts):
    """生成一张插画（SVG 字符串）。W/H 只决定宽高比和内部坐标，插入页面时由容器尺寸决定实际大小。"""
    if kind not in KINDS:
        raise ValueError(f'未知插画 {kind}，可选：{", ".join(KINDS)}')
    return KINDS[kind](int(W), int(H), pal, seed=seed, bg=bg, **opts)


def mini(kind, pal, seed=1, bg='dark'):
    return make(kind, 400, 400, pal, seed, bg)


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--demo':
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        pal = core.resolve_palette(sys.argv[3] if len(sys.argv) > 3 else 'midnight')
        for k in KINDS:
            open(os.path.join(out, f'art_{k}.svg'), 'w', encoding='utf-8').write(make(k, 1000, 640, pal, 3))
        print('demo art →', out)
