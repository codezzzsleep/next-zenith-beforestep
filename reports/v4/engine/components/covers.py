"""Seven compositions. Shared identity; no mandatory hero, metrics or claims."""
from core import component,inline as I,esc as E
from .figures import _visual
from .numbers import statbar

DESCRIPTIONS={
 'horizon':('地平线','场景、自然、城市与文化主题；一张横向主视觉','无场景特征时不要硬套山水'),
 'poster':('整幅海报','有强主视觉或适合抽象意象的创意项目','文字多或图片细节需要精读时不用'),
 'type':('字体主导','研究、申报、概念、暂无可靠大图','标题与信息层级要足够鲜明'),
 'split':('左右分栏','物体、装置、产品或纵向照片与说明并置','需要横向全景时改 horizon'),
 'numbers':('数据主导','1–3 个已核对且能代表项目的数据','无可靠关键数据时禁止选择'),
 'frame':('框景与题签','文化、出版、档案与机构类项目','不要把所有文化题材强行做仿古'),
 'mosaic':('素材拼图','2–4 张不同但互补的真实产出','没有多个素材时不复制同一张图凑格')}

def render_cover(c,p,kind):
    title=p['title'];subtitle=p.get('subtitle','');kicker=p.get('kicker','');desc=p.get('description','');meta=p.get('meta',[])
    txt=(f'<div class="cover-kicker">{I(kicker)}</div>' if kicker else '')+f'<h1>{I(title)}</h1>'+(f'<div class="cover-subtitle">{I(subtitle)}</div>' if subtitle else '')+(f'<p class="cover-desc">{I(desc)}</p>' if desc else '')
    mt='<div class="cover-meta">'+''.join(f'<div><span>{I(x["label"])}</span><b>{I(x["value"])}</b></div>' for x in meta)+'</div>' if meta else ''
    vis=lambda spec:_visual(c,dict(spec,art=spec.get('art',c.style['art'])))
    visual=vis(p.get('visual',{}))
    if kind=='numbers':
        if not 1<=len(p.get('metrics',[]))<=3:raise ValueError('数据封面需要 1–3 项有来源的 metrics；否则选 type/split/horizon')
        content=f'<div class="cover-art">{visual}</div><div class="cover-copy">{txt}</div>'+statbar(c,{'items':p['metrics'],'dark':True})
    elif kind=='type':content=f'<div class="cover-type-rule"></div><div class="cover-copy">{txt}</div>'
    elif kind=='mosaic':
        images=p.get('visuals',[])
        if not 2<=len(images)<=4:raise ValueError('拼图封面需要 2–4 张互补素材，缺图时换封面')
        content='<div class="cover-mosaic">'+''.join('<div>'+vis(s)+'</div>' for s in images)+f'</div><div class="cover-copy">{txt}</div>'
    else:content=f'<div class="cover-art">{visual}</div><div class="cover-copy">{txt}</div>'
    return f'<div class="cover-layout cover-{kind}">{content}{mt}</div>'

for _kind,(_title,_use,_avoid) in DESCRIPTIONS.items():
    sample={'title':'材料的形状','subtitle':'项目书设计系统 · 构图示例','kicker':'COMPOSITION STUDY','description':'固定设计语言，按材料选择表达方式。此页内容仅作排版演示。','meta':[{'label':'文档','value':'作品策划案'},{'label':'版本','value':'演示版'}]}
    if _kind=='numbers':sample['metrics']=[{'value':'18','label':'种数据图表'},{'value':'7','label':'种封面构图'}]
    if _kind=='mosaic':sample['visuals']=[{'art':'blocks'},{'art':'waves'},{'art':'orbits'}]
    def factory(kind):
        def fn(c,p):return render_cover(c,p,kind)
        return fn
    component('cover.'+_kind,'cover',_title,_use,_avoid,'title; subtitle?; description?; kicker?; visual?; meta?; metrics?; visuals?',sample)(factory(_kind))
