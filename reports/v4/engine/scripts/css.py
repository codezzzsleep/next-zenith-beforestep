"""Resolve the known design tokens and arithmetic before PDF layout.
WeasyPrint's unsupported CSS arithmetic must never silently change typography.
No user code, eval, network assets or external stylesheets are accepted.
"""
import ast,re
from core import css_vars

def _calc(expr):
    # Canonical lengths in mm. Percent arithmetic needs layout context: leave it alone.
    if '%' in expr:return 'calc('+expr+')'
    unit=bool(re.search(r'(mm|pt|px)\b',expr))
    factors={'mm':1,'pt':25.4/72,'px':25.4/96}
    expr=re.sub(r'([\d.]+)(mm|pt|px)\b',lambda m:str(float(m[1])*factors[m[2]]),expr)
    def go(n):
        if isinstance(n,ast.Expression):return go(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(float,int)):return n.value
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -go(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=go(n.left),go(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError('不支持的 CSS 算术')
    return f'{go(ast.parse(expr,mode="eval")):.6f}'+('mm' if unit else '')

def freeze(css,style,pal):
    tokens={}
    def declarations(body):
        for k,v in re.findall(r'(--[\w-]+)\s*:\s*([^;{}]+)',body):tokens[k]=v.strip()
    for body in re.findall(r':root\s*\{([^}]+)\}',css):declarations(body)
    for sel,body in re.findall(r'([^{}]+)\{([^{}]*)\}',css):
        if '.page,.pgfull' in sel:declarations(body)
    for key,val in style.items():
        if not isinstance(val,str):continue
        pattern=r'html\[data-'+re.escape(key)+r'="'+re.escape(val)+r'"\]\s*\{([^}]+)\}'
        for body in re.findall(pattern,css):declarations(body)
    declarations(css_vars(pal))
    def resolve(s,depth=0):
        if depth>30:raise ValueError('CSS token 循环引用')
        s=re.sub(r'var\((--[\w-]+)(?:,\s*([^()]+))?\)',lambda m:resolve(tokens.get(m[1],m[2] or 'initial'),depth+1),s)
        for _ in range(12):
            ns=re.sub(r'calc\(([^()]+)\)',lambda m:_calc(m[1]),s)
            if ns==s:break
            s=ns
        return s
    # Declarations are removed after values resolve: no hidden cascade remains.
    out=resolve(css)
    out=re.sub(r'--[\w-]+\s*:[^;{}]+;?','',out)
    return out
