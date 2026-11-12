"""Same actual scans, frozen RGB-D and rule motor control, independent new policies."""
from pathlib import Path
import time
import numpy as np
from beforestep import scene as S
from beforestep.navigation import map as N,controller as F
from beforestep.strict_pipeline import Recorder,initialize_recorded_look
from .common import ROOT,OUT,read,write,sha,finite
from .geometry import apply_scene
from .sensor import ProductionSensor,transplanted_qpos
from .policies import evidence,decide


def run(world,method,model,threshold,out,recorded=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'result.json').exists(),'Never overwrite a completed physical result'
    write(out/'world.json',world.manifest());sensor=ProductionSensor(world.definition,out/'physical');env=sensor.env
    if recorded is not None:initialize_recorded_look(env,recorded)
    else:sensor.set_qpos(transplanted_qpos(world.capsule))
    rec=Recorder();rec.frame(env,'START','start');watch=N.contact_watch(env,[r['body'] for r in sensor.meta['rocks'].values()]+sensor.meta['walls']);crash={}
    def monitor(e):
        hit,info=watch(e)
        if hit:crash.update(info)
        return hit
    env.physics_monitor=monitor;rec.monitor=monitor
    source_t=env.t;t0=time.monotonic();states=[];zmaps=[];observations=[];status='stopped';probabilities=[]
    radius=world.cfg['known_launch_radius_m'] if getattr(world,'launch_clear',False) else N.R_DRIVE
    known=N.swept([env.data.qpos[:2]],r=radius);candidates=world.imagination()
    try:
        for k in range(world.cfg['max_looks']):
            apply_scene(world.definition);position=env.data.qpos[:2].copy();yaw=F.yaw_of(env.data.qpos)
            if recorded is not None and k==0:
                directory=Path(recorded)/'looks';statefile=directory/'look1_fused_state.npy'
                if not statefile.exists():statefile=directory/'look1_state.npy'
                ob={'state':np.load(statefile),'zmax':np.load(directory/'look1_zmax.npy')}
            else:ob=N.observe(sensor.vm,env)
            states.append(ob['state']);zmaps.append(ob['zmax']);state=N.fuse(states);zmax=np.max(np.stack(zmaps),0)
            card=evidence(state,zmax,candidates,known,position,yaw,world.definition['sun'],world.ground)
            card['look_history']=[(np.array(o['position']),o['yaw']) for o in observations]
            action,probability,occ=decide(card,method,world.goal,world.cfg['max_looks']-k-1,model,threshold)
            if probability is not None:probabilities.append(probability.astype(np.float16))
            observations.append({'position':position.tolist(),'yaw':float(yaw),'action':finite(action),'state_sha256':__import__('hashlib').sha256(state.tobytes()).hexdigest()})
            np.save(out/f'look{k+1}_state.npy',state);np.save(out/f'look{k+1}_zmax.npy',zmax)
            if not rec.hold(env,'look',world.cfg['look_seconds']):status='collision';break
            if action['kind']=='stop':break
            motion=F.run_waypoints(env,action['path'],log=rec,phase=f'after_look{k+1}',on_step=monitor,final_yaw=action.get('yaw') if action['kind']=='look' else None)
            observations[-1]['motion']={'completed':motion.completed,'collided':motion.collision,'reason':motion.reason,'errors_m':motion.errors}
            if motion.collision or crash:status='collision';break
            if not motion.completed:status='controller_failed';break
            known|=N.swept(np.asarray(rec.q)[:,:2])
            if action['kind']=='go':status='arrived';break
        rec.save(out/'traj.npz')
        if probabilities:np.savez_compressed(out/'risk.npz',*probabilities)
        result={'method':method,'status':status,'seed':world.seed,'scene':world.definition['id'],'capsule_id':world.capsule['id'],
                'looks':len(observations),'sim_seconds':env.t-source_t,'wall_seconds':time.monotonic()-t0,
                'goal_error_m':float(np.linalg.norm(env.data.qpos[:2]-world.goal)),'collision':crash or None,'observations':observations,
                'trajectory_sha256':sha(out/'traj.npz'),'recorded_first_observation':str(recorded) if recorded else None,
                'controller':'Frozen rules controller; dynamics are MuJoCo, poses are assigned only at initialization',
                'sensor':'Frozen production RGB-D; first real-scene look is preserved observation reuse','new_lux_tasks':0,
                'initialization':'Declare start before environment construction, then load saved camera/robot pose',
                'mujoco_warning_counts':[int(w.number) for w in env.data.warning]}
        write(out/'result.json',finite(result));return result
    finally:
        if not (out/'traj.npz').exists():rec.save(out/'traj.npz')
        sensor.close()


def real_world(scene):
    from .world import World
    from .geometry import scene_height
    cfg=read(ROOT/'experimental/arena/parameters.json')
    library=read(ROOT/cfg.get('capsule_library','evidence/learning/arena_v2/capsules.json'));caps=[c for c in library['capsules'] if c['eligible'] and c['scene']==scene and c.get('source_look')=='look1']
    assert caps,scene;source=caps[0];w=object.__new__(World);w.seed=0;w.split='real-heldout';w.cfg=read(ROOT/'experimental/arena/parameters.json')
    w.definition=read(ROOT/'config/scenes'/f'{scene}.json');w.definition['sun']=S.sun_settings(w.definition)
    w.height,w.ground=scene_height(w.definition);w.raw=w.height>=N.ROCK_Z;w.nogo=N.prior_nogo();w.truth_occ=w.raw|w.nogo
    w.capsule={**source,'transplant_world_from_source':np.eye(4).tolist(),'deviations':{'camera_distance_ratio':1.,'view_azimuth_deviation_deg':0.,'sun_relative_azimuth_deviation_deg':0.},'candidates':[]};seen=set()
    for c in caps:
        for candidate in c['candidates']:
            if candidate['task_id'] not in seen:w.capsule['candidates'].append(candidate);seen.add(candidate['task_id'])
    w.start=np.array([source['local_frame']['x0'],source['local_frame']['y0']])
    w.cfg={**w.cfg,'max_looks':5}
    w.goal=np.array(w.definition['goal']);w.heading=source['local_frame']['yaw0'];w.family='real'
    w.launch_clear=not (w.raw&N.swept([w.start],r=w.cfg['known_launch_radius_m'])).any()
    w._sensor=None;w._sensor_cache={};w.look_count=0;w.first_camera=source['camera_world']
    observation=ROOT/source['observation'];recorded=observation.parents[2]
    assert (recorded/'looks/look1_state.npy').exists(),recorded
    return w,recorded
