import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory');ap.add_argument('--title',required=True);ap.add_argument('--preset',default='research');ap.add_argument('--inventory');a=ap.parse_args();out=Path(a.directory).resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'spec.json').exists():raise SystemExit('spec.json 已存在；不覆盖已有内容')
    s={'version':2,'document':{'title':a.title,'mode':'reflow' if a.inventory else 'compose','audience':'项目评审','allow_rewrite':False},'style':{'preset':a.preset},'facts':[],'pages':[]}
    if a.inventory:
        inv=Path(a.inventory).resolve();data=json.loads(inv.read_text());s['inventory']=str(inv);s['pages']=[{'id':f'source-{p}','title':f'原文第 {p} 页','blocks':[{'type':'source','ids':[u['id'] for u in data['units'] if u.get('page')==p]}]} for p in sorted({u.get('page',1) for u in data['units']})]
    (out/'spec.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8');print(out/'spec.json')

if __name__=='__main__':main()
