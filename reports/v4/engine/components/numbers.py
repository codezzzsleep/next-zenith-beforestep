from core import component, inline as I, esc as E

@component('metric','number','单项数字','一个有来源、有单位的关键量','没有关键数据时不用','value; unit?; label; note?; variant=horizontal|vertical|dark',{'value':'24','unit':'份','label':'样本示例','note':'仅展示排版，不是项目数据。'})
def metric(c,p):
    variant={'vertical':'v','dark':'dk'}.get(p.get('variant'),'')
    return f'<div class="sh {variant}"><div class="n">{I(p["value"])}<small>{I(p.get("unit",""))}</small></div><div class="d"><b>{I(p["label"])}</b><span>{I(p.get("note",""))}</span></div></div>'

@component('metrics','number','数字卡组','2–4 个相关的量','单位不同不画共同长度比较','items:[{value,label,unit?,note?}]; cols?',{'items':[{'value':'12','label':'样本 A','unit':'份'},{'value':'18','label':'样本 B','unit':'份'},{'value':'24','label':'样本 C','unit':'份'}]})
def metrics(c,p):
    n=p.get('cols',min(3,len(p['items'])))
    return f'<div class="cards" style="grid-template-columns:repeat({n},1fr)">'+''.join(f'<div class="card sc"><div class="n">{I(x["value"])}<small>{I(x.get("unit",""))}</small></div><div class="l"><b>{I(x["label"])}</b><br>{I(x.get("note",""))}</div></div>' for x in p['items'])+'</div>'

@component('stat-bar','number','细数字带','页尾或导读中的短数据','不强制封面三数字','items:[{value,label}]; dark?',{'items':[{'value':'3','label':'示例阶段'},{'value':'2','label':'示例方案'}]})
def statbar(c,p):return f'<div class="statrow {"dk" if p.get("dark") else ""}" style="grid-template-columns:repeat({len(p["items"])},1fr)">'+''.join(f'<div><b>{I(x["value"])}</b><span>{I(x["label"])}</span></div>' for x in p['items'])+'</div>'

@component('ratio','number','分子分母占比','分母明确的完成数、命中数','不把样本通过率当可靠性承诺','value:number; total:number; label; note?',{'value':18,'total':24,'label':'样本通过数（示例）','note':'分母与统计口径必须保留。'})
def ratio(c,p):
    v,t=p['value'],p['total']
    if t<=0 or v<0 or v>t:raise ValueError('ratio 需要 0 ≤ value ≤ total 且 total > 0')
    return f'<div class="card ratio"><div class="rt"><b>{I(p["label"])}</b><span class="n">{v} / {t}</span></div><div class="bar"><i style="width:{100*v/t:.3f}%"></i></div><div class="rs">{I(p.get("note",""))}</div></div>'

@component('delta','number','前后双值','同口径前后两次测量','不同样本条件不可暗示因果','before; after; before_label; after_label; note?',{'before':'18 分钟','after':'12 分钟','before_label':'改动前（示例）','after_label':'改动后（示例）','note':'相同任务与计时口径；颜色不自动表示改善。'})
def delta(c,p):return f'<div class="card"><div class="delta"><div class="a"><div class="v">{I(p["before"])}</div><div class="t2">{I(p["before_label"])}</div></div><div class="ar">→</div><div class="b"><div class="v">{I(p["after"])}</div><div class="t2">{I(p["after_label"])}</div></div></div><p class="cap">{I(p.get("note",""))}</p></div>'
