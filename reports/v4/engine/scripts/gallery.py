"""Executable component examples, never a fixed content template.
Default: covers + representative pages + all 18 chart types. --all: entire registry.
"""
import argparse,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import components,charts
from core import REG
from engine import build

def spec(all_components=False,preset='culture-guide'):
    pages=[]
    for name in ['cover.horizon','cover.poster','cover.type','cover.split','cover.numbers','cover.frame','cover.mosaic']:
        pages.append({'id':name.replace('.','-'),'component':dict(copy.deepcopy(REG[name].sample),type=name)})
    if all_components:
        for name,co in REG.items():
            if co.kind=='cover':continue
            sample=dict(copy.deepcopy(co.sample),type=name)
            if name=='source':sample['ids']=['demo-source']
            if co.kind=='page':page={'id':'component-'+name.replace('.','-'),'component':sample}
            else:page={'id':'component-'+name.replace('.','-'),'title':co.title,'kicker':name,'lead':co.use,'blocks':[sample,{'type':'callout','variant':'note','text':co.avoid or '按内容选择，不要求每份文档都使用。'}]}
            pages.append(page)
    else:
        for name in ['page.editorial','page.statement']:
            pages.append({'id':name.replace('.','-'),'component':dict(copy.deepcopy(REG[name].sample),type=name)})
        groups=[('信息层级',['lead','metrics','callout','cards']),('证据与说明',['evidence','failure','quote']),('关系与过程',['process','layers','converge']),('时间与阶段',['timeline-horizontal','roadmap']),('精确比较',['matrix','budget'])]
        for i,(title,names) in enumerate(groups):pages.append({'id':'group-'+str(i),'title':title,'kicker':'COMPONENT STUDY','blocks':[dict(copy.deepcopy(REG[n].sample),type=n) for n in names]})
    for i,k in enumerate(charts.KINDS):
        if i%2==0:pages.append({'id':'charts-'+str(i//2),'title':'图表选择 · '+str(i//2+1),'kicker':'CHART STUDY','blocks':[]})
        pages[-1]['blocks'].append({'type':'chart','title':k,'data':charts.sample(k),'source':'虚构数据，仅用于组件展示。'})
    if all_components:
        for target in ['context','evidence','next']:pages.append({'id':target,'title':{'context':'问题与背景','evidence':'方法与证据','next':'计划与边界'}[target],'blocks':[{'type':'p','text':'这是目录定位示例页；实际文档不保留示例内容。'}]})
    return {'version':2,'document':{'title':'项目书设计系统 · 组件与选择示例','mode':'compose'},'style':{'preset':preset},'inventory':{'inventory_reviewed':True,'units':[{'id':'demo-source','kind':'text','text':'原文块示例：完整保留内容与限定条件。','required':True}] if all_components else []},'pages':pages}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--all',action='store_true');a.add_argument('--preset',default='culture-guide');a.add_argument('--diverse-covers',action='store_true',help='将七种构图分别用不同预设渲染，合成可比较样张');v=a.parse_args();out=Path(v.output).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if v.diverse_covers:
        import fitz
        folder=out.parent/(out.stem+'-parts');folder.mkdir(exist_ok=True);base=spec(v.all,v.preset);merged=fitz.open()
        themes=['culture-guide','ai-product','engineering','brand-creative','tech-lab','heritage','public-good']
        covers=base['pages'][:7]
        for i,(pg,theme) in enumerate(zip(covers,themes)):
            request={'version':2,'document':base['document'],'style':{'preset':theme},'pages':[pg]};inp=folder/f'cover-{i}.json';inp.write_text(json.dumps(request,ensure_ascii=False,indent=2));target=inp.with_suffix('.pdf');build(inp,target)
            with fitz.open(target) as pdf:merged.insert_pdf(pdf)
        body=copy.deepcopy(base);body['pages']=body['pages'][7:];inp=folder/'body.json';inp.write_text(json.dumps(body,ensure_ascii=False,indent=2));target=folder/'body.pdf';r=build(inp,target)
        with fitz.open(target) as pdf:merged.insert_pdf(pdf)
        merged.save(out,garbage=4,deflate=True);r['pages']=len(merged)
        from engine import contact
        contact(out,out.with_suffix('.contact.jpg'))
    else:
        inp=out.with_suffix('.spec.json');inp.write_text(json.dumps(spec(v.all,v.preset),ensure_ascii=False,indent=2),encoding='utf-8');r=build(inp,out)
    print(json.dumps({'pages':r['pages'],'pdf':str(out)},ensure_ascii=False))
