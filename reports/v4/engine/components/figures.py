from core import component,inline as I,esc as E,render_block as R
import charts,art

def _visual(c,p):
    if p.get('src'):return f'<img src="{c.img(p["src"])}" alt="{E(p.get("alt",p.get("caption","")))}">'
    return art.make(p.get('art',c.style['art']),1000,650,c.pal,seed=p.get('seed',c.seed),bg=p.get('bg','cover'))

@component('image','figure','原图与实录','照片、运行截图、原始图表','证据默认 contain；只对装饰照片允许 cover','src; caption?; height?; fit=contain|cover; alt?',{'art':'ridges','caption':'程序插画示例，不是项目实录。','height':75})
def image(c,p):
    fit=p.get('fit','contain')
    return f'<figure class="fig"><div class="fi {"contain" if fit=="contain" else ""}" style="height:{p.get("height",65)}mm">{_visual(c,p)}</div><figcaption class="cap">{I(p.get("caption",""))}</figcaption></figure>'

@component('device','figure','设备与浏览器框','展示真实界面并说明运行端','不把示意界面标成已完成产品','src; caption?; url_label?; height?',{'art':'blocks','url_label':'界面结构示意','caption':'插画仅展示设备框组件。','height':65})
def device(c,p):return f'<figure class="dev"><div class="bar"><i style="left:3mm"></i><i style="left:6mm"></i><i style="left:9mm"></i><em>{E(p.get("url_label",""))}</em></div>'+image(c,p)+'</figure>'

@component('gallery','figure','图像画廊','2–6 张独立作品或界面','不把说明文字烘焙到图片','items: image specs; cols=2|3',{'cols':2,'items':[{'art':'blocks','caption':'示意 A'},{'art':'orbits','caption':'示意 B'}]})
def gallery(c,p):
    n=p.get('cols',2)
    return f'<div class="gal" style="grid-template-columns:repeat({n},1fr)">'+''.join(image(c.child((c.w-4*(n-1))/n),dict(x,height=x.get('height',42))) for x in p['items'])+'</div>'

@component('annotated','figure','定位标注图','需要解释同一图上的 2–6 个位置','标注必须对应真实部件','src; items:[{x:0..100,y:0..100,title,text}]; height?',{'art':'network','items':[{'x':25,'y':40,'title':'标注一','text':'对应画面中的位置。'},{'x':72,'y':65,'title':'标注二','text':'说明与图同页阅读。'}],'height':70})
def annotated(c,p):
    pins=''
    for i,x in enumerate(p['items']):
        if not 0<=x['x']<=100 or not 0<=x['y']<=100:raise ValueError('标注坐标范围为 0–100')
        pins+=f'<span class="pin" style="left:{x["x"]}%;top:{x["y"]}%">{i+1}</span>'
    return f'<div class="pins"><div class="fi" style="height:{p.get("height",70)}mm">{_visual(c,p)}{pins}</div><ol>'+''.join(f'<li><b>{I(x["title"])}</b>{I(x["text"])}</li>' for x in p['items'])+'</ol></div>'

@component('chart','figure','数据图表十八种','存在可核对的量化关系','无原始数值不得反推漂亮图','data: chart request; title?; source; takeaway?',{'title':'类别比较（示例）','data':charts.sample('bar'),'source':'虚构数据，仅用于组件展示。'})
def chart(c,p):
    if not p.get('source'):raise ValueError('chart 必须提供 source 说明数据出处')
    return f'<figure class="card chart"><h3 class="ch">{I(p.get("title",""))}</h3>{charts.make(p["data"],c.pal)}<figcaption class="cap">{I(p["source"])}</figcaption>'+(f'<p class="tk">{I(p["takeaway"])}</p>' if p.get('takeaway') else '')+'</figure>'

@component('art','figure','程序插画七种','装饰、主题隐喻、章节节奏','不可替代数据图、地图或产品实录','kind?; height?; seed?; caption?',{'kind':'contours','height':75,'caption':'装饰插画，不承载项目事实。'})
def artwork(c,p):return image(c,{'art':p.get('kind',c.style['art']),'height':p.get('height',75),'seed':p.get('seed',c.seed),'caption':p.get('caption','装饰插画'),'fit':'cover'})
