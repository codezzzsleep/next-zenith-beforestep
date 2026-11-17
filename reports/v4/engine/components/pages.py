from core import component,inline as I,esc as E,render_blocks as RB
from .figures import _visual

HEADERS={'kicker':'标签页头','numeral':'章节序号','band':'色带页头','rail':'侧栏页头','split':'标题与摘要','minimal':'极简页头'}
def header(c,p,kind):
    no=p.get('number','');title=f'<h2 class="ttl">{I(p.get("title",""))}</h2>';kick=f'<div class="k">{I(p.get("kicker",""))}</div>' if p.get('kicker') else '';lead=f'<p class="lead">{I(p["lead"])}</p>' if p.get('lead') else ''
    if kind=='numeral':body=f'<div class="no">{I(no)}</div><div class="tt">{kick}{title}</div>{lead}'
    elif kind=='rail':body=f'<div class="rl"><div class="no">{I(no)}</div></div><div>{kick}{title}</div>{lead}'
    elif kind=='split':body=f'<div>{kick}{title}</div><div class="ans">{I(p.get("answer",p.get("lead","")))}</div>'+('' if not p.get('answer') else lead)
    else:body=kick+(f'<div class="section-number">{I(no)}</div>' if no else '')+title+lead
    return f'<header class="hd hd-{kind}">{body}</header>'

for _kind,_title in HEADERS.items():
    def factory(k):
        def fn(c,p):return header(c,p,k)
        return fn
    component('header.'+_kind,'header',_title,'整份报告选一种主页头；可在章节入口变奏','无序内容不要强加章节号','title; kicker?; number?; lead?; answer?',{'title':'内容决定表达方式','kicker':'DESIGN PRINCIPLE','number':'02','lead':'以一个主题组织页面，复杂主题可延续到下一页。','answer':'先保留信息，再决定版式。'})(factory(_kind))

@component('page.opener','page','章节扉页','确实需要区分大型章节时','短报告不必每章一扉页','title; subtitle?; art?',{'title':'从材料开始','subtitle':'章节入口 · 只在需要阅读停顿时使用','art':'contours'})
def opener(c,p):return f'<div class="full-opener"><div class="full-art">{_visual(c,p)}</div><div class="full-copy"><span class="lbl">{I(p.get("kicker","CHAPTER"))}</span><h2>{I(p["title"])}</h2><p>{I(p.get("subtitle",""))}</p></div></div>'

@component('page.statement','page','观点整页','一句真实核心主张与必要解释','不能拿口号填原本缺失的证据','title; text; note?',{'title':'设计负责表达，\n材料决定内容。','text':'版式可以重组，证据、条件、例外和出处都应保留。','note':'设计原则示例'})
def statement(c,p):return f'<div class="full-statement"><div class="lbl">{I(p.get("kicker","STATEMENT"))}</div><h2>{I(p["title"])}</h2><p class="lead">{I(p["text"])}</p><p class="cap">{I(p.get("note",""))}</p></div>'

@component('page.plate','page','整页图版','实物、总览图、地图、复杂界面需要细读','证据图片不能以裁切丢掉注释','title; src?; art?; caption?',{'title':'让图像有充分的阅读空间','art':'network','caption':'装饰插画示例，实际使用优先真实产出。'})
def plate(c,p):return f'<div class="full-plate"><h2>{I(p["title"])}</h2><div class="plate-visual">{_visual(c,p)}</div><p class="cap">{I(p.get("caption",""))}</p></div>'

@component('page.editorial','page','图文整页','场景、设计说明、案例叙事','不得用装饰图挤掉正文','title; text; src?; art?; caption?',{'title':'先读懂材料，\n再决定它的样子。','text':'不同项目有不同的材料结构。\n\n有的需要真实影像，有的需要精确表格，有的需要一条说明决策的流程。','art':'ridges','caption':'排版研究 · 示例'})
def editorial(c,p):return f'<div class="full-editorial"><div class="editorial-visual">{_visual(c,p)}</div><div class="editorial-copy"><h2>{I(p["title"])}</h2><p>{I(p["text"])}</p><p class="cap">{I(p.get("caption",""))}</p></div></div>'

@component('page.contents','page','可编排目录','长文档、多个大章节','短文档不必加目录；页码由引擎解析','title?; items:[{title,target,description?}]',{'title':'阅读路径','items':[{'title':'问题与背景','target':'context','description':'从哪里开始'},{'title':'方法与证据','target':'evidence','description':'如何判断'},{'title':'计划与边界','target':'next','description':'还有什么要做'}]})
def contents(c,p):return f'<div class="contents"><h2>{I(p.get("title","目录"))}</h2>'+''.join(f'<div class="toc-row"><div><b>{I(x["title"])}</b><p>{I(x.get("description",""))}</p></div><span data-target="{E(x["target"])}">—</span></div>' for x in p['items'])+'</div>'
