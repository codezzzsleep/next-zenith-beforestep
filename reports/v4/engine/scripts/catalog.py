"""Registry-derived catalog: fields, defaults, examples, uses and avoidances."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import components,charts,diagram,art
from core import REG,KINDS,KNOBS,palettes,presets

def catalog(kind=None):
    items=[{'type':x.name,'kind':x.kind,'title':x.title,'use':x.use,'avoid':x.avoid,'fields':x.fields,'example':dict(x.sample,type=x.name)} for x in REG.values() if kind is None or x.kind==kind]
    return {'component_count':len(REG),'components':items,'chart_types':list(charts.KINDS),'diagram_types':list(diagram.KINDS),'art_types':list(art.KINDS),'knobs':KNOBS,'palettes':list(palettes()),'presets':list(presets())}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=list(KINDS));ap.add_argument('--output');a=ap.parse_args();s=json.dumps(catalog(a.kind),ensure_ascii=False,indent=2)
    if a.output:Path(a.output).write_text(s,encoding='utf-8')
    else:print(s)
