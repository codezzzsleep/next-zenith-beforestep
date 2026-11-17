"""Content-first text and nesting. No raw HTML and no automatic summarization."""
from core import component, inline as I, esc as E, render_blocks as RB, render_block as R

@component('p','text','正文','解释事实、条件、细节','不要为了排版缩写原文','text',{'text':'先交代事实，再说明条件。内容长度决定页数。'})
def paragraph(c,p): return '<p class="p">'+I(p['text'])+'</p>'

@component('lead','text','导语','一段概述或主要判断','不强制每页都有导语','text',{'text':'让材料决定结构，让设计帮助阅读。'})
def lead(c,p): return '<p class="lead">'+I(p['text'])+'</p>'

@component('heading','text','段落标题','同页的次级分组','','text',{'text':'材料与依据'})
def heading(c,p): return '<h3 class="h3">'+I(p['text'])+'</h3>'

@component('callout','text','提示与结论','已有证据的结论或限定条件','不要为填空新增结论','text; label?; variant=note|good|bad|warn|dark',{'label':'阅读提示','text':'示例数值仅用于展示图形，不代表任何项目事实。','variant':'note'})
def callout(c,p): return f'<aside class="say {E(p.get("variant",""))}">'+(f'<b class="sl">{I(p["label"])}</b>' if p.get('label') else '')+I(p['text'])+'</aside>'

@component('quote','text','引文','保留访谈或引用的原话','无真实引文时不用','text; by; source?',{'text':'真正需要的是现场能用的帮助。','by':'虚构访谈示例'})
def quote(c,p): return f'<blockquote class="pull"><div class="q">{I(p["text"])}</div><div class="by">{I(p.get("by",""))}</div></blockquote>'

@component('list','text','列表三变体','并列事项、顺序动作、核对项','无先后关系不加步骤号','items: strings; variant=bullet|number|check',{'items':['保留条件与例外','保留原始图表','保留出处与标注'],'variant':'bullet'})
def listing(c,p):
    cls={'bullet':'bul','number':'num','check':'chk'}[p.get('variant','bullet')]
    return f'<ul class="{cls}" data-split="children">'+''.join(f'<li>{I(x)}</li>' for x in p['items'])+'</ul>'

@component('definitions','text','术语与键值','术语、规格、职责等精确对应','','items: [{term,text}]',{'items':[{'term':'信息单元','text':'源材料中需要保留的段落、图、表或注释。'},{'term':'版式','text':'信息的排列方式，可随内容改变。'}]})
def definitions(c,p): return '<dl class="dl">'+''.join(f'<dt>{I(x["term"])}</dt><dd>{I(x["text"])}</dd>' for x in p['items'])+'</dl>'

@component('columns','text','文字分栏','2–3 个并列主题','长文改连续段落；不得把先后当并列','items: [{title,text}]; cols?',{'items':[{'title':'问题','text':'来自材料中的真实问题。'},{'title':'方法','text':'保留实际采用的方法。'}]})
def columns(c,p): return f'<div class="tcols" style="grid-template-columns:repeat({p.get("cols",len(p["items"]))},1fr)">'+''.join(f'<div><h4>{I(x["title"])}</h4><p>{I(x["text"])}</p></div>' for x in p['items'])+'</div>'

@component('source','text','原文保留块','重排已有文件时逐单元保留','不把 source_ids 当作已经保留内容的证明','ids: inventory unit ids; title?',{'ids':[]})
def source(c,p):
    out=[]
    for sid in p['ids']:
        u=c.inventory[sid]
        if u['kind']=='image':
            body=f'<figure><img class="source-image" src="{c.img(u["asset"])}" alt="{E(u.get("text","原图"))}"><figcaption class="cap">{I(u.get("text",""))}</figcaption></figure>'
        else: body='<p class="p">'+E(p.get('fragments',{}).get(sid,u['text'])).replace('\n','<br>')+'</p>'
        out.append(f'<div class="source-unit" data-unit-id="{E(sid)}">{body}</div>')
    return (f'<h3 class="h3">{I(p["title"])}</h3>' if p.get('title') else '')+'<div class="source-group" data-split="children">'+''.join(out)+'</div>'

@component('row','layout','比例分栏','图片与文字或证据并置','A4 通栏最多 3 列，嵌套时最多 2 列','items: components; ratios?',{'items':[{'type':'card','title':'左栏','text':'内容决定比例。'},{'type':'card','title':'右栏','text':'支持 1:1 或 2:1。'}],'ratios':[1,1]})
def row(c,p):
    items=p['items']; ratios=p.get('ratios',[1]*len(items))
    if not 1<=len(items)<=3 or len(ratios)!=len(items) or any(x<=0 for x in ratios):raise ValueError('row 需要 1–3 栏与等长正比例')
    gap=4*(len(items)-1)
    return '<div class="row" style="grid-template-columns:'+ ' '.join(f'{v}fr' for v in ratios)+'">'+''.join(R(c.child((c.w-gap)*r/sum(ratios)),x) for r,x in zip(ratios,items))+'</div>'

@component('stack','layout','连续块','组合多个同主题块','','blocks',{'blocks':[{'type':'heading','text':'按主题组合'},{'type':'p','text':'组合保持每个块的来源与顺序。'}]})
def stack(c,p):return '<div data-split="children">'+RB(c,p['blocks'])+'</div>'
