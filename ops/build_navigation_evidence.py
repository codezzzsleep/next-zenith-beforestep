"""Publish completed navigation runs without training, inference or API calls."""
import collections
import hashlib
import json
import math
from pathlib import Path
import shutil

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/learning'
TARGET=ROOT/'evidence/learning/navigation_v1'
DATA=ROOT/'site/data/navigation'


def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def wilson(success,total):
    if not total:return [0.,1.]
    z=1.959963984540054;p=success/total;d=1+z*z/total
    center=(p+z*z/(2*total))/d
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [center-half,center+half]


def aggregate(rows):
    result={}
    for method in sorted({r['method'] for r in rows}):
        part=[r for r in rows if r['method']==method]
        reachable=[r for r in part if r['oracle_reachable']]
        n=len(part);k=sum(r['status']=='arrived' for r in part)
        result[method]={'episodes':n,'arrived':k,'success_rate':k/n,
          'success_wilson_95':wilson(k,n),'statuses':dict(collections.Counter(r['status'] for r in part)),
          'reachable':len(reachable),'reachable_arrived':sum(r['status']=='arrived' for r in reachable),
          **{'mean_'+field:float(np.mean([r[field] for r in part])) for field in
             ['path_length_m','panorama_looks','passive_observations','planning_wall_seconds']}}
    return result


def copy_run(name,destination,require_complete=True):
    source=SOURCE/name
    if require_complete and read(source/'identity.json')['stage']!='complete':
        raise RuntimeError('Run is still active: '+name)
    for path in sorted(source.rglob('*')):
        if not path.is_file():continue
        if path.suffix not in ('.json','.pt','.npz','.obj','.png','.py','.txt'):raise ValueError('Unexpected artifact '+str(path))
        target=destination/path.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and digest(target)!=digest(path):
            raise ValueError('Preserve existing published evidence: '+str(target))
        shutil.copy2(path,target)
    log=SOURCE/(name+'.log')
    if log.exists():shutil.copy2(log,destination/'execution.log')


def paired(rows):
    lookup={(r['seed'],r['method']):r for r in rows};out=collections.Counter()
    for seed in sorted({r['seed'] for r in rows}):
        a=lookup[(seed,'learned')]['status']=='arrived'
        b=lookup[(seed,'rules_cached_prior')]['status']=='arrived'
        out['both_arrive' if a and b else 'learned_only' if a else 'rules_only' if b else 'neither_arrives']+=1
    return dict(out)


def compact(world,rows,physical=False,base=None):
    episodes={}
    for row in rows:
        if physical:
            trajectory=base/f"{row['seed']}-{row['method']}"/'trajectory.npz'
            with np.load(trajectory,allow_pickle=False) as f:
                q=f['qpos_time']
                if len(q):
                    indices=np.unique(np.r_[np.arange(0,len(q),max(1,len(q)//1000)),len(q)-1])
                    points=q[indices,1:3];times=q[indices,0]-q[0,0]
                else:points=np.empty((0,2));times=np.empty(0)
        else:
            points=np.asarray(row['trace_cells'])*world['resolution_m'];times=np.arange(len(points))
        episodes[row['method']]={k:row[k] for k in ['status','goal_error_m','path_length_m','panorama_looks','planning_wall_seconds']}
        episodes[row['method']].update(trace_m=points.tolist(),time=times.tolist(),
                                      sim_seconds=row.get('sim_seconds'),collision=row.get('collision'))
    return {'world':world,'episodes':episodes,'mode':'physical' if physical else 'planar'}


def plots(history,stats):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'svg.fonttype':'none','font.size':10})
    output=ROOT/'site/media/navigation';output.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(7.2,3.2),layout='constrained')
    ax.plot([r['epoch'] for r in history],[r['train_loss'] for r in history],label='Training')
    ax.plot([r['epoch'] for r in history],[r['validation_loss'] for r in history],label='Validation')
    ax.set(xlabel='Epoch',ylabel='Supervised loss');ax.legend();ax.grid(alpha=.2)
    fig.savefig(output/'training.svg');plt.close(fig)
    names=['learned','rules_cached_prior','learned_no_prior','untrained','rules_optimistic','rules_conservative']
    labels=['Trained network','Cached-prior rules','Network without prior','Untrained network','Optimistic rules','Conservative rules']
    fig,axes=plt.subplots(1,2,figsize=(10.5,4),layout='constrained',sharey=True)
    for ax,split in zip(axes,['test','ood']):
        for i,name in enumerate(names):
            row=stats[split][name];lo,hi=row['success_wilson_95'];p=row['success_rate']
            ax.barh(i,p*100,color='#8fa3b8' if name=='learned' else '#c9b89d')
            ax.errorbar(p*100,i,xerr=np.array([[p-lo],[hi-p]])*100,fmt='none',ecolor='#333',capsize=3)
        ax.set_yticks(range(len(names)),labels);ax.invert_yaxis();ax.set(xlim=(0,106),xlabel='Arrivals / all tasks (%)',title=split.upper()+' (128 new layouts)')
        ax.grid(axis='x',alpha=.2)
    fig.savefig(output/'heldout.svg');plt.close(fig)


def main():
    runs={'training':'navigation_v1','validation':'navigation_v1-validation','heldout':'navigation_v1-heldout',
      'physics':'navigation_v1-physics','physics-start-v2':'navigation_v1-physics-start-v2',
      'physics-start-v2-validation':'navigation_v1-physics-start-v2-validation',
      'llm-first':'navigation_v1-llm','llm-fixed':'navigation_v1-llm-fixed',
      'physics-validation-first':'navigation_v1-physics-validation',
      'physics-validation-fixed':'navigation_v1-physics-validation-fixed'}
    # Check all mandatory terminal identities before publishing any partial report.
    for key,name in runs.items():
        if 'validation' in key and key!='validation':continue
        if read(SOURCE/name/'identity.json')['stage']!='complete':raise RuntimeError('Incomplete '+name)
    for key,name in runs.items():copy_run(name,TARGET/key,not ('validation' in key and key!='validation'))
    training=read(TARGET/'training/identity.json');heldout=read(TARGET/'heldout/identity.json')
    assert training['best_sha256']==heldout['model_sha256']==digest(TARGET/'training/best.pt')
    for filename,expected in heldout['navigation_sources'].items():
        assert digest(ROOT/'experimental/navigation'/filename)==expected,filename
    weights=ROOT/'assets/models/navigation_v1';weights.mkdir(parents=True,exist_ok=True)
    for name in ['best.pt','untrained.pt']:shutil.copy2(TARGET/'training'/name,weights/name)
    write(weights/'identity.json',{'revision':'navigation_v1','training_identity':'evidence/learning/navigation_v1/training/identity.json',
                                 'model_sha256':heldout['model_sha256'],'value_iterations':48})
    groups={};all_seeds={};viewer=[];pairings={}
    for split in ['validation','test','ood']:
        base=TARGET/('validation' if split=='validation' else 'heldout')
        rows=[read(p) for p in sorted((base/'episodes').glob('*.json'))]
        config=read(ROOT/'config/training/navigation_v1.json')[split]
        seeds=set(range(config['seed_start'],config['seed_start']+config['count']))
        rows=[r for r in rows if r['seed'] in seeds]
        assert len(rows)==len(seeds)*6 and {r['seed'] for r in rows}==seeds
        groups[split]=aggregate(rows);all_seeds[split]=seeds;pairings[split]=paired(rows)
        if split=='validation':continue
        for seed in sorted(seeds):
            world=read(base/'scenes'/f'{seed}.json');part=[r for r in rows if r['seed']==seed]
            file=f'{split}/{seed}.json';write(DATA/file,compact(world,part))
            viewer.append({'seed':seed,'split':split,'file':file,'reachable':world['oracle_reachable'],
                           'learned_status':next(r['status'] for r in part if r['method']=='learned')})
    physics=read(TARGET/'physics/results.json');groups['physical']=aggregate(physics);pairings['physical']=paired(physics)
    all_seeds['physical']={r['seed'] for r in physics}
    assert len(physics)==16 and len(all_seeds['physical'])==8
    for seed in sorted(all_seeds['physical']):
        world=read(TARGET/'physics/scenes'/f'{seed}.json');part=[r for r in physics if r['seed']==seed]
        file=f'physical/{seed}.json';write(DATA/file,compact(world,part,True,TARGET/'physics'))
        viewer.append({'seed':seed,'split':'physical','file':file,'reachable':world['oracle_reachable'],
                       'learned_status':next(r['status'] for r in part if r['method']=='learned')})
    all_seeds['train']={r['seed'] for r in read(TARGET/'training/train-scenes.json')}
    repaired=read(TARGET/'physics-start-v2/results.json');groups['physical_start_v2']=aggregate(repaired)
    pairings['physical_start_v2']=paired(repaired);all_seeds['physical_start_v2']={r['seed'] for r in repaired}
    assert len(repaired)==16 and len(all_seeds['physical_start_v2'])==8
    for seed in sorted(all_seeds['physical_start_v2']):
        world=read(TARGET/'physics-start-v2/scenes'/f'{seed}.json');part=[r for r in repaired if r['seed']==seed]
        file=f'physical_start_v2/{seed}.json';write(DATA/file,compact(world,part,True,TARGET/'physics-start-v2'))
        viewer.append({'seed':seed,'split':'physical_start_v2','file':file,'reachable':world['oracle_reachable'],
                       'learned_status':next(r['status'] for r in part if r['method']=='learned')})
    for a,sa in all_seeds.items():
        for b,sb in all_seeds.items():
            if a!=b:assert not sa & sb,(a,b)
    llm={}
    total_calls=0
    for key in ['llm-first','llm-fixed']:
        base=TARGET/key;calls=[read(p) for p in sorted((base/'calls').glob('*.json'))]
        rows=[read(p) for p in sorted((base/'episodes').glob('*.json'))]
        assert all(r['status']!='created' for r in calls)
        total_calls+=len(calls)
        llm[key]={'requests':len(calls),'call_statuses':dict(collections.Counter(r['status'] for r in calls)),
                  'errors':dict(collections.Counter(r.get('error','') for r in calls if r['status']!='ok')),
                  'model':read(base/'identity.json')['model'],'outcomes':aggregate(rows),
                  'decision_sources':dict(collections.Counter(d['source'] for r in rows if r['method']=='rules_llm' for d in r['decisions']))}
    assert total_calls<=32
    result={'schema':'beforestep-learned-navigation-result/v1','model_sha256':heldout['model_sha256'],
            'training':training,'results':groups,'paired_arrivals':pairings,'llm':llm,'total_llm_requests':total_calls,
            'new_lux_tasks':0,'seed_disjointness_verified':True,
            'scope':'Cached 27 scan/Lux shape pairs in new layouts; 0.30m planar sensing. Physical runs use convex footprint extrusions and learned_v4 motor control.'}
    write(TARGET/'result.json',result)
    write(DATA/'index.json',{'result':'evidence/learning/navigation_v1/result.json','scenes':viewer,'summary':groups,
                            'model_sha256':heldout['model_sha256'],'new_lux_tasks':0})
    plots(read(TARGET/'training/history.json'),groups)
    custody=[]
    for directory in [TARGET,weights,DATA,ROOT/'site/media/navigation']:
        for p in sorted(directory.rglob('*')):
            if p.is_file() and p.name!='custody.json':custody.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)})
    write(TARGET/'custody.json',{'files':custody,'file_count':len(custody),'total_bytes':sum(r['bytes'] for r in custody),
                                'original_outputs_preserved':True,'new_training_or_service_calls':0})
    print(json.dumps({'result':str(TARGET/'result.json'),'files':len(custody),'bytes':sum(r['bytes'] for r in custody),'llm_requests':total_calls}))


if __name__=='__main__':main()
