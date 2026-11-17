"""Small exact SVG primitives. Text wraps without ellipsizing."""
import math
from core import esc, wrap

FONT='Noto Sans CJK SC,Microsoft YaHei,PingFang SC,sans-serif'

def num(v):
    v=float(v)
    if not math.isfinite(v):raise ValueError('图表数值必须是有限数')
    return v

def fmt(v):return f'{v:,.3f}'.rstrip('0').rstrip('.') if v%1 else f'{v:,.0f}'

class Canvas:
    def __init__(self,w,h,pal,title=''):
        self.w,self.h,self.pal,self.parts,self.title=w,h,pal,[],title
    def text(self,x,y,s,size=16,fill=None,anchor='start',weight=400,width=None):
        lines=wrap(str(s),width/size) if width else str(s).split('\n')
        self.parts.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill or self.pal["ink"]}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="{FONT}">'+''.join(f'<tspan x="{x:.2f}" dy="{0 if i==0 else size*1.4}">{esc(t)}</tspan>' for i,t in enumerate(lines))+'</text>')
    def rect(self,x,y,w,h,fill,stroke='none',r=0):
        self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(0,w):.2f}" height="{max(0,h):.2f}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
    def line(self,x1,y1,x2,y2,color=None,width=1,dash=None):
        self.parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color or self.pal["line2"]}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def circle(self,x,y,r,fill,stroke='none'):
        self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke}"/>')
    def path(self,d,stroke='none',fill='none',width=2,extra=''):
        self.parts.append(f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{width}" {extra}/>')
    def finish(self):
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="100%" role="img" aria-label="{esc(self.title)}"><title>{esc(self.title)}</title>'+''.join(self.parts)+'</svg>'

def scale(lo,hi,a,b):
    if lo==hi:lo,hi=lo-1,hi+1
    return lambda v:a+(num(v)-lo)/(hi-lo)*(b-a)

def extent(values,zero=False):
    vs=[num(v) for v in values]
    if not vs:raise ValueError('数据不能为空')
    lo,hi=min(vs),max(vs)
    if zero:lo,hi=min(0,lo),max(0,hi)
    if hi==lo:hi=lo+1
    return lo,hi
