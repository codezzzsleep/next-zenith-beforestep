from core import component, inline as I, esc as E, render_blocks as RB

@component('card','card','通用卡片八变体','分组信息；变体用于信息层级','不把每个段落都装进卡片','title?; text?; blocks?; variant=default|white|dark|accent|top|good|bad|mid',{'title':'一个完整的信息组','text':'卡片可以放正文，也可以组合其他组件。','variant':'top'})
def card(c,p):
    skin=p.get('variant','default')
    return f'<article class="card {"is-"+E(skin) if skin!="default" else ""}">'+(f'<h3 class="ct">{I(p["title"])}</h3>' if p.get('title') else '')+(f'<div class="cs">{I(p["text"])}</div>' if p.get('text') else '')+RB(c.child(c.w-9),p.get('blocks',[]))+'</article>'

@component('cards','card','并列卡片组','能力、问题、原则等同级信息','过程关系应使用 process','items:[{title,text,variant?}]; cols=1|2|3',{'cols':2,'items':[{'title':'理解','text':'先识别材料的真实信息。'},{'title':'表达','text':'再选择适合的视觉形式。'}]})
def cards(c,p):
    n=p.get('cols',2)
    if n not in (1,2,3):raise ValueError('cards.cols 只能为 1、2、3')
    return f'<div class="cards" data-split="children" style="grid-template-columns:repeat({n},1fr)">'+''.join(card(c.child((c.w-4*(n-1))/n),x) for x in p['items'])+'</div>'

@component('failure','card','边界与失败卡','已发生的问题或明确局限','不要在没有证据时强凑失败','title; phenomenon; cause; next; variant=bad|mid|good',{'title':'当前边界（示例）','phenomenon':'材料中尚无实地验证结果。','cause':'项目仍处在原型阶段。','next':'将实地验证列为计划，不写成完成。','variant':'mid'})
def failure(c,p):return f'<article class="card fail f-{E(p.get("variant","bad"))}"><div class="fh">{I(p["title"])}</div>'+''.join(f'<div class="fr"><b>{a}</b><span>{I(p[k])}</span></div>' for a,k in [('现象','phenomenon'),('原因','cause'),('下一步','next')])+'</article>'

@component('person','card','人物与职责','团队成员、服务对象、角色','不要虚构头像与履历','name; role; bio; initials?',{'name':'示例成员','role':'设计与验证','bio':'这里只写材料支持的职责。','initials':'设'})
def person(c,p):return f'<div class="card person"><div class="av">{I(p.get("initials",p["name"][:1]))}</div><div><div class="nm">{I(p["name"])}</div><div class="rl">{I(p["role"])}</div><div class="bio">{I(p["bio"])}</div></div></div>'

@component('link','card','资源链接卡','演示、代码、文献与复现材料','不得伪造可访问链接','label; url; description?',{'label':'示例资源入口','url':'https://example.com','description':'实际使用时填入可核对的链接。'})
def link(c,p):
    from urllib.parse import urlparse
    u=p['url']
    if urlparse(u).scheme not in ('http','https','mailto'):raise ValueError('link.url 只接受 http/https/mailto')
    return f'<div class="card lnk"><div class="lb">{I(p["label"])}</div><a class="u" href="{E(u)}">{E(u)}</a><p class="ds">{I(p.get("description",""))}</p></div>'

@component('evidence','card','证据与限定条件','结果、方法与局限成组阅读','不可只显示结论而省略条件','title; finding; method; boundary; source',{'title':'一项证据（示例）','finding':'结果应逐字保留原口径。','method':'注明样本、环境、对照与指标。','boundary':'说明尚未覆盖的情况。','source':'对应源文件与页码。'})
def evidence(c,p):return card(c,{'title':p['title'],'variant':'white','blocks':[{'type':'lead','text':p['finding']},{'type':'definitions','items':[{'term':'方法','text':p['method']},{'term':'边界','text':p['boundary']},{'term':'来源','text':p['source']}]}]})
