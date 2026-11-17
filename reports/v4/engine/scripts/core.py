#!/usr/bin/env python3
"""核心工具：颜色推导、调色板解析、风格旋钮、内联标记、文字宽度估算、组件注册表。

这个文件是「设计语言」在代码里的落点：
  - palettes.json 只写基础色，这里推导出全部 token 并保证对比度；
  - KNOBS 是风格旋钮的唯一定义，文档和校验都从这里取；
  - REG 是组件注册表，catalog.py / gallery.py 都从它自动生成，文档不会和代码脱节。
"""
import json, os, re, html, math, base64, mimetypes
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, 'design')

# ───────────────────────── 风格旋钮（唯一定义） ─────────────────────────
KNOBS = {
    'cover':    ['horizon', 'poster', 'type', 'split', 'numbers', 'frame', 'mosaic'],
    'header':   ['kicker', 'numeral', 'band', 'rail', 'split', 'minimal'],
    'art':      ['ridges', 'contours', 'network', 'waves', 'orbits', 'blocks', 'halftone'],
    'radius':   ['sharp', 'soft', 'round'],
    'card':     ['tint', 'outline', 'flat', 'edge'],
    'fontpair': ['serif-sans', 'sans-sans', 'serif-serif', 'mono-accent'],
    'density':  ['compact', 'regular', 'airy'],
    'footer':   ['rule', 'minimal', 'index', 'none'],
}
DEFAULT_STYLE = {'preset': None, 'palette': 'midnight', 'cover': 'horizon', 'header': 'kicker', 'art': 'ridges',
                 'radius': 'soft', 'card': 'tint', 'fontpair': 'serif-sans', 'density': 'regular', 'footer': 'rule'}


def _load(name):
    with open(os.path.join(DESIGN, name), encoding='utf-8') as f:
        return json.load(f)


def palettes():
    return _load('palettes.json')['palettes']


def presets():
    return _load('presets.json')['presets']


def resolve_style(style):
    """preset → 基础默认 → 用户显式值（后者覆盖前者）。返回完整旋钮 dict，并校验取值。"""
    style = dict(style or {})
    unknown = set(style) - set(DEFAULT_STYLE)
    if unknown:
        raise ValueError(f'未知风格旋钮：{sorted(unknown)}')
    out = dict(DEFAULT_STYLE)
    pre = style.get('preset')
    if pre:
        P = presets()
        if pre not in P:
            raise ValueError(f'未知 preset：{pre}。可选：{", ".join(P)}')
        out.update({k: v for k, v in P[pre].items() if k != 'why'})
    out.update({k: v for k, v in style.items() if v is not None})
    for k, allowed in KNOBS.items():
        if out.get(k) not in allowed:
            raise ValueError(f'style.{k} = {out.get(k)!r} 不合法。可选：{", ".join(allowed)}')
    if isinstance(out['palette'], str) and out['palette'] not in palettes():
        raise ValueError(f'未知 palette：{out["palette"]}。可选：{", ".join(palettes())}')
    return out


# ───────────────────────── 颜色 ─────────────────────────
def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(r, g, b):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))


def mix(a, b, t):
    """a 和 b 按 t 混合（t=0 全是 a，t=1 全是 b）。"""
    ra, rb = hex2rgb(a), hex2rgb(b)
    return rgb2hex(*[ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def lum(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex2rgb(h)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def ensure_contrast(fg, bg, ratio=4.5, toward=None):
    """把 fg 往 toward（默认：bg 亮则往黑，bg 暗则往白）推，直到和 bg 的对比度 ≥ ratio。"""
    if contrast(fg, bg) >= ratio:
        return fg
    toward = toward or ('#000000' if lum(bg) > 0.4 else '#ffffff')
    for i in range(1, 21):
        c = mix(fg, toward, i / 20)
        if contrast(c, bg) >= ratio:
            return c
    return toward


def on_color(bg, light='#ffffff', dark='#111111'):
    return light if contrast(light, bg) >= contrast(dark, bg) else dark


def resolve_palette(p):
    """基础色 → 完整 token。p 可以是名称或 dict（自定义调色板同样走这里）。"""
    if isinstance(p, str):
        p = palettes()[p]
    t = dict(p)
    paper, ink = t['paper'], t['ink']
    t['ink'] = ink = ensure_contrast(ink, paper)
    t['mut'] = ensure_contrast(t['mut'], paper)
    t['paper2'] = mix(paper, ink, .035)
    t['ink2'] = ensure_contrast(mix(ink, paper, .28), paper)
    t['mut2'] = mix(t['mut'], paper, .5)
    t['line2'] = mix(t['line'], ink, .12)
    t['tint2'] = mix(t['tint'], ink, .045)
    t['accent_ink'] = ensure_contrast(t['accent'], paper, 4.5)
    t['accent_soft'] = mix(t['accent'], paper, .88)
    t['accent2_ink'] = ensure_contrast(t['accent2'], paper, 4.5)
    t['accent2_soft'] = mix(t['accent2'], paper, .88)
    t['on_accent'] = on_color(t['accent'])
    t['on_accent2'] = on_color(t['accent2'])
    for k in ('good', 'bad', 'mid'):
        t[k + '_ink'] = ensure_contrast(t[k], paper, 4.5)
        t[k + '_soft'] = mix(t[k], paper, .88)
        t['on_' + k] = on_color(t[k])
    d = t['dark']
    t['dark2'] = mix(d, '#ffffff', .07)
    t['dark3'] = mix(d, '#ffffff', .13)
    t['dark_line'] = mix(d, '#ffffff', .18)
    t['dark_mut'] = mix('#ffffff', d, .38)
    t['on_dark'] = '#ffffff'
    t['accent_on_dark'] = ensure_contrast(t['accent'], d, 4.5, toward='#ffffff')
    c = t['cover']
    t['cover_mode'] = c.get('mode', 'dark')
    t['cover_bg'], t['cover_bg2'] = c['bg'][0], c['bg'][-1]
    if t['cover_mode'] == 'dark':
        t['cover_fg'] = '#ffffff'
        t['cover_mut'] = mix('#ffffff', t['cover_bg'], .42)
        t['cover_line'] = mix(t['cover_bg2'], '#ffffff', .22)
        t['cover_card'] = mix(t['cover_bg2'], '#ffffff', .06)
    else:
        t['cover_fg'] = ink
        t['cover_mut'] = mix(ink, t['cover_bg'], .45)
        t['cover_line'] = mix(t['cover_bg2'], ink, .18)
        t['cover_card'] = mix(t['cover_bg'], '#ffffff', .55)
    t['cover_mut'] = ensure_contrast(t['cover_mut'], t['cover_bg'])
    t['cover_accent'] = ensure_contrast(c.get('accent', t['accent']), t['cover_bg'], 4.5,
                                        toward=('#ffffff' if t['cover_mode'] == 'dark' else '#000000'))
    t['cover_accent_ink'] = ensure_contrast(c.get('accent', t['accent']), t['cover_bg'], 4.5)
    t['on_cover_accent'] = on_color(t['cover_accent'])
    t.setdefault('series', [t['accent'], t['accent2'], t['good'], t['bad'], t['mut'], t['mid']])
    t.setdefault('art', [t['accent'], t['accent2'], t['dark']])
    return t


def css_vars(t):
    keys = ['paper', 'paper2', 'ink', 'ink2', 'mut', 'mut2', 'line', 'line2', 'tint', 'tint2',
            'accent', 'accent_ink', 'accent_soft', 'on_accent', 'accent2', 'accent2_ink', 'accent2_soft', 'on_accent2',
            'good', 'good_ink', 'good_soft', 'on_good', 'bad', 'bad_ink', 'bad_soft', 'on_bad',
            'mid', 'mid_ink', 'mid_soft', 'on_mid',
            'dark', 'dark2', 'dark3', 'dark_line', 'dark_mut', 'on_dark', 'accent_on_dark',
            'cover_bg', 'cover_bg2', 'cover_fg', 'cover_mut', 'cover_line', 'cover_card', 'cover_accent',
            'cover_accent_ink', 'on_cover_accent']
    s = ':root{' + ''.join(f'--{k.replace("_", "-")}:{t[k]};' for k in keys)
    s += ''.join(f'--s{i + 1}:{c};' for i, c in enumerate(t['series'][:6])) + '}'
    return s


# ───────────────────────── 文字 ─────────────────────────
def esc(s):
    return html.escape('' if s is None else str(s), quote=True)


_TAGS = {'g': 'good', 'r': 'bad', 'a': 'mid', 'n': 'accent', 'k': 'dark'}


def inline(s):
    """安全的行内标记：**加粗**  ==强调色==  `代码`  [[g:通过]] [[r:失败]] [[a:停下]] [[n:中性]] [[k:深色]]  换行 \\n。"""
    if s is None:
        return ''
    s = html.escape(str(s), quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'==(.+?)==', r'<span class="hl">\1</span>', s, flags=re.S)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    s = re.sub(r'\[\[([grank]):(.+?)\]\]', lambda m: f'<span class="tag t-{m.group(1)}">{m.group(2)}</span>', s)
    return s.replace('\n', '<br>')


def plain(s):
    """去掉行内标记，用于 SVG 文本和宽度估算。"""
    s = '' if s is None else str(s)
    s = re.sub(r'\*\*(.+?)\*\*|==(.+?)==|`(.+?)`', lambda m: m.group(1) or m.group(2) or m.group(3), s)
    return re.sub(r'\[\[[grank]:(.+?)\]\]', r'\1', s)


def cw(ch):
    o = ord(ch)
    if o < 0x80:
        if ch == ' ':
            return .3
        if ch in 'il.,;:!|\'`1jtfI()[]':
            return .32
        if ch in 'mwMW@%':
            return .88
        if ch.isupper() or ch.isdigit():
            return .62
        return .55
    if (0x2E80 <= o <= 0x9FFF) or (0xAC00 <= o <= 0xD7AF) or (0xFF00 <= o <= 0xFFEF) or (0x3000 <= o <= 0x303F) \
            or (0x2010 <= o <= 0x2027) or (0xF900 <= o <= 0xFAFF):
        return 1.0
    return .72


def tw(s):
    """估算文字宽度，单位 em（CJK=1，拉丁约 0.55）。"""
    return sum(cw(c) for c in plain(s))


_NO_START = set('，。、；：！？）」』》〉】〕…—,.;:!?)]}%')
_NO_END = set('（「『《〈【〔([{')


def wrap(s, max_em, max_lines=None):
    """按估算宽度换行，遵守简单的避头尾规则。返回行列表。"""
    s = plain(s)
    lines = []
    for para in s.split('\n'):
        cur, w = '', 0.0
        i = 0
        toks = re.findall(r'[A-Za-z0-9_\-./%+#@]+|\s+|.', para, flags=re.S)
        for tk in toks:
            tkw = tw(tk)
            if tk.isspace():
                if cur:
                    cur += ' '
                    w += .3
                continue
            if w + tkw > max_em and cur:
                if len(tk) == 1 and tk in _NO_START:
                    cur += tk
                    w += tkw
                    continue
                if cur and cur[-1] in _NO_END:
                    ch, cur = cur[-1], cur[:-1]
                    lines.append(cur.rstrip())
                    cur, w = ch + tk, cw(ch) + tkw
                    continue
                # 超长的拉丁词按字符切
                lines.append(cur.rstrip())
                cur, w = '', 0.0
            if tkw > max_em:
                for ch in tk:
                    if w + cw(ch) > max_em and cur:
                        lines.append(cur)
                        cur, w = '', 0.0
                    cur += ch
                    w += cw(ch)
            else:
                cur += tk
                w += tkw
        lines.append(cur.rstrip())
    lines = [l for l in lines] or ['']
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip('，。、；： ') + '…'
    return lines


# ───────────────────────── 上下文与注册表 ─────────────────────────
class Ctx:
    """渲染上下文：调色板 token、风格旋钮、可用宽度（mm）、素材解析、告警收集。"""

    def __init__(self, pal, style, base_dir='.', width_mm=180.0, report=None, seed=7):
        self.pal, self.style, self.base = pal, style, base_dir
        self.w = width_mm
        self.report = report if report is not None else {'missing': [], 'warn': []}
        self._n = [0]
        self.seed = seed
        self.page = None
        self.inventory = {}
        self.facts = {}

    def uid(self, p='u'):
        self._n[0] += 1
        return f'{p}{self._n[0]}'

    def child(self, w=None):
        c = Ctx(self.pal, self.style, self.base, self.w if w is None else w, self.report, self.seed)
        c._n = self._n
        c.page = self.page
        c.inventory = self.inventory
        c.facts = self.facts
        return c

    def warn(self, msg):
        self.report['warn'].append(f'[{self.page or "-"}] {msg}')

    def img(self, path):
        """返回可放进 src/url() 的路径；文件不存在时记录缺图。"""
        if not path:
            return ''
        if path.startswith('data:image/'):
            return path
        if path.startswith(('http://', 'https://')):
            raise ValueError('请先下载并核对图片，生成文档只使用本地素材。')
        full = path if os.path.isabs(path) else os.path.join(self.base, path)
        if not os.path.exists(full):
            self.report['missing'].append(path)
            return ''
        mime = mimetypes.guess_type(full)[0] or ''
        if not mime.startswith('image/'):
            raise ValueError(f'素材不是图片：{path}')
        return 'data:' + mime + ';base64,' + base64.b64encode(Path(full).read_bytes()).decode('ascii')


class Comp:
    def __init__(self, name, kind, title, use, avoid, fields, sample, fn, h):
        self.name, self.kind, self.title, self.use, self.avoid = name, kind, title, use, avoid
        self.fields, self.sample, self.fn, self.h = fields, sample, fn, h


REG = {}
KINDS = {'cover': '封面', 'header': '页头', 'page': '整页', 'layout': '布局', 'text': '文字', 'number': '数字',
         'card': '卡片', 'figure': '图片与图表', 'structure': '结构', 'time': '时间', 'table': '表格'}


def component(name, kind, title, use, avoid='', fields='', sample=None, h=None):
    """注册组件。use=什么情况选它；avoid=什么情况别选；fields=字段说明；sample=示例属性；h=大致高度 mm。"""
    def deco(fn):
        REG[name] = Comp(name, kind, title, use, avoid, fields, sample or {}, fn, h)
        return fn
    return deco


def render_block(ctx, spec):
    if isinstance(spec, str):
        spec = {'type': 'p', 'text': spec}
    t = spec.get('type')
    if t not in REG:
        near = [k for k in REG if t and (t in k or k in t)][:4]
        raise KeyError(f'未知组件 type={t!r}。' + (f'相近：{", ".join(near)}。' if near else '') + ' 运行 scripts/catalog.py 查看全部。')
    body = REG[t].fn(ctx, {k: v for k, v in spec.items() if k != 'type'})
    refs = spec.get('source_ids', [])
    facts = spec.get('fact_ids', [])
    return (f'<div class="blk" data-component="{esc(t)}" data-source-ids="{esc(json.dumps(refs, ensure_ascii=False))}" '
            f'data-fact-ids="{esc(json.dumps(facts, ensure_ascii=False))}">{body}</div>')


def render_blocks(ctx, specs):
    return ''.join(render_block(ctx, s) for s in specs or [])


def get(p, k, d=None):
    v = p.get(k, d)
    return d if v is None else v


def mm(v):
    return f'{v:.2f}mm'


def fit_h(h):
    """随页面自动伸缩的高度（mm）：由 fit.py 调节 --fit。"""
    return f'calc({h}mm * var(--fit, 1))'
