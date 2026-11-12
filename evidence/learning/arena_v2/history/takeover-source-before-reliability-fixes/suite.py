"""Preregistered paired evaluations. Completed episodes are never rerun."""
from pathlib import Path
import os,time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import torch
from .common import ROOT,OUT,read,write,sha,finite
from .world import World
from .model import load
from .evaluate import run,summarize

RULES=['conservative','optimistic','imagination','strict','see_dark']


def one(seed,split,out,lux,no_lux,thresholds=None,chosen=None):
    torch.set_num_threads(1);out=Path(out);folder=out/str(seed);folder.mkdir(parents=True,exist_ok=True)
    w=World(seed,split);write(folder/'world.json',w.manifest());models={'learned':load(lux),'learned_no_lux':load(no_lux)};rows=[]
    grid=thresholds if thresholds is not None else [None]
    try:
        for method in [*RULES,'learned','learned_no_lux']:
            for threshold in (grid if method.startswith('learned') else [None]):
                t=threshold if threshold is not None else chosen.get(method,.1) if chosen else .1
                name=method+(f'-t{t}' if thresholds is not None and method.startswith('learned') else '')
                result=folder/f'{name}.json'
                if result.exists():rows.append(read(result));continue
                archive=folder/f'{name}-maps.npz'
                if archive.exists():
                    with np.load(archive) as stored:row=__import__('json').loads(str(stored['result']))
                    write(result,row);rows.append(row);continue
                row,data=run(w,method,models.get(method),t);row['threshold']=t if method.startswith('learned') else None
                # One atomic archive contains the terminal result and maps.
                # A crash before the JSON sidecar never requires another test run.
                temporary=archive.with_suffix('.npz.tmp')
                with temporary.open('wb') as f:
                    np.savez_compressed(f,result=__import__('json').dumps(row),state=data['state'],risk=np.asarray(data['risk']),truth=data['truth'])
                temporary.replace(archive);write(result,row)
                rows.append(row)
        write(folder/'complete.json',{'status':'complete','rows':len(rows)})
        return rows
    finally:w.close()


def evaluate(split,out,lux,no_lux,thresholds=None,chosen=None,workers=2):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);cfg=read(ROOT/'experimental/arena/parameters.json');r=cfg[split]
    identity={'status':'running','pid':os.getpid(),'split':split,'seed_start':r['seed_start'],'worlds':r['count'],
              'parameters_sha256':sha(ROOT/'experimental/arena/parameters.json'),'capsules_sha256':sha(ROOT/cfg.get('capsule_library','evidence/learning/arena_v2/capsules.json')),
              'lux_model_sha256':sha(lux),'no_lux_model_sha256':sha(no_lux),'protocol_sha256':sha(ROOT/'docs/arena-protocol.md'),
              'thresholds':thresholds,'chosen_thresholds':chosen,'new_lux_tasks':0}
    previous=read(out/'identity.json') if (out/'identity.json').exists() else None
    if previous:
        for k in ['split','parameters_sha256','capsules_sha256','lux_model_sha256','no_lux_model_sha256','protocol_sha256','thresholds','chosen_thresholds']:
            assert previous[k]==identity[k],f'Changed resume identity {k}'
    if split in ['sealed','ood']:
        assert chosen is not None and thresholds is None,'No threshold search on sealed worlds'
        assert (OUT/'validation/workpoint.json').exists()
    write(out/'identity.json',identity)
    rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={seed:pool.submit(one,seed,split,out,lux,no_lux,thresholds,chosen) for seed in range(r['seed_start'],r['seed_start']+r['count'])}
        for seed,future in futures.items():
            rows+=future.result();write(out/'progress.json',{'completed_worlds':sum((out/str(s)/'complete.json').exists() for s in futures),'rows':len(rows)})
            print(split,seed,flush=True)
    write(out/'results.json',rows)
    if thresholds is None:write(out/'summary.json',summarize(rows))
    else:select_workpoint(rows,thresholds,out)
    identity['status']='complete';write(out/'identity.json',identity)


def select_workpoint(rows,thresholds,out):
    strict=[r for r in rows if r['method']=='strict'];limit=min(.03,sum(r['status']=='collision' for r in strict)/len(strict)+.01)
    result={'collision_limit':limit,'thresholds':thresholds,'chosen':{},'statistics':{}}
    for method in ['learned','learned_no_lux']:
        stats=[]
        for t in thresholds:
            g=[r for r in rows if r['method']==method and r['threshold']==t]
            stats.append({'threshold':t,'worlds':len(g),'arrived':sum(r['status']=='arrived' for r in g),'collisions':sum(r['status']=='collision' for r in g),'arrival_rate':sum(r['status']=='arrived' for r in g)/len(g),'collision_rate':sum(r['status']=='collision' for r in g)/len(g)})
        safe=[r for r in stats if r['collision_rate']<=limit]
        selected=max(safe,key=lambda r:(r['arrival_rate'],-r['collision_rate'],-r['threshold'])) if safe else min(stats,key=lambda r:(r['collision_rate'],-r['arrival_rate'],r['threshold']))
        result['chosen'][method]=selected['threshold'];result['statistics'][method]=stats
        result.setdefault('safe_workpoint_exists',{})[method]=bool(safe)
    write(Path(out)/'workpoint.json',result)


def clustered_comparison(rows,a='learned',b='strict',samples=2000):
    by_a={r['seed']:r for r in rows if r['method']==a};by_b={r['seed']:r for r in rows if r['method']==b}
    keys=sorted(set(by_a)&set(by_b));capsules=sorted({by_a[k]['capsule_id'] for k in keys});groups=[[k for k in keys if by_a[k]['capsule_id']==c] for c in capsules]
    rng=np.random.default_rng(20261112);boot=[]
    for _ in range(samples):
        seeds=[k for i in rng.integers(0,len(groups),len(groups)) for k in groups[i]]
        boot.append([np.mean([(by_a[k]['status']==s)-(by_b[k]['status']==s) for k in seeds]) for s in ['arrived','collision']])
    delta=[np.mean([(by_a[k]['status']==s)-(by_b[k]['status']==s) for k in keys]) for s in ['arrived','collision']]
    return finite({'a':a,'b':b,'paired_worlds':len(keys),'real_imagination_groups':len(capsules),'arrival_delta':delta[0],'collision_delta':delta[1],'cluster_bootstrap_95ci':np.quantile(boot,[.025,.975],axis=0),'bootstrap_samples':samples,'per_capsule':{c:summarize([r for r in rows if r['capsule_id']==c]) for c in capsules}})
