"""Development-only world checks; recorded 17-scene sensor fidelity diagnostics."""
import argparse
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from beforestep import scene as S
from beforestep.navigation import map as N
from .common import ROOT,OUT,read,write,sha,finite
from .world import World
from .geometry import scene_height,geometric_observation,camera_at,apply_scene
from .evaluate import run,summarize


def initialize_worker(cfg,library):
    global WORKER_CONFIG,WORKER_LIBRARY
    WORKER_CONFIG=cfg;WORKER_LIBRARY=library


def dev_one(seed):
    w=World(seed,cfg=WORKER_CONFIG,library=WORKER_LIBRARY);rows=[]
    for m in ['optimistic','conservative','see_dark']:
        row,_=run(w,m);rows.append(row)
    w.close()
    return {'manifest':w.manifest(),'rows':rows}


def development(out,count=300,workers=3):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cfg=read(ROOT/'experimental/arena/parameters.json');start=cfg['development']['seed_start']
    libpath=cfg.get('capsule_library','evidence/learning/arena_v2/capsules.json');library=read(ROOT/libpath)
    identity={'status':'running','pid':__import__('os').getpid(),'parameters_sha256':sha(ROOT/'experimental/arena/parameters.json'),'capsule_library':libpath,'capsules_sha256':sha(ROOT/libpath),'count':count,'seed_start':start,'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'experimental/arena').glob('*.py'))}}
    if (out/'identity.json').exists():
        previous=read(out/'identity.json')
        for key in ['parameters_sha256','capsules_sha256','count','seed_start','sources_sha256']:
            assert previous[key]==identity[key],f'Changed development identity: {key}'
        if previous['status']=='complete':return
    write(out/'identity.json',identity)
    seeds=[s for s in range(start,start+count) if not (out/f'{s}.json').exists()]
    with ProcessPoolExecutor(max_workers=workers,initializer=initialize_worker,initargs=(cfg,library)) as pool:
        for i,(seed,result) in enumerate(zip(seeds,pool.map(dev_one,seeds))):
            write(out/f'{seed}.json',result)
            if i%20==0:print('development',i,flush=True)
    rows=[r for seed in range(start,start+count) for r in read(out/f'{seed}.json')['rows']]
    summary=summarize(rows)
    passed=(summary['optimistic']['all']['collision_rate']>=.15 and summary['conservative']['all']['arrival_rate']<=.70 and (summary['see_dark']['reachable']['arrival_rate'] or 0)>=.85)
    write(out/'summary.json',{'passed':passed,'summary':summary})
    identity=read(out/'identity.json');identity['status']='complete';write(out/'identity.json',identity)
    print({'passed':passed,'summary':summary},flush=True)


def real_runs():
    plan=read(ROOT/'evidence/reviews/beforestep_r3/experiment-plan.json')
    for row in plan['frozen']+plan['holdouts']:
        scene=row['scene'];base=ROOT/'outputs/r3/v3/holdouts'/scene/'baselines'
        if not base.exists():
            base=ROOT/'outputs/suite/baselines-crater-target'/scene
            if scene=='stress_v8':base=ROOT/'outputs/review_r1/baselines'
        if not baseline_folder(base,'conservative').exists():
            paths=list((ROOT/'outputs').rglob(scene+'/conservative/summary.json'))
            if not paths:paths=list((ROOT/'outputs').rglob('conservative/summary.json'))
            matches=[p for p in paths if read(p).get('scene_id')==scene and (p.parent/'looks/look1_state.npy').exists()]
            assert matches,scene
            base=matches[0].parent.parent
        yield row,base


def baseline_folder(base,method):
    folder=base/method
    return folder/'run' if (folder/'run/summary.json').exists() else folder


def recorded_camera(folder):
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
    look=next(e for e in events if e['kind']=='look')
    traj=np.load(folder/'traj.npz');idx=int(np.argmin(abs(traj['t']-look['t'])));q=traj['qpos'][idx]
    from scipy.spatial.transform import Rotation
    R=Rotation.from_quat(q[[4,5,6,3]]).as_matrix()
    canonical=camera_at([0,0],0)['R_world_from_camera']
    return {'world_pos':(q[:3]+R@np.array(S.CAM['pos'])).tolist(),'R_world_from_camera':(R@canonical).tolist(),
            'fovy_deg':S.CAM['fovy'],'intrinsics':{'width':1600,'height':1200}},q


def fidelity(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];total=np.zeros((6,6),int)
    for definition,base in real_runs():
        scene=definition['scene'];folder=baseline_folder(base,'conservative');d=read(ROOT/definition['config'])
        d={**d,'sun':S.sun_settings(d)}
        height,ground=scene_height(d,include_walls=True);cam,q=recorded_camera(folder)
        actual=np.load(folder/'looks/look1_state.npy');ob=geometric_observation(height,ground,cam,S.sun_settings(d))
        lane=~N.prior_nogo();conf=np.bincount((actual[lane]*6+ob['state'][lane]).ravel(),minlength=36).reshape(6,6)
        total+=conf;write(out/f'{scene}-state.json',{'scene':scene,'reference':str(folder.relative_to(ROOT)),'reference_sha256':sha(folder/'looks/look1_state.npy'),'lane_cells':int(lane.sum()),'confusion_matrix_reference_rows':conf.tolist(),'agreement':float(np.trace(conf)/conf.sum())})
        # Run shared geometric route logic on the exact original scene, first pose.
        w=object.__new__(World);w.seed=0;w.split='recorded-diagnostic';w.cfg=read(ROOT/'experimental/arena/parameters.json')
        w.start=q[:2];w.heading=float(__import__('scipy').spatial.transform.Rotation.from_quat(q[[4,5,6,3]]).as_euler('xyz')[2]);w.goal=np.array(d['goal'])
        w.definition=d;w.height=height;w.ground=ground;w.raw=height>=N.ROCK_Z;w.truth_occ=w.raw|N.prior_nogo();w.first_camera=cam;w.look_count=0
        w.capsule={'id':scene,'candidates':[]};comp=[]
        for m in ['conservative','optimistic','see_dark']:
            ref=baseline_folder(base,m)/'summary.json'
            result,_=run(w,m);original=read(ref)['result']
            normalized='arrived' if original=='arrived' else 'collision' if original=='collision' else 'stopped'
            comp.append({'method':m,'geometric_result':result['status'],'recorded_result':original,'agree':result['status']==normalized,'reference':str(ref.relative_to(ROOT))})
        rows.append({'scene':scene,'state_agreement':float(np.trace(conf)/conf.sum()),'methods':comp})
        write(out/'progress.json',rows);print(scene,rows[-1],flush=True)
    agreement=float(np.trace(total)/total.sum());matches=sum(c['agree'] for r in rows for c in r['methods'])
    write(out/'summary.json',{'state_agreement':agreement,'confusion_matrix_reference_rows':total.tolist(),'method_matches':matches,'method_comparisons':len(rows)*3,'method_agreement':matches/(len(rows)*3),'scenes':rows,'passed':agreement>=.90 and matches/(len(rows)*3)>=.80})


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['development','fidelity']);a.add_argument('--out',required=True);a.add_argument('--count',type=int,default=300);a.add_argument('--workers',type=int,default=3);args=a.parse_args()
    if args.stage=='development':development(args.out,args.count,args.workers)
    else:fidelity(args.out)
