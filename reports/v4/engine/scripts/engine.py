"""JSON → registered components → self-contained HTML → measured pagination → PDF.

Never shortens content to make it fit. Splits paragraphs, source units, lists and tables.
Oversized atomic charts/images/layouts fail with an actionable error.
"""
import argparse,copy,json,os,re,sys,logging,hashlib
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import components
from core import REG,KNOBS,Ctx,resolve_style,resolve_palette,render_block,esc,inline,plain
from css import freeze
from coverage import check as coverage_check,walk,norm

logging.getLogger('weasyprint').setLevel(logging.ERROR)

def _json(ref,base):
    return json.loads((base/ref).read_text(encoding='utf-8')) if isinstance(ref,str) else ref

def load_spec(path):
    path=Path(path).resolve();s=json.loads(path.read_text(encoding='utf-8'))
    if s.get('version')!=2:raise ValueError('spec.version 必须为 2；旧模板不能直接充当内容输入')
    if not s.get('document',{}).get('title'):raise ValueError('document.title 必填')
    if s['document'].get('mode','compose') not in ('compose','reflow'):raise ValueError('document.mode 只能是 compose / reflow')
    if s.get('cover'):
        cover=dict(s['cover']);kind=cover.pop('kind',resolve_style(s.get('style'))['cover']);cover.setdefault('title',s['document']['title']);cover['type']='cover.'+kind
        s['pages']=[{'id':'cover','component':cover}]+s.get('pages',[]);s.pop('cover')
    if not s.get('pages'):raise ValueError('至少需要一页内容')
    ids=[p.get('id') for p in s['pages']]
    if any(not x or not re.fullmatch(r'[A-Za-z][\w-]*',x) for x in ids) or len(set(ids))!=len(ids):raise ValueError('pages[].id 必须为唯一的字母开头标识')
    for p in s['pages']:
        if p.get('header') and p['header'] not in KNOBS['header']:raise ValueError(f'未知页头 {p["header"]}')
        if p.get('component') and not p['component'].get('type','').startswith(('cover.','page.')):raise ValueError('pages[].component 只用于 cover.* / page.* 整页构图')
        for b in walk(p.get('blocks',[])):
            if b.get('type','').startswith(('cover.','page.')):raise ValueError('整页构图放 pages[].component，不嵌在普通正文块内')
    invref=s.get('inventory',{})
    inventory=_json(invref,path.parent) or {}
    if s['document'].get('mode')=='reflow' and not inventory.get('units'):raise ValueError('重排已有文件必须先建立 inventory.json')
    if inventory and not inventory.get('inventory_reviewed'):raise ValueError('先逐页核对 inventory 与原 PDF，补齐矢量图/表格/脚注，再设 inventory_reviewed=true')
    invbase=(path.parent/invref).resolve().parent if isinstance(invref,str) else path.parent
    for u in inventory.get('units',[]):
        if 'asset' in u:u['asset']=str((invbase/u['asset']).resolve())
    unitids=[u['id'] for u in inventory.get('units',[])]
    if len(set(unitids))!=len(unitids):raise ValueError('inventory 单元 id 重复')
    s['_inventory']=inventory;s['_base']=str(path.parent)
    facts=_json(s.get('facts',[]),path.parent) or []
    factids=[f['id'] for f in facts]
    if len(set(factids))!=len(factids):raise ValueError('facts.id 重复')
    for f in facts:
        if not f.get('display') or not f.get('source') or not f.get('context') or f.get('status') not in ('observed','planned','estimated'):raise ValueError('事实须含 id/display/context/source/status(observed|planned|estimated)')
    s['_facts']=facts
    for b in walk(s['pages']):
        if 'type' in b and b['type'] not in REG:raise ValueError(f'未知组件 {b["type"]}；运行 catalog.py 查可选组件')
        for fid in b.get('fact_ids',[]):
            if fid not in factids:raise ValueError(f'未知 fact_ids {fid}')
    cv=coverage_check(s,inventory)
    if cv['errors']:raise ValueError('内容完整性预检失败：\n'+'\n'.join(cv['errors'][:20]))
    return s

def _context(s):
    st=resolve_style(s.get('style'));pal=resolve_palette(st['palette']);c=Ctx(pal,st,s['_base'],report={'missing':[],'warn':[]},seed=s.get('seed',7));c.inventory={u['id']:u for u in s['_inventory'].get('units',[])};c.facts={f['id']:f for f in s['_facts']};return c

def html_document(s,pages=None):
    c=_context(s);pages=pages if pages is not None else s['pages'];out=[]
    css=freeze((ROOT/'design/base.css').read_text(),c.style,c.pal)
    attrs=' '.join(f'data-{k}="{esc(v)}"' for k,v in c.style.items() if k!='palette' and isinstance(v,str))
    for i,p in enumerate(pages):
        c.page=p['id'];comp=p.get('component');kind=comp.get('type','') if comp else '';cover=kind.startswith('cover.');full=kind.startswith('page.')
        cls='sheet page'+(' cover-sheet' if cover else ' full-sheet' if full else '')
        if comp:body=render_block(c,comp);head=''
        else:
            hp={k:p[k] for k in ('title','kicker','number','lead','answer') if k in p}
            if p.get('continued'):hp['title']=p.get('title','')+' · 续'
            ht=p.get('header',c.style['header']);head=components.pages.header(c,hp,ht) if hp.get('title') else ''
            body=''.join(render_block(c,b) for b in p.get('blocks',[]))
        footer='' if cover else f'<footer class="footer"><span class="footer-title">{inline(s["document"]["title"])}</span><span>{i+1} / {len(pages)}</span></footer>'
        out.append(f'<section class="{cls}" data-page="{esc(p["id"])}"><main class="main">{head}<div class="body-content">{body}</div></main>{footer}</section>')
    if c.report['missing']:raise ValueError('缺少素材：'+', '.join(c.report['missing']))
    return f'<!doctype html><html lang="zh-CN" {attrs}><head><meta charset="utf-8"><title>{esc(s["document"]["title"])}</title><style>{css}</style></head><body>'+''.join(out)+'</body></html>',c.report

def render(s,pages):
    from weasyprint import HTML
    h,report=html_document(s,pages);doc=HTML(string=h,base_url=s['_base']).render();report['missing_text']=missing_visible_text(doc,h);return doc,h,report

def _boxes(box):
    yield box
    for ch in getattr(box,'children',[]):yield from _boxes(ch)

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.skip=0;self.chunks=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('head','svg'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('head','svg'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.chunks.append(data)

def missing_visible_text(doc,html):
    parser=VisibleText();parser.feed(html)
    laid_out=norm(''.join(getattr(b,'text','') for page in doc.pages for b in _boxes(page._page_box)))
    return [x for x in parser.chunks if norm(x) not in laid_out]

def measurements(doc):
    results=[]
    for page in doc.pages:
        bs=list(_boxes(page._page_box));sheet=next((b for b in bs if b.element is not None and 'sheet' in b.element.get('class','').split()),None)
        if sheet is None:continue
        main=next(b for b in bs if b.element is not None and b.element.get('class')=='main')
        # The absolute main is atomic: its full natural height is measured without fragmentation.
        limit=sheet.content_box_y()+sheet.height
        if 'cover-sheet' in sheet.element.get('class',''):limit=sheet.position_y+297*96/25.4
        overflow=max(0,main.position_y+main.height-limit)
        mainboxes=list(_boxes(main))
        for b in mainboxes:
            if getattr(b,'text',None):overflow=max(overflow,b.position_y+b.height-limit)
        if 'cover-sheet' in sheet.element.get('class',''):
            def hasclass(b,cls):return b.element is not None and cls in b.element.get('class','').split()
            copybox=next((b for b in mainboxes if hasclass(b,'cover-copy')),None)
            anchors=[b.position_y for b in mainboxes if hasclass(b,'cover-meta') or hasclass(b,'statrow')]
            if copybox and anchors:overflow=max(overflow,copybox.position_y+copybox.height-min(anchors)+8)
        sideways=[]
        for b in bs:
            if getattr(b,'element_tag',None) in ('p','h1','h2','h3','td','th','figure','img') and b.element is not None:
                # Cover art and band headers intentionally reach physical page edges.
                if b.position_x < -1 or b.position_x+b.width > 210*96/25.4+1:sideways.append(b.element_tag)
        results.append({'id':sheet.element.get('data-page'),'overflow_mm':round(overflow*25.4/96,3),'horizontal_overflow':sorted(set(sideways)),'used_mm':round(main.height*25.4/96,2)})
    return results

def _split_text(text):
    if len(text)<2:return None
    mid=len(text)//2;breaks=[m.end() for m in re.finditer(r'[。！？；\n.!?;]\s*',text)]
    cut=min((v for v in breaks if 0<v<len(text)),key=lambda n:abs(n-mid),default=mid)
    return text[:cut],text[cut:]

def split_block(block,inventory):
    b={'type':'p','text':block} if isinstance(block,str) else copy.deepcopy(block)
    t=b['type']
    key={'source':'ids','list':'items','cards':'items','stack':'blocks','table':'rows','matrix':'rows','timeline':'items'}.get(t)
    if key and len(b.get(key,[]))>1:
        n=len(b[key])//2;a,z=copy.deepcopy(b),copy.deepcopy(b);a[key],z[key]=b[key][:n],b[key][n:];return a,z
    if t=='p':
        parts=_split_text(b['text'])
        if parts:return dict(b,text=parts[0]),dict(b,text=parts[1])
    if t=='source' and len(b.get('ids',[]))==1:
        sid=b['ids'][0];u=inventory[sid]
        if u['kind']=='text':
            text=b.get('fragments',{}).get(sid,u['text']);parts=_split_text(text)
            if parts:
                a,z=copy.deepcopy(b),copy.deepcopy(b);a['fragments']={sid:parts[0]};z['fragments']={sid:parts[1]};return a,z
    return None

def paginate(s):
    final=[];inv={u['id']:u for u in s['_inventory'].get('units',[])}
    for original in s['pages']:
        if original.get('component'):
            d,_,rp=render(s,[original]);m=measurements(d)
            if len(d.pages)!=1 or m[0]['overflow_mm']>1 or m[0]['horizontal_overflow'] or rp['missing_text']:raise ValueError(f'{original["id"]} 整页组件溢出或正文漏排；减少封面字段、缩短主标题或换构图，正文移到续页，禁止删信息')
            final.append(copy.deepcopy(original));continue
        queue=copy.deepcopy(original.get('blocks',[]));current=dict(original,blocks=[]);seq=0;steps=0
        while queue:
            steps+=1
            if steps>1000:raise ValueError('分页超过 1000 次，请检查过大原子组件')
            b=queue.pop(0);trial=dict(current,blocks=current['blocks']+[b]);doc,_,rp=render(s,[trial]);m=measurements(doc)
            fits=len(doc.pages)==1 and m and m[0]['overflow_mm']<=.6 and not m[0]['horizontal_overflow'] and not rp['missing_text']
            if fits:current=trial;continue
            if current['blocks']:
                final.append(current);seq+=1;current={k:v for k,v in original.items() if k not in ('lead','answer','number')};current.update(id=original['id']+f'-cont-{seq}',continued=True,blocks=[]);queue.insert(0,b);continue
            split=split_block(b,inv)
            if not split:raise ValueError(f'{original["id"]} 的 {b.get("type") if isinstance(b,dict) else "p"} 超过单页容量；拆成子图/连续表，调整图高或改为通栏。禁止缩字、裁切或删除正文。测量：{m}')
            queue=list(split)+queue
        if current['blocks'] or not original.get('blocks'):final.append(current)
    # Resolve cross references from final physical page order.
    targets={p['id']:i+1 for i,p in enumerate(final)}
    s['_targets']=targets
    return final

def contact(pdf,out,thumb_width=200):
    import fitz
    from PIL import Image,ImageDraw
    doc=fitz.open(pdf);cols=min(4,len(doc));rows=(len(doc)+cols-1)//cols;tileh=int(thumb_width*297/210)+25
    sheet=Image.new('RGB',(cols*(thumb_width+12),rows*tileh),'#dededb');draw=ImageDraw.Draw(sheet)
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(thumb_width/page.rect.width,thumb_width/page.rect.width),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);x=(i%cols)*(thumb_width+12)+6;y=(i//cols)*tileh+5;sheet.paste(im,(x,y));draw.text((x,y+im.height+3),str(i+1),fill='black')
    sheet.save(out)

def build(path,output):
    import fitz
    s=load_spec(path);out=Path(output).resolve();out.parent.mkdir(parents=True,exist_ok=True);pages=paginate(s);doc,h,render_report=render(s,pages)
    for target in set(re.findall(r'data-target="([^"]+)"',h)):
        if target not in s['_targets']:raise ValueError(f'目录指向未知页 {target}')
        h=h.replace(f'data-target="{target}">—',f'data-target="{target}">{s["_targets"][target]}')
    from weasyprint import HTML
    doc=HTML(string=h,base_url=s['_base']).render();ms=measurements(doc)
    dropped=missing_visible_text(doc,h)
    if len(doc.pages)!=len(pages) or any(m['overflow_mm']>1 or m['horizontal_overflow'] for m in ms) or dropped:raise ValueError('最终分页/溢出/漏排检查失败：'+str(ms)+'，漏排文字：'+str(dropped[:3]))
    out.with_suffix('.html').write_text(h,encoding='utf-8');doc.write_pdf(out)
    pdf=fitz.open(out);text='\n'.join(p.get_text() for p in pdf);public={k:v for k,v in s.items() if not k.startswith('_')};public['pages']=pages
    cv=coverage_check(public,s['_inventory'],text)
    factcheck=[]
    for f in s['_facts']:
        used=any(f['id'] in b.get('fact_ids',[]) for b in walk(pages))
        if used and norm(plain(f['display'])) not in norm(text):cv['errors'].append(f'事实 {f["id"]} 的 display 未出现在 PDF：{f["display"]}')
        factcheck.append({'id':f['id'],'used':used,'status':f['status'],'source':f['source']})
    report={'pages':len(pdf),'style':s.get('style',{}),'measurements':ms,'coverage':cv,'facts':factcheck,'missing_text':dropped,'warnings':render_report['warn'],'source_sha256':s['_inventory'].get('source',{}).get('sha256'),'note':'自动检查证明结构覆盖、精确原文和版面边界；改写语义、数据口径、图片完整性仍须逐页目视核对。'}
    out.with_suffix('.audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');out.with_suffix('.pages.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8');contact(out,out.with_suffix('.contact.jpg'))
    if cv['errors']:raise ValueError('PDF 已生成但内容核对未通过，不可交付：\n'+'\n'.join(cv['errors']))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('spec');ap.add_argument('output');a=ap.parse_args()
    try:r=build(a.spec,a.output);print(json.dumps({'output':str(Path(a.output).resolve()),'pages':r['pages'],'coverage':r['coverage']},ensure_ascii=False))
    except (ValueError,KeyError,FileNotFoundError) as e:print(f'构建未通过：{e}',file=sys.stderr);sys.exit(1)
