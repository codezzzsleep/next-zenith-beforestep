"""Paired closed-loop planar navigation; keep every seed, including no-path worlds."""
import collections
import time
from pathlib import Path

import numpy as np
import torch
from scipy import ndimage

from .model import infer,load_model
from .world import DIRECTIONS,World,known_blocked,read,safe_transition,sha,shortest_paths,write

METHODS = ['rules_conservative','rules_optimistic','rules_cached_prior',
           'learned','untrained','learned_no_prior']


def decision(method,features,position,goal,cfg,model=None,visits=None):
    guard=known_blocked(features,cfg)
    if method in ('learned','untrained','learned_no_prior'):
        scores,risk=infer(model,features,goal)
        values=scores[:,position[0],position[1]].copy()
        # Repeated-state penalty is common navigation memory, explicitly recorded.
        for a,delta in enumerate(DIRECTIONS):
            target=position+delta
            if not safe_transition(guard,position,a):values[a]=-np.inf
            elif visits is not None:values[a]-=.025*visits[tuple(target)]
        action=int(np.argmax(values)) if np.isfinite(values).any() else None
        return action,{'source':'neural_value_iteration','scores':values.tolist(),
                       'risk_at_pose':float(risk[tuple(position)])}
    occupied=features[0]>.5
    if method=='rules_conservative':occupied |= features[1]<.5
    elif method=='rules_cached_prior':occupied |= features[2]>.5
    blocked=ndimage.distance_transform_edt(~occupied)*cfg['resolution_m'] <= cfg['robot_radius_m']
    _,actions=shortest_paths(blocked,goal)
    a=int(actions[tuple(position)])
    return (a if a>=0 and safe_transition(guard,position,a) else None),{'source':'graph_search'}


def rollout(world,method,model=None):
    pos=world.start.copy();known=None;heading=0.;visits=np.zeros(world.shape,np.int32)
    trace=[pos.tolist()];decisions=[];looks=0;length=0.;elapsed=0.
    status='time_limit'
    if world.blocked[tuple(pos)]:status='invalid_start'
    else:
        for step in range(world.cfg['max_decisions']):
            if np.array_equal(pos,world.goal):status='arrived';break
            features,known=world.observe(pos,heading,known,prior_enabled=method!='learned_no_prior')
            started=time.monotonic()
            action,details=decision(method,features,pos,world.goal,world.cfg,model,visits)
            elapsed+=time.monotonic()-started
            # Every method receives the same optional stationary panorama budget.
            if action is None:
                if looks>=world.cfg['max_panorama_looks']:status='stopped';break
                features,known=world.observe(pos,heading,known,panorama=True,prior_enabled=method!='learned_no_prior')
                looks+=1;started=time.monotonic()
                action,details=decision(method,features,pos,world.goal,world.cfg,model,visits)
                elapsed+=time.monotonic()-started
                if action is None:status='stopped';break
            decisions.append({'step':step,'position':pos.tolist(),'action':action,
                              'known_cells':int(known.sum()),'source':details['source']})
            if not safe_transition(world.blocked,pos,action):status='collision';break
            delta=DIRECTIONS[action];pos+=delta;visits[tuple(pos)]+=1
            heading=float(np.arctan2(delta[1],delta[0]));length+=float(np.linalg.norm(delta))*world.res
            trace.append(pos.tolist())
            if visits[tuple(pos)]>=5:status='loop';break
    return {'seed':world.seed,'method':method,'oracle_reachable':bool(world.reachable),'status':status,
            'path_length_m':length,'panorama_looks':looks,'passive_observations':len(decisions),
            'planning_wall_seconds':elapsed,'goal_error_m':float(np.linalg.norm(pos-world.goal)*world.res),
            'trace_cells':trace,'decisions':decisions}


def summary(rows):
    groups={}
    for method in sorted({r['method'] for r in rows}):
        items=[r for r in rows if r['method']==method]
        reachable=[r for r in items if r['oracle_reachable']]
        groups[method]={'episodes':len(items),'statuses':dict(collections.Counter(r['status'] for r in items)),
                        'reachable_episodes':len(reachable),
                        'reachable_arrivals':sum(r['status']=='arrived' for r in reachable),
                        'reachable_success_rate':sum(r['status']=='arrived' for r in reachable)/max(1,len(reachable)),
                        'mean_planning_wall_seconds':float(np.mean([r['planning_wall_seconds'] for r in items]))}
    return groups


def evaluate(cfg_path,library_path,training,out,splits=None):
    cfg,library=read(cfg_path),read(library_path);out=Path(out);training=Path(training)
    if out.exists() and any(out.iterdir()):raise ValueError('Preserve the first test; use a new output directory')
    out.mkdir(parents=True);torch.set_num_threads(1)
    trained=load_model(training/'best.pt',cfg['value_iterations'])
    untrained=load_model(training/'untrained.pt',cfg['value_iterations'])
    identity={'schema':'beforestep-navigation-evaluation/v1','config_sha256':sha(cfg_path),
              'library_sha256':sha(library_path),'model_sha256':sha(training/'best.pt'),
              'weight_selection':'validation only; no test seed is used by training',
              'simulation':'2D grid, planar ray visibility and cast shadows; not RGB-D or MuJoCo',
              'new_paid_tasks':0,'stage':'running'}
    write(out/'identity.json',identity);rows=[]
    for split in splits or ['test','ood']:
        part=[];spec=cfg[split]
        for seed in range(spec['seed_start'],spec['seed_start']+spec['count']):
            world=World(cfg,library,split,seed);write(out/'scenes'/f'{seed}.json',world.manifest())
            for method in METHODS:
                row=rollout(world,method,untrained if method=='untrained' else trained)
                part.append(row);write(out/'episodes'/f'{seed}-{method}.json',row)
            if (seed-spec['seed_start']+1)%16==0:
                print({'split':split,'completed_worlds':seed-spec['seed_start']+1},flush=True)
        rows.extend(part);write(out/f'{split}-summary.json',summary(part))
    identity.update(stage='complete',episodes=len(rows));write(out/'identity.json',identity)
    write(out/'summary.json',summary(rows));return summary(rows)
