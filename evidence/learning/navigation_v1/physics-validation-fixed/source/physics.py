"""MuJoCo execution on the same new worlds, with planar sensing explicitly kept.

All compared route policies use the same frozen learned v4 motor controller.
Robot position is assigned only during initialization; subsequent motion comes
from wheel and joint commands integrated by MuJoCo.
"""
import time
from pathlib import Path
import numpy as np
import torch
from scipy.spatial import ConvexHull

from beforestep import scene as S
from beforestep.learning.policy import GoalPolicy,apply_action,completed
from beforestep.navigation.controller import yaw_of
from beforestep.navigation.map import contact_watch
from beforestep.simulation.environment import WheelLegEnv
from beforestep.simulation import terrain

from .evaluate import decision,summary
from .model import load_model
from .world import ROOT,DIRECTIONS,World,known_blocked,read,safe_transition,sha,write


def scene_spec(world,out):
    objects=[]
    for i,rock in enumerate(world.rocks):
        polygon=np.asarray(rock['truth_polygon'])
        center=polygon.mean(0);local=polygon-center
        n=len(local)
        vertices=np.vstack([np.column_stack([local,np.zeros(n)]),
                            np.column_stack([local*.70,np.full(n,rock['height_m'])])])
        hull=ConvexHull(vertices);lines=['v %.8f %.8f %.8f'%tuple(v) for v in vertices]
        lines.extend('f %d %d %d'%tuple(face+1) for face in hull.simplices)
        mesh=Path(out)/'meshes'/f'rock-{i}.obj';mesh.parent.mkdir(parents=True,exist_ok=True)
        mesh.write_text('\n'.join(lines)+'\n')
        objects.append({'mesh_file':str(mesh.resolve()),'x':float(center[0]),'y':float(center[1]),
                        'yaw_deg':0.,'height_m':rock['height_m']})
    # Border boxes are physical obstacles too, so leaving the map cannot pass unnoticed.
    width,height=np.array(world.shape)*world.res
    # The grid boundary is a conservative robot-centre constraint. Physical
    # walls sit one grid cell outside it so the rectangular wheel-leg body can
    # occupy the declared initial/terminal pose without touching a wall.
    for i,(x,y,sx,sy) in enumerate([(width/2,-world.res,width/2+.6,.15),
                                  (width/2,height,width/2+.6,.15),
                                  (-world.res,height/2,.15,height/2+.6),
                                  (width,height/2,.15,height/2+.6)]):
        vertices=np.array([[dx*sx,dy*sy,dz*.8] for dx in [-1,1] for dy in [-1,1] for dz in [0,1]])
        hull=ConvexHull(vertices)
        mesh=Path(out)/'meshes'/f'border-{i}.obj'
        mesh.write_text('\n'.join(['v %.8f %.8f %.8f'%tuple(v) for v in vertices]+
                                  ['f %d %d %d'%tuple(f+1) for f in hull.simplices])+'\n')
        objects.append({'mesh_file':str(mesh.resolve()),'x':x,'y':y,'yaw_deg':0.})
    terrain.SPAN=S.SPAN;terrain.N=S.NGRID
    spec=terrain.make_spec(kind='flat',seed=world.seed,goal_x=float(world.goal[0]*world.res),
                           span=S.SPAN,name=f'navigation_{world.seed}',objects=objects)
    spec['terrain']['field_x_max']=float(width)
    spec['channel']={'center_y':float(height/2),'half_width':float(height/2)}
    spec['soil']=S.v7_soil.resolve('nominal')
    spec['init_perturbation']={'lateral_m':0.,'yaw_rad':0.}
    return spec


def run(world,method,model,out):
    out=Path(out);out.mkdir(parents=True)
    spec=scene_spec(world,out);write(out/'scene-spec.json',spec)
    env=WheelLegEnv(spec,control_hz=50,max_seconds=world.cfg['physical_limit_sim_s'],v_ref=.18,nav_base=False)
    env.model.opt.gravity[:]=[0.,0.,-1.62]
    env.reset(seed=world.seed);S.place(env,*(world.start*world.res),yaw=0.);S.settle(env,30)
    ctrl=GoalPolicy(ROOT/world.cfg['physical_control_model'])
    watch=contact_watch(env,[f'obstacle{i}' for i in range(len(spec['objects']))])
    trace=[];controls=[];decisions=[];known=None;looks=0;collision=None;status='time_limit'
    visits=np.zeros(world.shape,np.int32);last_cell=None;t0=env.t;started=time.monotonic()
    goal=world.goal*world.res
    for step in range(world.cfg['max_decisions']):
        actual=env.data.qpos[:2].copy();cell=np.rint(actual/world.res).astype(int)
        if not ((cell>=0).all() and (cell<world.shape).all()):status='out_of_map';break
        if np.linalg.norm(actual-goal)<.075 and completed(env,goal):status='arrived';break
        features,known=world.observe(cell,yaw_of(env.data.qpos),known)
        a,info=decision(method,features,cell,world.goal,world.cfg,model,visits)
        if a is None and looks<world.cfg['max_panorama_looks']:
            features,known=world.observe(cell,yaw_of(env.data.qpos),known,panorama=True);looks+=1
            a,info=decision(method,features,cell,world.goal,world.cfg,model,visits)
        if a is None:status='stopped';break
        guard=known_blocked(features,world.cfg)
        waypoint_cell=cell.copy()
        # Same-direction subgoals shorten low-level stop/start overhead, using only
        # the current observation and route policy; no future truth is sampled.
        for _ in range(3):
            if not safe_transition(guard,waypoint_cell,a):break
            waypoint_cell+=DIRECTIONS[a]
            if np.array_equal(waypoint_cell,world.goal):break
            next_a,_=decision(method,features,waypoint_cell,world.goal,world.cfg,model,visits)
            if next_a != a:break
        target=waypoint_cell*world.res
        if np.linalg.norm(actual-goal)<.5:target=goal
        decisions.append({'step':step,'position_m':actual.tolist(),'waypoint_m':target.tolist(),
                          'action':a,'source':info['source'],'known_cells':int(known.sum())})
        stable=0;segment_start=env.t
        while env.t-segment_start<30. and env.t-t0<world.cfg['physical_limit_sim_s']:
            action=ctrl.action(env,target);apply_action(env,action)
            if env.n_control%5==0:
                trace.append([float(env.t),*env.data.qpos[:7].tolist()]);controls.append(action.tolist())
            hit,details=watch(env)
            if hit or env.contact_steps>0:
                collision=details or {'first_contact_t':env.first_contact_t};status='collision';break
            if env.terminated or env.truncated:
                status=env.last_termination.get('reason','terminated');break
            stable=stable+1 if completed(env,target) else 0
            if stable>=5:break
        if status=='collision' or env.terminated or env.truncated:break
        if stable<5:status='controller_time_limit';break
        if np.linalg.norm(env.data.qpos[:2]-goal)<.075 and completed(env,goal):status='arrived';break
        reached=np.rint(env.data.qpos[:2]/world.res).astype(int)
        if (reached>=0).all() and (reached<world.shape).all():
            visits[tuple(reached)]+=1
            if visits[tuple(reached)]>=5:status='loop';break
    np.savez_compressed(out/'trajectory.npz',qpos_time=np.asarray(trace),actions=np.asarray(controls))
    result={'seed':world.seed,'method':method,'oracle_reachable':bool(world.reachable),'status':status,
            'sim_seconds':env.t-t0,'wall_seconds':time.monotonic()-started,'physics_steps':env.n_physics,
            'goal_error_m':float(np.linalg.norm(env.data.qpos[:2]-goal)),'collision':collision,
            'panorama_looks':looks,'passive_observations':len(decisions),
            'planning_wall_seconds':0.,'path_length_m':float(np.linalg.norm(np.diff(np.asarray(trace)[:,1:3],axis=0),axis=1).sum()) if len(trace)>1 else 0.,
            'motor_controller':'learned_v4','motor_model_sha256':sha(ROOT/world.cfg['physical_control_model']),
            'sensor':'planar simulated visibility, not production RGB-D',
            'geometry':'convex extrusions of scan footprints, not original scan triangles',
            'decisions':decisions,'trajectory_sha256':sha(out/'trajectory.npz')}
    write(out/'result.json',result);return result


def evaluate_physics(cfg_path,library_path,training,out,resume=False):
    cfg,library=read(cfg_path),read(library_path);out=Path(out)
    if out.exists() and any(out.iterdir()) and not resume:raise ValueError('Preserve existing physical runs; use --resume')
    out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1)
    model=load_model(Path(training)/'best.pt',cfg['value_iterations'])
    identity={'stage':'running','model_sha256':sha(Path(training)/'best.pt'),
                             'config_sha256':sha(cfg_path),'physics':'MuJoCo 3.17.0, gravity 1.62m/s2',
                             'physical_source_sha256':sha(__file__),
                             'sensor':'planar simulated visibility','new_paid_tasks':0}
    if resume:
        previous=read(out/'identity.json')
        for field in ['model_sha256','config_sha256','physical_source_sha256']:
            if previous[field]!=identity[field]:raise ValueError('Physical resume identity changed: '+field)
    write(out/'identity.json',identity)
    results=[];p=cfg['physical']
    for seed in range(p['seed_start'],p['seed_start']+p['count']):
        world=World(cfg,library,'physical',seed);write(out/'scenes'/f'{seed}.json',world.manifest())
        for method in ['rules_cached_prior','learned']:
            folder=out/f'{seed}-{method}'
            if resume and (folder/'result.json').exists():row=read(folder/'result.json')
            else:
                if folder.exists():
                    # Preserve interrupted physical bytes before rerunning the unfinished episode.
                    folder.rename(folder.with_name(folder.name+'-interrupted-'+str(time.time_ns())))
                row=run(world,method,model,folder)
            results.append(row)
            write(out/'results.json',results);print({k:row[k] for k in ['seed','method','status','goal_error_m','sim_seconds']},flush=True)
    write(out/'summary.json',summary(results))
    identity=read(out/'identity.json');identity.update(stage='complete',episodes=len(results));write(out/'identity.json',identity)
