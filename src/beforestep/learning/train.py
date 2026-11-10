"""Physical demonstrations, behavior cloning, PPO and disjoint goal evaluation."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import time
from datetime import datetime, timezone
import uuid

import numpy as np

from beforestep.paths import ROOT
from beforestep import scene
from beforestep.simulation import terrain
from beforestep.simulation.environment import WheelLegEnv
from beforestep.generation.client import atomic_json
from . import ppo
from .policy import observation, apply_action, expert_action, completed

def checkpoint(path, params):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    with temporary.open('wb') as f:np.savez_compressed(f,**params)
    temporary.replace(path)

def environment(name='train_flat', slope=0., roughness=0.):
    terrain.SPAN=scene.SPAN;terrain.N=scene.NGRID
    spec=terrain.make_spec(kind='slope' if slope else 'flat',seed=3,slope_deg=slope,
                           roughness=roughness,goal_x=12.,name=name,span=scene.SPAN)
    spec['terrain']['field_x_max']=15.
    spec['channel']={'center_y':0.,'half_width':12.}
    spec['soil']=scene.v7_soil.resolve('nominal')
    spec['init_perturbation']={'lateral_m':0.,'yaw_rad':0.}
    env=WheelLegEnv(spec,control_hz=50,max_seconds=90,v_ref=.18,nav_base=False)
    env.model.opt.gravity[:]=[0.,0.,-1.62]
    return env

def sample_task(rng, seed, profile=None):
    profile=profile or {}
    distance=float(rng.uniform(.5,3.0))
    if seed%11==0:distance=float(rng.uniform(3.5,5.0))
    if profile.get('near_goal_fraction') and rng.random()<profile['near_goal_fraction']:
        distance=float(rng.uniform(.08,.5))
    bearing=float(rng.uniform(-1.2,1.2))
    spread=profile.get('relative_yaw_range',1.2)
    yaw=bearing+float(rng.uniform(-spread,spread))
    goal=[distance*np.cos(bearing),distance*np.sin(bearing)]
    with_yaw = rng.random() < profile['goal_yaw_fraction'] if 'goal_yaw_fraction' in profile else seed%3 == 0
    yaw_range = profile.get('goal_yaw_range_rad', 1.6)
    final_yaw=bearing+float(rng.uniform(-yaw_range,yaw_range)) if with_yaw else None
    return {'seed':int(seed),'goal':[float(x) for x in goal],'initial_yaw':yaw,'goal_yaw':final_yaw}

def reset_task(env, task):
    env.reset(seed=task['seed']);scene.place(env,0.,0.,task['initial_yaw']);scene.settle(env,30)
    return np.zeros(4)

def evaluate(params, env, manifest, max_seconds):
    results=[]
    for task in manifest:
        previous=reset_task(env,task);t0=env.t;stable=0
        while env.t-t0<max_seconds:
            obs=observation(env,task['goal'],task['goal_yaw'],previous,params['W1'].shape[0])
            action=ppo.deterministic_action(params,obs);apply_action(env,action);previous=action
            stable=stable+1 if completed(env,task['goal'],task['goal_yaw']) else 0
            if stable>=5 or env.terminated or env.truncated:break
        error=float(np.linalg.norm(np.asarray(task['goal'])-env.data.qpos[:2]))
        results.append({**task,'success':stable>=5,'goal_error_m':error,'sim_seconds':env.t-t0,
                        'tilt_degrees':env._tilt(),'physical_steps':env.n_physics,
                        'failure':None if stable>=5 else env.last_termination.get('reason','time_limit')})
    return {'episodes':len(results),'successes':sum(r['success'] for r in results),
            'success_rate':float(np.mean([r['success'] for r in results])),
            'mean_goal_error_m':float(np.mean([r['goal_error_m'] for r in results])),'per_episode':results}

def bc_grads(params, obs, targets, weights=None):
    f=ppo.forward(params,obs);diff=f['mean']-targets
    weights=np.ones(len(obs)) if weights is None else np.asarray(weights)
    grad=2.*diff*weights[:,None]/(weights.sum()*targets.shape[1])*(1.-f['mean']**2)
    g={k:np.zeros_like(v) for k,v in params.items()}
    g['Wm']=f['h2'].T@grad;g['bm']=grad.sum(0)
    d2=(grad@params['Wm'].T)*(1.-f['h2']**2)
    g['W2']=f['h1'].T@d2;g['b2']=d2.sum(0)
    d1=(d2@params['W2'].T)*(1.-f['h1']**2)
    g['W1']=obs.T@d1;g['b1']=d1.sum(0)
    return g,float(np.sum(np.mean(diff**2,axis=1)*weights)/weights.sum())

def main(argv=None):
    ap=argparse.ArgumentParser(prog='beforestep train')
    ap.add_argument('--config',default='config/training/goal_controller.json');ap.add_argument('--out',required=True)
    ap.add_argument('--demonstrations-from',help='Reuse recorded physical demonstrations with an explicit source identity')
    ap.add_argument('--additional-demonstrations-from',help='Append preserved physical demonstrations to newly collected episodes')
    ap.add_argument('--initial-checkpoint',help='Explicit warm-start weights; optimizer and physical training are new')
    ap.add_argument('--resume',action='store_true',help='Resume a complete PPO state in --out; source and configuration must match')
    ap.add_argument('--stop-after-updates',type=int,help='Save and exit at an update boundary, for restart verification')
    args=ap.parse_args(argv);cfg=json.loads((ROOT/args.config).read_text());out=ROOT/args.out
    if args.resume:
        resume(out,cfg,args.stop_after_updates)
        return
    if out.exists() and any(out.iterdir()):ap.error('Training output must be new; existing checkpoints are preserved')
    out.mkdir(parents=True);t0=time.monotonic()
    init_rng=np.random.default_rng(cfg['seed']);tasks_rng=np.random.default_rng(cfg['seed']+1000)
    shuffle_rng=np.random.default_rng(cfg['seed']+2000);action_rng=np.random.default_rng(cfg['seed']+3000)
    eval_rng=np.random.default_rng(900001)
    manifest=[sample_task(eval_rng,900001+i) for i in range(cfg['evaluation_episodes'])]
    dimension=cfg['observation_dim']
    params=ppo.init_params(init_rng,obs_dim=dimension,act_dim=4,hidden=cfg['hidden'])
    initial_checkpoint=None
    if args.initial_checkpoint:
        source=ROOT/args.initial_checkpoint
        with np.load(source,allow_pickle=False) as data:
            loaded={k:data[k].copy() for k in params}
        if dimension==51 and loaded['W1'].shape[0]==49:
            loaded['W1']=np.vstack((loaded['W1'],np.zeros((2,loaded['W1'].shape[1]))))
            loaded['V1']=np.vstack((loaded['V1'],np.zeros((2,loaded['V1'].shape[1]))))
        if any(loaded[k].shape!=params[k].shape or not np.isfinite(loaded[k]).all() for k in params):
            raise ValueError('Initial checkpoint architecture or values are incompatible')
        params=loaded
        initial_checkpoint={'path':args.initial_checkpoint,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                            'note':'Warm start of a new training run, not restoration of the original optimizer or physics'}
    identity={'schema':'beforestep-trained-controller/v1','run_id':uuid.uuid4().hex,
              'started_at':datetime.now(timezone.utc).isoformat(),'config':cfg,
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((ROOT/'src/beforestep').rglob('*.py'))},
              'training_task_seeds':[],'evaluation_manifest':manifest,
              'action_contract':'Front/rear thigh residuals, forward wheel speed and differential steering; PD servos only, nav_base disabled',
              'gravity_mps2':1.62,'initial_actor_sha':ppo.actor_checksum(params),
              'initialization':'warm_start' if initial_checkpoint else 'random',
              'initial_checkpoint':initial_checkpoint}
    identity['resume_source_sha256']={path:sha for path,sha in identity['source_sha256'].items()
        if path.startswith(('src/beforestep/learning/', 'src/beforestep/simulation/'))
        or path in ('src/beforestep/scene.py','src/beforestep/paths.py','src/beforestep/visualization/textures.py')}
    atomic_json(out/'run_identity.json',identity);checkpoint(out/('checkpoints/initial_warm_start.npz' if initial_checkpoint else 'checkpoints/untrained.npz'),params)
    for relative, expected in identity['source_sha256'].items():
        source=ROOT/relative
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Source changed while preserving training snapshot: '+relative)
        destination=out/'source_snapshot'/relative
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    atomic_json(out/'source_snapshot/manifest.json',identity['source_sha256'])
    train_env=environment();eval_env=environment('validation_flat')
    initial=evaluate(params,eval_env,manifest[:4],min(15.,cfg['episode_max_seconds']))
    atomic_json(out/('initial_evaluation.json' if initial_checkpoint else 'untrained_evaluation.json'),initial)
    print(json.dumps({'stage':'warm_start' if initial_checkpoint else 'untrained','evaluation':initial['success_rate']}),flush=True)
    obs_rows=[];actions=[];demo_results=[]
    for episode in range(0 if args.demonstrations_from else cfg['demonstration_episodes']):
        task=sample_task(tasks_rng,cfg.get('demonstration_seed_start',10000)+episode,cfg.get('task_distribution'));identity['training_task_seeds'].append(task['seed'])
        previous=reset_task(train_env,task);start=train_env.t;stable=0
        while train_env.t-start<cfg['episode_max_seconds']:
            obs=observation(train_env,task['goal'],task['goal_yaw'],previous,dimension)
            action=expert_action(train_env,task['goal'],task['goal_yaw'])
            obs_rows.append(obs);actions.append(action);apply_action(train_env,action);previous=action
            stable=stable+1 if completed(train_env,task['goal'],task['goal_yaw']) else 0
            if stable>=5 or train_env.terminated or train_env.truncated:break
        demo_results.append({**task,'success':stable>=5,'physical_steps':train_env.n_physics,
                             'sim_seconds':train_env.t-start,'goal_error_m':float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))})
        if (episode+1)%8==0:print(json.dumps({'stage':'physical_demonstrations','episodes':episode+1,'transitions':len(actions),'successful':sum(r['success'] for r in demo_results)}),flush=True)
    if args.demonstrations_from:
        source=ROOT/args.demonstrations_from
        data=np.load(source/'demonstrations.npz');old=data['observations'];Y=data['actions'].copy()
        if dimension in (49,51) and old.shape[1]==47:
            X=old.copy();X[:,43]=np.minimum(old[:,43]*15.,2.);X[:,45]*=4.
            X=np.column_stack((X,np.clip(old[:,39:41]*15.,-2.,2.)))
        elif old.shape[1] in (dimension,49) and dimension in (49,51):X=old.copy()
        elif old.shape[1]==dimension:X=old.copy()
        else:raise ValueError('Demonstration observation dimension cannot be converted')
        if dimension==51 and X.shape[1]==49:
            terminal=np.linalg.norm(X[:,39:41]*3.,axis=1)<.055
            orientation_only=terminal & (X[:,46]>.5)
            X[orientation_only,39:41]=0.;X[orientation_only,41]=1.;X[orientation_only,42]=0.;X[orientation_only,47:49]=0.
            X=np.column_stack((X,terminal.astype(float),orientation_only.astype(float)))
        demo_results=json.loads((source/'demonstration_manifest.json').read_text())
        identity['training_task_seeds']=[r['seed'] for r in demo_results]
        identity['demonstrations_source']={'path':args.demonstrations_from,
              'sha256':hashlib.sha256((source/'demonstrations.npz').read_bytes()).hexdigest(),
              'recorded_physical_transitions':len(X),'conversion':'Same physical states; explicit goal observation contract, including orientation phase when dimension=51'}
        print(json.dumps({'stage':'reused_physical_demonstrations','transitions':len(X)}),flush=True)
    else:X,Y=np.asarray(obs_rows),np.asarray(actions)
    identity['new_physical_demonstration_transitions']=len(obs_rows)
    if args.additional_demonstrations_from:
        source=ROOT/args.additional_demonstrations_from
        with np.load(source/'demonstrations.npz',allow_pickle=False) as data:
            old_X=data['observations'];old_Y=data['actions']
        if old_X.shape[1]!=dimension:raise ValueError('Additional demonstrations must use the same observation contract')
        X=np.concatenate((X,old_X));Y=np.concatenate((Y,old_Y))
        old_results=json.loads((source/'demonstration_manifest.json').read_text())
        demo_results.extend(old_results)
        identity['training_task_seeds'].extend(row['seed'] for row in old_results)
        identity['additional_demonstrations_source']={'path':args.additional_demonstrations_from,
            'sha256':hashlib.sha256((source/'demonstrations.npz').read_bytes()).hexdigest(),'reused_physical_transitions':len(old_X)}
    identity['physical_demonstration_transitions']=len(X)
    with (out/'demonstrations.npz').open('wb') as f:np.savez_compressed(f,observations=X,actions=Y)
    atomic_json(out/'demonstration_manifest.json',demo_results);atomic_json(out/'run_identity.json',identity)
    if dimension in (49,51) and cfg.get('terminal_goal_augmentation',0):
        count=cfg['terminal_goal_augmentation'];indices=shuffle_rng.integers(0,len(X),size=count)
        augmented=X[indices].copy();angles=shuffle_rng.uniform(-np.pi,np.pi,count);distances=shuffle_rng.uniform(0.,cfg.get('terminal_goal_radius_m',.05),count)
        local=np.column_stack((distances*np.cos(angles),distances*np.sin(angles)))
        augmented[:,39:41]=local/3.;augmented[:,41]=np.cos(angles);augmented[:,42]=np.sin(angles)
        augmented[:,43]=distances/.2;augmented[:,47:49]=local/.2
        yaw_range=cfg.get('terminal_yaw_range_rad',.35)
        yaw_errors=shuffle_rng.uniform(-yaw_range,yaw_range,count);mask=shuffle_rng.random(count)<cfg.get('terminal_yaw_fraction',.35)
        augmented[:,44]=np.cos(yaw_errors);augmented[:,45]=4.*np.sin(yaw_errors);augmented[:,46]=mask
        if dimension==51:
            terminal=distances<.055;orientation_only=terminal & mask
            augmented[:,49]=terminal;augmented[:,50]=orientation_only
            augmented[orientation_only,39:41]=0.;augmented[orientation_only,41]=1.;augmented[orientation_only,42]=0.;augmented[orientation_only,47:49]=0.
        labels=np.zeros((count,4));turn=np.clip(6.*yaw_errors,-3.,3.)
        turn=np.where(np.abs(yaw_errors)<np.radians(1.5),0.,np.sign(turn)*np.maximum(np.abs(turn),cfg.get('terminal_min_turn_rps',.65)))
        labels[:,3]=mask*turn/4.
        X=np.concatenate((X,augmented));Y=np.concatenate((Y,labels))
        identity['goal_augmentation']={'rows':count,'physical_state_source':'Recorded demonstrations',
                                     'targets':'Counterfactual nearby goals; supervised labels, not new physical transitions',
                                     'radius_m':cfg.get('terminal_goal_radius_m',.05),
                                     'orientation_goal_fraction':cfg.get('terminal_yaw_fraction',.35),
                                     'orientation_error_range_rad':yaw_range}
    atomic_json(out/'run_identity.json',identity)
    actual_distance=np.linalg.norm(X[:,39:41]*3.,axis=1)
    weights=np.where(actual_distance<.3,cfg.get('near_goal_weight',1.),1.)
    with (out/'supervision.npz').open('wb') as stream:np.savez_compressed(stream,observations=X,actions=Y,weights=weights)
    opt=ppo.Adam(params,lr=cfg['behavior_cloning_lr']);bc_log=[]
    for epoch in range(cfg['behavior_cloning_epochs']):
        losses=[]
        for indices in np.array_split(shuffle_rng.permutation(len(X)),max(1,len(X)//cfg['minibatch'])):
            grads,loss=bc_grads(params,X[indices],Y[indices],weights[indices]);grads,_=ppo.clip_grads(grads,1.)
            opt.step(params,grads);losses.append(loss)
        bc_log.append({'epoch':epoch+1,'loss':float(np.mean(losses)),'actor_sha':ppo.actor_checksum(params)})
        atomic_json(out/'behavior_cloning.json',bc_log)
        if (epoch+1)%5==0:print(json.dumps({'stage':'behavior_cloning',**bc_log[-1]}),flush=True);checkpoint(out/'checkpoints/bc_latest.npz',params)
    checkpoint(out/'checkpoints/behavior_cloning.npz',params)
    bc_eval=evaluate(params,eval_env,manifest,cfg['episode_max_seconds']);atomic_json(out/'bc_evaluation.json',bc_eval)
    print(json.dumps({'stage':'bc_evaluation','success_rate':bc_eval['success_rate']}),flush=True)
    best=params.copy();best_rate=bc_eval['success_rate'];checkpoint(out/'checkpoints/best.npz',best)
    optimize(out,cfg,identity,params,X,Y,weights,train_env,eval_env,manifest,tasks_rng,shuffle_rng,action_rng,
             best,best_rate,initial,bc_eval,bc_log,t0,stop_after_updates=args.stop_after_updates)


def resume(out,cfg,stop_after_updates=None):
    from .checkpoints import load
    if (out/'summary.json').exists():raise ValueError('Completed training cannot be overwritten')
    _,_,_,_,state=load(out/'checkpoints/resume.npz')
    if cfg!=state['config']:raise ValueError('Resume configuration differs from saved training')
    identity=state['identity']
    for path,expected in identity.get('resume_source_sha256',identity['source_sha256']).items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Resume source differs: '+path)
    with np.load(out/'supervision.npz',allow_pickle=False) as data:
        X=data['observations'];Y=data['actions'];weights=data['weights']
    initial=json.loads((out/('initial_evaluation.json' if (out/'initial_evaluation.json').exists() else 'untrained_evaluation.json')).read_text())
    bc_eval=json.loads((out/'bc_evaluation.json').read_text())
    bc_log=json.loads((out/'behavior_cloning.json').read_text())
    params=load(out/'checkpoints/resume.npz')[0]
    best=load(out/'checkpoints/resume.npz')[1]
    print(json.dumps({'stage':'resumed','run_id':identity['run_id'],'control_steps':state['steps']}),flush=True)
    optimize(out,cfg,identity,params,X,Y,weights,environment(),environment('validation_flat'),
             identity['evaluation_manifest'],None,None,None,best,state['best_rate'],initial,bc_eval,bc_log,
             time.monotonic(),restored=state,stop_after_updates=stop_after_updates)


def optimize(out,cfg,identity,params,X,Y,weights,train_env,eval_env,manifest,tasks_rng,shuffle_rng,action_rng,
             best,best_rate,initial,bc_eval,bc_log,start_time,restored=None,stop_after_updates=None):
    dimension=cfg['observation_dim']
    params['log_std']=np.array([-3.,-3.,-2.7,-2.7]);opt=ppo.Adam(params,lr=cfg['ppo_lr'])
    task=sample_task(tasks_rng,20001,cfg.get('task_distribution')) if restored is None else restored['task']
    previous=reset_task(train_env,task);obs=observation(train_env,task['goal'],task['goal_yaw'],previous,dimension)
    steps=updates=episodes=0;stable=0;episode_t=train_env.t
    if restored is not None:
        from .checkpoints import load
        params,best,opt,generators,state=load(out/'checkpoints/resume.npz')
        tasks_rng=generators['tasks'];shuffle_rng=generators['shuffle'];action_rng=generators['action']
        train_env.restore_state(state['environment'])
        task=state['task'];previous=np.asarray(state['previous']);obs=np.asarray(state['observation'])
        steps=state['steps'];updates=state['updates'];episodes=state['episodes'];stable=state['stable'];episode_t=state['episode_t']
        best_rate=state['best_rate'];t0=time.monotonic()-state['elapsed_seconds']
        with (out/'ppo.jsonl').open('w') as log:
            for row in state['history']:log.write(json.dumps(row)+'\n')
    else:
        t0=start_time
    history=[json.loads(line) for line in (out/'ppo.jsonl').read_text().splitlines()] if (out/'ppo.jsonl').exists() else []
    def persist(pending_evaluation=False):
        from .checkpoints import save, physical_state
        save(out/'checkpoints/resume.npz',params,best,opt,
             {'tasks':tasks_rng,'shuffle':shuffle_rng,'action':action_rng},
             {'config':cfg,'identity':identity,'environment':physical_state(train_env),'task':task,
              'previous':previous.tolist(),'observation':obs.tolist(),'steps':steps,'updates':updates,
              'episodes':episodes,'stable':stable,'episode_t':episode_t,'best_rate':best_rate,
              'elapsed_seconds':time.monotonic()-t0,'history':history,'pending_evaluation':pending_evaluation})
    def validation():
        nonlocal best,best_rate
        evaluated=evaluate(params,eval_env,manifest,cfg['episode_max_seconds'])
        atomic_json(out/f'evaluation_u{updates:04}.json',evaluated)
        print(json.dumps({'stage':'ppo_evaluation','update':updates,'success_rate':evaluated['success_rate']}),flush=True)
        if evaluated['success_rate']>=best_rate:
            best={k:v.copy() for k,v in params.items()};best_rate=evaluated['success_rate'];checkpoint(out/'checkpoints/best.npz',best)
        persist(False)
    if restored is not None and state.get('pending_evaluation'):validation()
    else:persist(False)
    while steps<cfg['ppo_control_steps']:
        rows={k:[] for k in ('obs','raw','logp_old','reward','value','next_obs','bootstrap','continue')}
        for _ in range(min(cfg['horizon'],cfg['ppo_control_steps']-steps)):
            value=float(ppo.forward(params,obs[None])['value'][0]);action,raw,logp,_=ppo.sample(params,obs,action_rng)
            before=float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))
            before_potential=potential(train_env,task)
            apply_action(train_env,action);previous_action=previous;previous=action
            after=float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))
            after_potential=potential(train_env,task)
            stable=stable+1 if completed(train_env,task['goal'],task['goal_yaw']) else 0
            terminated=stable>=5 or train_env.terminated
            truncated=train_env.truncated or train_env.t-episode_t>=cfg['episode_max_seconds']
            reward=after_potential-before_potential-.005-.02*float(np.mean((action-previous_action)**2))
            reward-=.01*float(np.mean(action[:2]**2))+.01*max(0.,train_env._tilt()-15.)
            if stable>=5:reward+=25.
            elif train_env.terminated:reward-=25.
            successor=observation(train_env,task['goal'],task['goal_yaw'],previous,dimension)
            for key,item in [('obs',obs),('raw',raw),('logp_old',logp),('reward',reward),('value',value),('next_obs',successor),('bootstrap',0. if terminated else 1.),('continue',0. if terminated or truncated else 1.)]:rows[key].append(item)
            obs=successor;steps+=1
            if terminated or truncated:
                episodes+=1;task=sample_task(tasks_rng,20002+episodes,cfg.get('task_distribution'));previous=reset_task(train_env,task)
                obs=observation(train_env,task['goal'],task['goal_yaw'],previous,dimension);stable=0;episode_t=train_env.t
        next_values=ppo.forward(params,np.asarray(rows['next_obs']))['value']
        advantages,returns=ppo.gae(rows['reward'],rows['value'],next_values,rows['bootstrap'],rows['continue'],cfg['gamma'],cfg['gae_lambda'])
        advantages=(advantages-advantages.mean())/(advantages.std()+1e-8)
        batch={'obs':np.asarray(rows['obs']),'raw':np.asarray(rows['raw']),'logp_old':np.asarray(rows['logp_old']),'adv':advantages,'ret':returns}
        params,hist=ppo.ppo_update(params,batch,opt,shuffle_rng,epochs=cfg['ppo_epochs'],minibatch=cfg['minibatch'],clip=cfg['clip'],ent_coef=cfg['entropy_coefficient'],vf_coef=cfg['value_coefficient'])
        for _ in range(cfg.get('imitation_anchor_minibatches',0)):
            indices=shuffle_rng.integers(0,len(X),size=cfg['minibatch'])
            grads,_=bc_grads(params,X[indices],Y[indices],weights[indices]);grads,_=ppo.clip_grads(grads,.2)
            opt.step(params,grads)
        updates+=1;record={'stage':'ppo','update':updates,'control_steps':steps,'actor_sha':ppo.actor_checksum(params),
                          'reward_mean':float(np.mean(rows['reward'])),'policy_loss':float(np.mean([r['policy_loss'] for r in hist])),
                          'value_loss':float(np.mean([r['value_loss'] for r in hist])),'wall_seconds':time.monotonic()-t0}
        history.append(record)
        with (out/'ppo.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        checkpoint(out/'checkpoints/latest.npz',params)
        atomic_json(out/'progress.json',record)
        if updates%4==0:print(json.dumps(record),flush=True)
        pending_evaluation=updates%cfg['evaluation_every_updates']==0 or steps>=cfg['ppo_control_steps']
        persist(pending_evaluation)
        if pending_evaluation:validation()
        if stop_after_updates is not None and updates>=stop_after_updates and steps<cfg['ppo_control_steps']:
            print(json.dumps({'stage':'checkpoint_saved','run_id':identity['run_id'],'control_steps':steps}),flush=True)
            return
    checkpoint(out/'checkpoints/final.npz',params)
    summary={'schema':'beforestep-controller-training/v1','run_id':identity['run_id'],
             'demonstration_transitions':identity.get('physical_demonstration_transitions',len(X)-identity.get('goal_augmentation',{}).get('rows',0)),
             'new_physical_demonstration_transitions':identity.get('new_physical_demonstration_transitions',0),
             'counterfactual_goal_augmentation_rows':identity.get('goal_augmentation',{}).get('rows',0),'ppo_control_steps':steps,'ppo_updates':updates,
             'initial_actor_sha':identity['initial_actor_sha'],'bc_actor_sha':bc_log[-1]['actor_sha'],
             'final_actor_sha':ppo.actor_checksum(params),'best_actor_sha':ppo.actor_checksum(best),
             'untrained_success_rate':initial['success_rate'] if identity.get('initialization','random')=='random' else None,
             'initial_success_rate':initial['success_rate'],'bc_success_rate':bc_eval['success_rate'],
             'best_validation_success_rate':best_rate,'wall_seconds':time.monotonic()-t0,
             'note':'Validation goals disjoint from training; full lunar obstacle mission is a separate required acceptance.'}
    atomic_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)

def yaw_of_goal(env, task):
    from beforestep.navigation.controller import yaw_of
    distance=float(np.linalg.norm(np.asarray(task['goal'])-env.data.qpos[:2]))
    if distance<.08 and task['goal_yaw'] is not None:target=task['goal_yaw']
    else:
        delta=np.asarray(task['goal'])-env.data.qpos[:2];target=float(np.arctan2(delta[1],delta[0]))
    return abs((target-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi)

def potential(env, task):
    from beforestep.navigation.controller import yaw_of
    delta=np.asarray(task['goal'])-env.data.qpos[:2];distance=float(np.linalg.norm(delta))
    bearing=abs((np.arctan2(delta[1],delta[0])-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi)
    yaw_error=0. if task['goal_yaw'] is None else abs((task['goal_yaw']-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi)
    return -50.*distance-3.*min(distance/.5,1.)*bearing-2.*max(0.,1.-distance/.3)*yaw_error
