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


def decision(method,features,position,goal,cfg,model=None,visits=None,advisor=None):
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
    elif method in ('rules_cached_prior','rules_llm'):occupied |= features[2]>.5
    blocked=ndimage.distance_transform_edt(~occupied)*cfg['resolution_m'] <= cfg['robot_radius_m']
    distances,actions=shortest_paths(blocked,goal)
    a=int(actions[tuple(position)])
    if method=='rules_llm':
        if not getattr(advisor,'consult_now',True):
            return (a if a>=0 and safe_transition(guard,position,a) else None),{'source':'graph_search_between_llm_consults'}
        candidates=[]
        for option,delta in enumerate(DIRECTIONS):
            target=position+delta
            if not safe_transition(guard,position,option):continue
            x,y=target
            visible=features[1,max(0,x-2):x+3,max(0,y-2):y+3]
            distance=float(distances[x,y])
            candidates.append({'id':option,'delta':delta.tolist(),
                               'goal_distance_m':float(np.linalg.norm(target-goal)*cfg['resolution_m']),
                               'estimated_remaining_steps':distance if np.isfinite(distance) else None,
                               'observed_fraction_near_target':float(visible.mean()),
                               'cached_prior_blocked':bool(blocked[x,y]),
                               'visits':int(visits[x,y]) if visits is not None else 0})
        context={'position':position.tolist(),'goal':goal.tolist(),'known_fraction':float(features[1].mean()),
                 'candidates':candidates,'looks_remaining':getattr(advisor,'looks_remaining',cfg['max_panorama_looks'])}
        reply=advisor.choose(context)
        if reply['status']=='ok':
            answer=reply['answer']
            return (answer.get('candidate_id') if answer['action']=='move' else None),{
                'source':'llm','call_id':reply['id'],'stop_requested':answer['action']=='stop'}
        return (a if a>=0 and safe_transition(guard,position,a) else None),{
            'source':'graph_search_llm_unavailable','llm_status':reply['status']}
    return (a if a>=0 and safe_transition(guard,position,a) else None),{'source':'graph_search'}


def rollout(world,method,model=None,advisor=None):
    pos=world.start.copy();known=None;heading=0.;visits=np.zeros(world.shape,np.int32)
    trace=[pos.tolist()];decisions=[];looks=0;length=0.;elapsed=0.
    status='time_limit'
    calls_before=advisor.calls if advisor is not None else 0
    if world.blocked[tuple(pos)]:status='invalid_start'
    else:
        for step in range(world.cfg['max_decisions']):
            if advisor is not None:
                advisor.looks_remaining=world.cfg['max_panorama_looks']-looks
                advisor.consult_now=(step%12==0 and advisor.calls-calls_before<4)
            if np.array_equal(pos,world.goal):status='arrived';break
            features,known=world.observe(pos,heading,known,prior_enabled=method!='learned_no_prior')
            started=time.monotonic()
            action,details=decision(method,features,pos,world.goal,world.cfg,model,visits,advisor)
            elapsed+=time.monotonic()-started
            # Every method receives the same optional stationary panorama budget.
            if action is None:
                if details.get('stop_requested'):status='stopped';break
                if looks>=world.cfg['max_panorama_looks']:status='stopped';break
                features,known=world.observe(pos,heading,known,panorama=True,prior_enabled=method!='learned_no_prior')
                looks+=1;started=time.monotonic()
                if advisor is not None:
                    advisor.looks_remaining=world.cfg['max_panorama_looks']-looks
                    advisor.consult_now=advisor.calls-calls_before<4
                action,details=decision(method,features,pos,world.goal,world.cfg,model,visits,advisor)
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


def evaluate_llm(cfg_path,library_path,env_file,out,seed_start=6100000,count=8,max_calls=32):
    from .llm import Advisor
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Preserve first LLM comparison')
    advisor=Advisor(env_file,out/'calls',max_calls=max_calls)
    cfg,library=read(cfg_path),read(library_path)
    write(out/'identity.json',{'stage':'running','seed_start':seed_start,'count':count,'max_calls':max_calls,
                             'model':advisor.model,'config_sha256':sha(cfg_path),
                             'new_lux_tasks':0,'scope':'Separate rule + LLM planar comparison'})
    rows=[]
    for seed in range(seed_start,seed_start+count):
        world=World(cfg,library,'test',seed);write(out/'scenes'/f'{seed}.json',world.manifest())
        for method in ['rules_cached_prior','rules_llm']:
            row=rollout(world,method,advisor=advisor);rows.append(row)
            write(out/'episodes'/f'{seed}-{method}.json',row)
    write(out/'summary.json',summary(rows))
    identity=read(out/'identity.json');identity.update(stage='complete',service_requests=advisor.calls)
    write(out/'identity.json',identity)


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


def evaluate(cfg_path,library_path,training,out,splits=None,resume=False):
    cfg,library=read(cfg_path),read(library_path);out=Path(out);training=Path(training)
    if out.exists() and any(out.iterdir()) and not resume:raise ValueError('Preserve the first test; use --resume')
    out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1)
    trained=load_model(training/'best.pt',cfg['value_iterations'])
    untrained=load_model(training/'untrained.pt',cfg['value_iterations'])
    identity={'schema':'beforestep-navigation-evaluation/v1','config_sha256':sha(cfg_path),
              'library_sha256':sha(library_path),'model_sha256':sha(training/'best.pt'),
              'weight_selection':'validation only; no test seed is used by training',
              'simulation':'2D grid, planar ray visibility and cast shadows; not RGB-D or MuJoCo',
              'evaluation_source_sha256':sha(__file__),
              'new_paid_tasks':0,'stage':'running'}
    if resume:
        previous=read(out/'identity.json')
        for field in ['config_sha256','library_sha256','model_sha256','evaluation_source_sha256']:
            if previous[field]!=identity[field]:raise ValueError('Evaluation resume identity changed: '+field)
    write(out/'identity.json',identity);rows=[]
    for split in splits or ['test','ood']:
        part=[];spec=cfg[split]
        for seed in range(spec['seed_start'],spec['seed_start']+spec['count']):
            world=World(cfg,library,split,seed);write(out/'scenes'/f'{seed}.json',world.manifest())
            for method in METHODS:
                file=out/'episodes'/f'{seed}-{method}.json'
                row=read(file) if resume and file.exists() else rollout(world,method,untrained if method=='untrained' else trained)
                part.append(row);write(out/'episodes'/f'{seed}-{method}.json',row)
            if (seed-spec['seed_start']+1)%16==0:
                print({'split':split,'completed_worlds':seed-spec['seed_start']+1},flush=True)
        rows.extend(part);write(out/f'{split}-summary.json',summary(part))
    identity.update(stage='complete',episodes=len(rows));write(out/'identity.json',identity)
    write(out/'summary.json',summary(rows));return summary(rows)
