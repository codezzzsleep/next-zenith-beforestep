"""Frozen v72 crossing plus observed-space approach and shared task outcomes."""
import copy,json,time
from pathlib import Path
import numpy as np
import trimesh
from .runtime import *
from .action import crossing
from .scene import generate,track_geometry

PASS={'clean_pass','wheel_contact_pass'}


def yaw_of(e):
    w,x,y,z=e.data.qpos[3:7];return float(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))


def goto(rec,pose,target,phase,timeout=45.,speed=.12):
    started=rec.e.t
    while rec.e.t-started<timeout:
        dx,dy=np.array(target)-rec.e.data.qpos[:2];distance=float(np.hypot(dx,dy))
        if distance<.06:return True
        heading=np.arctan2(dy,dx);error=(heading-yaw_of(rec.e)+np.pi)%(2*np.pi)-np.pi
        v=min(speed,max(.025,distance*.45))*max(0.,np.cos(error)) if abs(error)<.55 else 0.
        # Direct wheel linear-speed feedback, with the same .15m/s cap.
        turn=float(np.clip(.65*error,-.15,.15));omega=np.array([(v+(-1 if leg in ['FL','RL'] else 1)*turn)/WHEEL_R for leg in LEG])
        if not rec.command(pose,np.clip(omega,-.15/WHEEL_R,.15/WHEEL_R),phase=phase):return False
    return False


def align(rec,pose,heading=0.,timeout=45.):
    started=rec.e.t;integral=0.
    while rec.e.t-started<timeout:
        error=(heading-yaw_of(rec.e)+np.pi)%(2*np.pi)-np.pi
        if abs(error)<.02:
            return transition(rec,pose,.6,'ready-brake')
        integral=float(np.clip(integral+error/rec.e.control_hz,-.5,.5))
        turn=float(np.clip(1.5*error+.5*integral,-.15,.15));omega=np.array([(-1 if leg in ['FL','RL'] else 1)*turn/WHEEL_R for leg in LEG])
        if not rec.command(pose,omega,phase='ready-align'):return False
    return False


def observed_geometry(obs,lateral=0.):
    points=np.load(Path(obs)/'visible_points_world.npy')
    return {'near':[float(points[:,0].min())]*2,'far':[float(points[:,0].max())]*2,
            'high':[float(points[:,2].max())]*2,'lateral':lateral,
            'definition':'B uses the farthest and highest actually observed stone point; same envelope on both wheel tracks'}


def geometry_for(mesh,lateral=0.):
    g=track_geometry(mesh,lateral)
    v=mesh.vertices;body=v[np.abs(v[:,1]-lateral)<.33]
    g['body_high']=float(body[:,2].max()) if len(body) else None
    return g


def make_env(scene,obs,objects=None):
    spec=copy.deepcopy(scene['spec']);spec['goal_x']=4.;spec['channel']['half_width']=2.
    if objects is not None:spec['objects']=objects
    e=WheelLegEnv(spec,control_hz=50,max_seconds=240,nav_base=False,tip_deg=60)
    with np.load(Path(obs)/'physical-state.npz') as st:
        e.data.qpos[:]=st['qpos'];e.data.qvel[:]=st['qvel']
    # Initialization from the one saved physical observation, never during action.
    mujoco.mj_forward(e.model,e.data);return e


def execute(scene,obs,geometry,folder,method,objects=None):
    folder=Path(folder)
    if (folder/'result.json').exists():return json.loads((folder/'result.json').read_text())
    folder.mkdir(parents=True,exist_ok=True);e=make_env(scene,obs,objects);rec=Record(e);rec.frame('observed-initial-state');started=time.monotonic()
    pose=stance_array(STANCE);near=observed_geometry(obs)['near'][0]
    ok=transition(rec,pose,1.,'prepare-normal-stance')
    if ok:ok=goto(rec,pose,[near-.65,0.],'prepare-at-threshold')
    if ok:ok=align(rec,pose)
    preparation_end=e.t;preparation_success=ok;stages=[]
    if ok:ok,stages=crossing(rec,geometry)
    if ok:ok=goto(rec,stance_array(STANCE_HIGH),[4.,geometry.get('lateral',0.)],'reach-known-goal',timeout=max(.1,240.-e.t))
    summary=rec.summary();success=ok and e.data.qpos[0]>=3.94 and abs(e.data.qpos[1])<=.4
    status=('clean_pass' if success and not summary['steps_with_wheel_stone'] else 'wheel_contact_pass' if success else
            'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else 'stuck')
    rec.save(folder);row={'schema':'beforestep-crossing-execution/v1','method':method,'seed':scene['seed'],'revision':scene['revision'],
        'status':status,'sim_seconds':e.t,'wall_seconds':time.monotonic()-started,'preparation_end_s':preparation_end,
        'action_started':bool(preparation_success),'geometry_input':geometry,'contact':summary,'stages':stages,'last_phase':rec.phase[-1],
        'final_base':e.data.qpos[:7].tolist(),'final_wheel_centres':wheel_positions(e).tolist(),
        'goal_xy':[4.,0.],'goal_tolerance_m':{'longitudinal':.06,'lateral':.4},'time_limit_s':240.,'speed_cap_m_s':.15,
        'action_sha256':sha(ROOT/'experimental/crossing/action.py'),'scene':e.spec,'observation':str(Path(obs).relative_to(ROOT)),
        'trajectory_sha256':sha(folder/'trajectory.npz'),'contacts_sha256':sha(folder/'contacts.npz'),
        'raw_path':str(folder.relative_to(ROOT)),'diagnostic_only':method=='E','excluded_from_formal_statistics':True}
    write(folder/'result.json',row);return row
