from core import component,inline as I,esc as E,render_blocks as RB
import diagram

@component('process','structure','线性步骤','2–7 个有先后关系的动作','出现分支或回路时用 diagram；超过 7 步拆成主干与子流程','items:[{title,text}]; key?',{'items':[{'title':'收集','text':'读取原始材料。'},{'title':'整理','text':'保留信息与出处。'},{'title':'表达','text':'按关系选组件。'},{'title':'核对','text':'检查内容与版面。'}]})
def process(c,p):
    items=p['items'];n=len(items)
    if not 2<=n<=7:raise ValueError('process 使用 2–7 步；更多步骤请拆分')
    if n>4 or c.w<120:
        return '<div class="vl" data-split="children">'+''.join(f'<div class="it"><div class="n">{i+1}</div><div><b>{I(x["title"])}</b><span>{I(x.get("text",""))}</span></div></div>' for i,x in enumerate(items))+'</div>'
    return f'<div class="flow" style="grid-template-columns:'+ ' 5mm '.join(['1fr']*n)+'">'+''.join((('<div class="ar">→</div>') if i else '')+f'<div class="step {"key" if i==p.get("key",-1) else ""}"><div class="n">{i+1}</div><b>{I(x["title"])}</b><span>{I(x.get("text",""))}</span></div>' for i,x in enumerate(items))+'</div>'

@component('diagram','structure','拓扑结构图五种','分支流程、树、系统依赖、跨角色交接、循环','箭头必须对应已知关系','data: {kind,nodes,edges,...}; caption?',{'data':diagram.sample('flow'),'caption':'仅表达声明的先后与分支。'})
def diagram_block(c,p):return '<figure>'+diagram.make(p['data'],c.pal)+f'<figcaption class="cap">{I(p.get("caption",""))}</figcaption></figure>'

@component('layers','structure','分层架构','3–6 个职责层及其成员','层级图不自动表示数据流向','items:[{title,subtitle?,text,modules?}]',{'items':[{'title':'交互层','text':'用户可以操作的入口。','modules':['输入','结果']},{'title':'服务层','text':'完成领域任务。','modules':['编排','计算']},{'title':'数据层','text':'材料与可核对的记录。','modules':['资料','日志']}]})
def layers(c,p):return '<div class="layers">'+''.join(f'<div class="ly"><div class="lh" style="background:{c.pal["dark" if i==0 else "accent_ink"]}">{I(x["title"])}<span>{I(x.get("subtitle",""))}</span></div><div class="lc">{I(x.get("text",""))}<div>'+''.join(f'<span class="chip">{I(m)}</span>' for m in x.get('modules',[]))+'</div></div></div>' for i,x in enumerate(p['items']))+'</div>'

@component('converge','structure','两组条件汇合','明确的两类输入汇成一个结果','没有汇合关系时改成并列卡片','left:{title,items}; right:{title,items}; result; note?',{'left':{'title':'材料条件','items':['真实内容','可核对数据']},'right':{'title':'表达条件','items':['阅读任务','素材特点']},'result':'选择适合当前项目的版式','note':'汇合关系示例。'})
def converge(c,p):
    return '<div class="conv"><div class="two">'+''.join(f'<div class="side"><h3 class="sh2">{I(p[k]["title"])}</h3>'+''.join(f'<div class="itm">{I(t)}</div>' for t in p[k]['items'])+'</div>' for k in ['left','right'])+f'</div><div class="mid"><span>↓</span><span>↓</span></div><div class="res"><div class="rt">{I(p["result"])}</div><div class="rs">{I(p.get("note",""))}</div></div></div>'

@component('timeline','time','纵向时间线','≥3 个真实时间或明确阶段节点；过程回顾','没有时间信息的动作改用 process','items:[{date,title,text,status?}]; caption?',{'items':[{'date':'2027-01-01','title':'调研（计划）','text':'收集使用场景。'},{'date':'2027-01-15','title':'原型（计划）','text':'制作可测试版本。'},{'date':'2027-02-01','title':'验证（计划）','text':'按明确口径验证。'}]})
def timeline(c,p):return '<div class="tl" data-split="children">'+''.join(f'<div class="it {"x" if x.get("status")=="failed" else ""}"><div class="d">{I(x["date"])}</div><b>{I(x["title"])}</b><p>{I(x.get("text",""))}</p></div>' for x in p['items'])+'</div><p class="cap">'+I(p.get('caption','节点等距排布，不表示时间间隔。'))+'</p>'

@component('timeline-horizontal','time','横向里程碑','3–5 个短时间节点','长说明或更多节点用纵向时间线','items:[{date,title,text?}]',{'items':[{'date':'一月','title':'调研','text':'计划'},{'date':'二月','title':'原型','text':'计划'},{'date':'三月','title':'验证','text':'计划'}]})
def timeline_h(c,p):
    if not 2<=len(p['items'])<=5:raise ValueError('横向里程碑限 2–5 个节点')
    return f'<div class="tlh" style="grid-template-columns:repeat({len(p["items"])},1fr)">'+''.join(f'<div class="m"><div class="d">{I(x["date"])}</div><b>{I(x["title"])}</b><p>{I(x.get("text",""))}</p></div>' for x in p['items'])+'</div><p class="cap">节点等距排布，不表示时间间隔。</p>'

@component('roadmap','time','阶段路线图','只有阶段目标、尚无确定日期','不要自动补出年月日','items:[{phase,title,tasks:strings}]',{'items':[{'phase':'阶段一','title':'材料整理','tasks':['核对内容','识别缺项']},{'phase':'阶段二','title':'设计表达','tasks':['选择组件','渲染复核']}]})
def roadmap(c,p):return f'<div class="road" style="grid-template-columns:repeat({min(3,len(p["items"]))},1fr)">'+''.join(f'<div><div class="ph">{I(x["phase"])}<span>{I(x["title"])}</span></div><div class="pc"><ul class="bul">'+''.join(f'<li>{I(t)}</li>' for t in x['tasks'])+'</ul></div></div>' for x in p['items'])+'</div>'

def _table(c,p,matrix=False):
    cols=p['columns'];rows=p['rows'];n=len(cols)
    if not 1<=n<=8:raise ValueError('A4 表格只使用 1–8 列；更多列请分表或用横版附录')
    if any(len(r)!=n for r in rows):raise ValueError('表格行列不齐')
    symbols={'yes':'支持','no':'不支持','partial':'部分支持','unknown':'未提供'}
    def cell(v):return I(symbols.get(v,v)) if matrix and isinstance(v,str) else I(v)
    return '<div class="table-shell" data-split="table"><table class="tbl v-'+E(p.get('variant','line'))+(' zebra' if p.get('zebra') else '')+'"><thead><tr>'+''.join(f'<th>{I(x)}</th>' for x in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{cell(v)}</td>' for v in r)+'</tr>' for r in rows)+'</tbody></table></div>'+(f'<p class="cap">{I(p["note"])}</p>' if p.get('note') else '')

@component('table','table','精确表格三变体','精确值、规格、条款、清单和明细','无需把所有表格改成图','columns: strings; rows: arrays; variant=line|dark|tint; note?',{'columns':['项目','内容','状态'],'rows':[['材料','原始来源','已提供'],['版式','按内容选择','示例']],'variant':'line'})
def table(c,p):return _table(c,p)

@component('matrix','table','方案对比矩阵','2–6 方案 × 3–8 个共同维度；定性或混合值','不同维度不可擅自打分求和；缺失不等于不支持','columns; rows; note?',{'columns':['方案','适用情境','素材要求','限制'],'rows':[['文字封面','概念与研究','无图片也可','靠标题与排版'],['影像封面','实物与场景','真实大图','不得替代证据']],'note':'这里只作形式选择示例，不含优劣评分。'})
def matrix(c,p):return _table(c,dict(p,variant=p.get('variant','dark')),True)

@component('budget','table','预算与金额明细','有单价、数量、单位的预算','不要用图替代审计所需明细','items:[{name,quantity,unit_price,unit}]; currency?; total_label?; note?',{'items':[{'name':'示例材料','quantity':2,'unit_price':150,'unit':'份'},{'name':'示例制作','quantity':3,'unit_price':200,'unit':'次'}],'currency':'元','note':'虚构数据，仅用于组件展示。'})
def budget(c,p):
    from decimal import Decimal
    rows=[];total=Decimal(0)
    for x in p['items']:
        q=Decimal(str(x['quantity']));v=Decimal(str(x['unit_price']))
        if q<0 or v<0:raise ValueError('预算数量与单价不得为负')
        subtotal=q*v;total+=subtotal;rows.append([x['name'],f'{q} {x["unit"]}',f'{v:.2f}',f'{subtotal:.2f}'])
    rows.append([p.get('total_label','合计'),'','',f'{total:.2f}'])
    return _table(c,{'columns':['项目','数量','单价（'+p.get('currency','元')+'）','小计'],'rows':rows,'variant':'dark','note':p.get('note','按单价 × 数量计算。')})
