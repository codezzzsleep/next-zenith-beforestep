"""Archive immutable crossing checkpoint members while generation continues."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ops.crossing_development_evidence import bundle

def collect(name):
    indexfile=ROOT/'evidence/crossing/development/narrow-generator-index.json'
    index=json.loads(indexfile.read_text());archives=index.get('archives',[index['archive']])
    previous={r['path']:r['sha256'] for a in archives for r in a['members']}
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    files=[];complete=[]
    def add(directory):
        directory=Path(directory)
        if directory.is_file():files.append(directory)
        elif directory.is_dir():files.extend(p for p in directory.rglob('*') if p.is_file() and p.suffix not in ['.tmp','.lock','.part'])
    for folder in (ROOT/'outputs/crossing/development/scene-dev-v9').glob('seed-*'):
        add(folder/'observation/gen');add(folder/'observation/lux_request.json');add(folder/'lux-source')
        for sample in (folder/'admission-by-sample').glob('*'):
            if (sample/'target_decision.json').exists():add(sample)
        if (folder/'lux-development.json').exists():
            add(folder/'lux-development.json');add(folder/'observation/lux_result.json');add(folder/'decision')
            add(ROOT/f'evidence/crossing/development-lux-scene-dev-v9-{folder.name[5:]}.json')
            complete.append(int(folder.name[5:]))
        method=folder/'method-D-v1'
        if (method/'result.json').exists():add(method)
        else:
            for result in (method/'rehearsal').glob('*/result.json'):add(result.parent)
    for job in budget['tasks']:
        if job['scene'].startswith('scene-dev-v9/') and job['status']=='ok':
            glb=ROOT/job['glb'];assert glb.is_file() and hashlib.sha256(glb.read_bytes()).hexdigest()==job['glb_sha256']
            add(glb.parent)
    for filename in ['development-narrow-summary.json','diagnosis-summary.json']:
        add(ROOT/'evidence/crossing'/filename)
    selected=[]
    for p in sorted(set(files)):
        rel=str(p.relative_to(ROOT))
        if previous.get(rel)!=hashlib.sha256(p.read_bytes()).hexdigest():selected.append(p)
    if not selected:return {'changed_files':0}
    artifact=bundle(name,selected)
    index['archives']=archives+[artifact];index['latest_checkpoint']={'name':name,'created_at_capture':budget['created'],'completed_lux_scenes':complete,'includes_incomplete_experiments':False}
    indexfile.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    return {'changed_files':len(selected),'bytes':artifact['bytes'],'sha_check':artifact['member_sha_check'],'captured_created':budget['created']}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);args=parser.parse_args();print(json.dumps(collect(args.name)))
