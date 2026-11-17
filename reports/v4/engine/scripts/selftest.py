"""Integration regression: retained text, multipage tables, strict failures and vector renderers.
Run with an explicit disposable directory: python3 scripts/selftest.py output-directory
"""
import argparse,copy,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import engine,charts,diagram,art,choose,components
from core import resolve_palette,resolve_style,contrast,palettes,REG
from coverage import check,norm

def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);results=[]
    def ok(name,fn):
        fn();results.append(name)
    def fails(fn):
        try:fn()
        except (ValueError,KeyError,FileNotFoundError):return
        raise AssertionError('不合法输入意外通过')
    def vectors():
        p=resolve_palette('midnight')
        for k in charts.KINDS:ET.fromstring(charts.make(charts.sample(k),p))
        for k in diagram.KINDS:ET.fromstring(diagram.make(diagram.sample(k),p))
        for k in art.KINDS:ET.fromstring(art.make(k,900,640,p,seed=7))
        for name in palettes():
            p=resolve_palette(name)
            for fg,bg in [('ink','paper'),('mut','paper'),('accent_ink','paper'),('cover_mut','cover_bg')]:assert contrast(p[fg],p[bg])>=4.49,(name,fg,bg)
    ok('18 charts + 5 diagrams + 7 art SVG; 10 palettes text contrast',vectors)
    ok('invalid values and semantic structure rejected',lambda:[fails(lambda:resolve_style({'palette':'missing'})),fails(lambda:charts.make({'kind':'funnel','labels':['a','b'],'series':[{'name':'x','values':[3,9]}]})),fails(lambda:diagram.make({'kind':'flow','nodes':[{'id':'a','label':'a'},{'id':'b','label':'b'}],'edges':[{'from':'a','to':'b'},{'from':'b','to':'a'}]}))])
    units=[{'id':'u'+str(i),'kind':'text','text':f'第 {i:03d} 个原文单元。'+('须完整保留否定、条件、责任、未定事项，以及 **星号** 与 `符号`。'*10),'required':True} for i in range(24)]
    s={'version':2,'document':{'title':'原文与续表回归验证','mode':'reflow'},'style':{'preset':'research'},'inventory':{'inventory_reviewed':True,'units':units},'pages':[{'id':'source','title':'完整原文','blocks':[{'type':'source','ids':[u['id'] for u in units]}]},{'id':'table','title':'连续明细','blocks':[{'type':'table','columns':['记录号','保留值','状态'],'rows':[[f'ROW-{i:03d}',f'VALUE-{i:03d}','尚未确认' if i%2 else '计划'] for i in range(100)]}]}]}
    f=out/'reflow.json';f.write_text(json.dumps(s,ensure_ascii=False));r=engine.build(f,out/'reflow.pdf')
    def retained():
        import fitz
        assert r['pages']>3 and not r['coverage']['errors']
        text='\n'.join(p.get_text() for p in fitz.open(out/'reflow.pdf'))
        for i in range(100):assert f'ROW-{i:03d}' in text and f'VALUE-{i:03d}' in text
        assert text.count('记录号')>=2
        assert not any(m['overflow_mm']>1 or m['horizontal_overflow'] for m in r['measurements'])
    ok('long source retained verbatim; automatic continuation; repeated table headers; no clipped rows',retained)
    def conservation():
        bad=copy.deepcopy(s);bad['pages'][0]['blocks'][0]['ids'].pop();assert check(bad,bad['inventory'])['errors']
        bad['inventory']['units'][-1]['required']=False;assert check(bad,bad['inventory'])['errors']
        bad=copy.deepcopy(s);bad['pages'][0]['blocks']=[{'type':'p','text':'摘要','source_ids':[u['id'] for u in units]}];assert check(bad,bad['inventory'])['errors']
    ok('missing source / required=false bypass / unauthorized summary rejected',conservation)
    def atoms():
        d={'version':2,'document':{'title':'检查'},'pages':[{'id':'broken','blocks':[{'type':'image','src':'does-not-exist.png'}]}]};p=out/'bad.json';p.write_text(json.dumps(d));fails(lambda:engine.build(p,out/'bad.pdf'))
        d['pages']=[{'id':'cover','component':{'type':'cover.type','title':'超长标题'*120}}];p.write_text(json.dumps(d,ensure_ascii=False));fails(lambda:engine.build(p,out/'bad.pdf'))
    ok('missing image and cover collision rejected',atoms)
    def rules():
        assert choose.choose({'relation':'process','items':3})['chosen']=='list'
        assert choose.choose({'relation':'process','items':5})['chosen']=='process'
        assert choose.choose({'relation':'process','items':2,'branches':True})['chosen']=='diagram.flow'
        assert choose.choose({'relation':'matrix','all_numeric':False})['chosen']=='matrix'
        assert choose.choose({'relation':'chronology','items':7,'has_time':True})['chosen']=='timeline'
        assert choose.choose({'relation':'schedule','start_end':False})['chosen']=='roadmap'
        assert choose.cover({})['chosen']=='cover.type'
    ok('relationship decisions and no-data cover fallback',rules)
    (out/'results.json').write_text(json.dumps({'passed':results,'pages':r['pages']},ensure_ascii=False,indent=2));return results

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('directory');v=a.parse_args();r=run(v.directory);print(json.dumps({'passed':r},ensure_ascii=False,indent=2))
