"""Physical demonstrations, behavior cloning, PPO and disjoint goal evaluation."""
import argparse
import hashlib
import json
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

def sample_task(rng, seed):
    distance=float(rng.uniform(.5,3.0))
    if seed%11==0:distance=float(rng.uniform(3.5,5.0))
    bearing=float(rng.uniform(-1.2,1.2))
    yaw=bearing+float(rng.uniform(-1.2,1.2))
    goal=[distance*np.cos(bearing),distance*np.sin(bearing)]
    final_yaw=None if seed%3 else bearing+float(rng.uniform(-1.6,1.6))
    return {'seed':int(seed),'goal':[float(x) for x in goal],'initial_yaw':yaw,'goal_yaw':final_yaw}

def reset_task(env, task):
    env.reset(seed=task['seed']);scene.place(env,0.,0.,task['initial_yaw']);scene.settle(env,30)
    return np.zeros(4)

def evaluate(params, env, manifest, max_seconds):
    results=[]
    for task in manifest:
        previous=reset_task(env,task);t0=env.t;stable=0
        while env.t-t0<max_seconds:
            obs=observation(env,task['goal'],task['goal_yaw'],previous)
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

def bc_grads(params, obs, targets):
    f=ppo.forward(params,obs);diff=f['mean']-targets
    grad=2.*diff/(len(obs)*targets.shape[1])*(1.-f['mean']**2)
    g={k:np.zeros_like(v) for k,v in params.items()}
    g['Wm']=f['h2'].T@grad;g['bm']=grad.sum(0)
    d2=(grad@params['Wm'].T)*(1.-f['h2']**2)
    g['W2']=f['h1'].T@d2;g['b2']=d2.sum(0)
    d1=(d2@params['W2'].T)*(1.-f['h1']**2)
    g['W1']=obs.T@d1;g['b1']=d1.sum(0)
    return g,float(np.mean(diff**2))

def main(argv=None):
    ap=argparse.ArgumentParser(prog='beforestep train')
    ap.add_argument('--config',default='config/training/goal_controller.json');ap.add_argument('--out',required=True)
    args=ap.parse_args(argv);cfg=json.loads((ROOT/args.config).read_text());out=ROOT/args.out
    if out.exists() and any(out.iterdir()):ap.error('Training output must be new; existing checkpoints are preserved')
    out.mkdir(parents=True);t0=time.monotonic()
    init_rng=np.random.default_rng(cfg['seed']);tasks_rng=np.random.default_rng(cfg['seed']+1000)
    shuffle_rng=np.random.default_rng(cfg['seed']+2000);action_rng=np.random.default_rng(cfg['seed']+3000)
    eval_rng=np.random.default_rng(900001)
    manifest=[sample_task(eval_rng,900001+i) for i in range(cfg['evaluation_episodes'])]
    params=ppo.init_params(init_rng,obs_dim=47,act_dim=4,hidden=cfg['hidden'])
    identity={'schema':'beforestep-trained-controller/v1','run_id':uuid.uuid4().hex,
              'started_at':datetime.now(timezone.utc).isoformat(),'config':cfg,
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((ROOT/'src/beforestep').rglob('*.py'))},
              'training_task_seeds':[],'evaluation_manifest':manifest,
              'action_contract':'Front/rear thigh residuals, forward wheel speed and differential steering; PD servos only, nav_base disabled',
              'gravity_mps2':1.62,'initial_actor_sha':ppo.actor_checksum(params)}
    atomic_json(out/'run_identity.json',identity);checkpoint(out/'checkpoints/untrained.npz',params)
    train_env=environment();eval_env=environment('validation_flat')
    initial=evaluate(params,eval_env,manifest[:4],min(15.,cfg['episode_max_seconds']))
    atomic_json(out/'untrained_evaluation.json',initial)
    print(json.dumps({'stage':'untrained','evaluation':initial['success_rate']}),flush=True)
    obs_rows=[];actions=[];demo_results=[]
    for episode in range(cfg['demonstration_episodes']):
        task=sample_task(tasks_rng,10000+episode);identity['training_task_seeds'].append(task['seed'])
        previous=reset_task(train_env,task);start=train_env.t;stable=0
        while train_env.t-start<cfg['episode_max_seconds']:
            obs=observation(train_env,task['goal'],task['goal_yaw'],previous)
            action=expert_action(train_env,task['goal'],task['goal_yaw'])
            obs_rows.append(obs);actions.append(action);apply_action(train_env,action);previous=action
            stable=stable+1 if completed(train_env,task['goal'],task['goal_yaw']) else 0
            if stable>=5 or train_env.terminated or train_env.truncated:break
        demo_results.append({**task,'success':stable>=5,'physical_steps':train_env.n_physics,
                             'sim_seconds':train_env.t-start,'goal_error_m':float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))})
        if (episode+1)%8==0:print(json.dumps({'stage':'physical_demonstrations','episodes':episode+1,'transitions':len(actions),'successful':sum(r['success'] for r in demo_results)}),flush=True)
    X,Y=np.asarray(obs_rows),np.asarray(actions)
    with (out/'demonstrations.npz').open('wb') as f:np.savez_compressed(f,observations=X,actions=Y)
    atomic_json(out/'demonstration_manifest.json',demo_results);atomic_json(out/'run_identity.json',identity)
    opt=ppo.Adam(params,lr=cfg['behavior_cloning_lr']);bc_log=[]
    for epoch in range(cfg['behavior_cloning_epochs']):
        losses=[]
        for indices in np.array_split(shuffle_rng.permutation(len(X)),max(1,len(X)//cfg['minibatch'])):
            grads,loss=bc_grads(params,X[indices],Y[indices]);grads,_=ppo.clip_grads(grads,1.)
            opt.step(params,grads);losses.append(loss)
        bc_log.append({'epoch':epoch+1,'loss':float(np.mean(losses)),'actor_sha':ppo.actor_checksum(params)})
        atomic_json(out/'behavior_cloning.json',bc_log)
        if (epoch+1)%5==0:print(json.dumps({'stage':'behavior_cloning',**bc_log[-1]}),flush=True);checkpoint(out/'checkpoints/bc_latest.npz',params)
    checkpoint(out/'checkpoints/behavior_cloning.npz',params)
    bc_eval=evaluate(params,eval_env,manifest,cfg['episode_max_seconds']);atomic_json(out/'bc_evaluation.json',bc_eval)
    print(json.dumps({'stage':'bc_evaluation','success_rate':bc_eval['success_rate']}),flush=True)
    best=params.copy();best_rate=bc_eval['success_rate'];checkpoint(out/'checkpoints/best.npz',best)
    params['log_std']=np.array([-3.,-3.,-2.7,-2.7]);opt=ppo.Adam(params,lr=cfg['ppo_lr'])
    previous=reset_task(train_env,sample_task(tasks_rng,20000));task=sample_task(tasks_rng,20001)
    previous=reset_task(train_env,task);obs=observation(train_env,task['goal'],task['goal_yaw'],previous)
    steps=updates=episodes=0;stable=0;episode_t=train_env.t
    while steps<cfg['ppo_control_steps']:
        rows={k:[] for k in ('obs','raw','logp_old','reward','value','next_obs','bootstrap','continue')}
        for _ in range(min(cfg['horizon'],cfg['ppo_control_steps']-steps)):
            value=float(ppo.forward(params,obs[None])['value'][0]);action,raw,logp,_=ppo.sample(params,obs,action_rng)
            before=float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))
            old_yaw=yaw_of_goal(train_env,task)
            apply_action(train_env,action);previous_action=previous;previous=action
            after=float(np.linalg.norm(np.asarray(task['goal'])-train_env.data.qpos[:2]))
            new_yaw=yaw_of_goal(train_env,task)
            stable=stable+1 if completed(train_env,task['goal'],task['goal_yaw']) else 0
            terminated=stable>=5 or train_env.terminated
            truncated=train_env.truncated or train_env.t-episode_t>=cfg['episode_max_seconds']
            reward=50.*(before-after)+10.*(old_yaw-new_yaw)-.005-.02*float(np.mean((action-previous_action)**2))
            reward-=.01*float(np.mean(action[:2]**2))+.01*max(0.,train_env._tilt()-15.)
            if stable>=5:reward+=25.
            elif train_env.terminated:reward-=25.
            successor=observation(train_env,task['goal'],task['goal_yaw'],previous)
            for key,item in [('obs',obs),('raw',raw),('logp_old',logp),('reward',reward),('value',value),('next_obs',successor),('bootstrap',0. if terminated else 1.),('continue',0. if terminated or truncated else 1.)]:rows[key].append(item)
            obs=successor;steps+=1
            if terminated or truncated:
                episodes+=1;task=sample_task(tasks_rng,20002+episodes);previous=reset_task(train_env,task)
                obs=observation(train_env,task['goal'],task['goal_yaw'],previous);stable=0;episode_t=train_env.t
        next_values=ppo.forward(params,np.asarray(rows['next_obs']))['value']
        advantages,returns=ppo.gae(rows['reward'],rows['value'],next_values,rows['bootstrap'],rows['continue'],cfg['gamma'],cfg['gae_lambda'])
        advantages=(advantages-advantages.mean())/(advantages.std()+1e-8)
        batch={'obs':np.asarray(rows['obs']),'raw':np.asarray(rows['raw']),'logp_old':np.asarray(rows['logp_old']),'adv':advantages,'ret':returns}
        params,hist=ppo.ppo_update(params,batch,opt,shuffle_rng,epochs=cfg['ppo_epochs'],minibatch=cfg['minibatch'],clip=cfg['clip'],ent_coef=cfg['entropy_coefficient'],vf_coef=cfg['value_coefficient'])
        updates+=1;record={'stage':'ppo','update':updates,'control_steps':steps,'actor_sha':ppo.actor_checksum(params),
                          'reward_mean':float(np.mean(rows['reward'])),'policy_loss':float(np.mean([r['policy_loss'] for r in hist])),
                          'value_loss':float(np.mean([r['value_loss'] for r in hist])),'wall_seconds':time.monotonic()-t0}
        with (out/'ppo.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        checkpoint(out/'checkpoints/latest.npz',params)
        atomic_json(out/'progress.json',record)
        if updates%4==0:print(json.dumps(record),flush=True)
        if updates%cfg['evaluation_every_updates']==0 or steps>=cfg['ppo_control_steps']:
            evaluated=evaluate(params,eval_env,manifest,cfg['episode_max_seconds'])
            atomic_json(out/f'evaluation_u{updates:04}.json',evaluated)
            print(json.dumps({'stage':'ppo_evaluation','update':updates,'success_rate':evaluated['success_rate']}),flush=True)
            if evaluated['success_rate']>=best_rate:
                best=params.copy();best_rate=evaluated['success_rate'];checkpoint(out/'checkpoints/best.npz',params)
    checkpoint(out/'checkpoints/final.npz',params)
    summary={'schema':'beforestep-controller-training/v1','run_id':identity['run_id'],
             'demonstration_transitions':len(X),'ppo_control_steps':steps,'ppo_updates':updates,
             'initial_actor_sha':identity['initial_actor_sha'],'bc_actor_sha':bc_log[-1]['actor_sha'],
             'final_actor_sha':ppo.actor_checksum(params),'best_actor_sha':ppo.actor_checksum(best),
             'untrained_success_rate':initial['success_rate'],'bc_success_rate':bc_eval['success_rate'],
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
