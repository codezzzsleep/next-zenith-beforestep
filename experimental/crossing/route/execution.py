"""Continuous two-segment execution with a complete saved physical handoff."""
import copy, hashlib, json, sys, time
from pathlib import Path
import mujoco
import numpy as np
from PIL import Image
from beforestep import scene as S, pipeline as P
from beforestep.navigation import map as N
from beforestep.geometry import imagination as IM, camera as Camera
from beforestep.visualization import camera as VZ
from experimental.crossing.runtime import *
from experimental.crossing.execution import goto, align, observed_geometry
from experimental.crossing.action import crossing
from .world import ROUTE, EVIDENCE, register, make, footprint

def hashes(e):
    return {k:hashlib.sha256(np.asarray(getattr(e.data,k),dtype=np.float64).tobytes()).hexdigest() for k in ('qpos','qvel')}

def save_physical(e, folder):
    write(Path(folder)/'world-spec.json',e.spec)
    write(Path(folder)/'physical-state.json',e.save_state())
    np.savez_compressed(Path(folder)/'physical-state.npz',qpos=e.data.qpos.copy(),qvel=e.data.qvel.copy(),ctrl=e.data.ctrl.copy(),time=np.array(e.data.time))

def first_segment(scene, folder, policy, imagine='lux', reuse=None, max_looks=None):
    """Invoke the unchanged pipeline in-process and retain its live environment."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    register(scene)
    original_make=S.make_env
    original_rehearsal=IM.rehearsal_spec
    original_recorder=P.Recorder
    live=[]
    captures=[]
    def make_env(spec):
        e=original_make(spec)
        index=int(spec.get('route_threshold_index',0))
        record=Record(e,index)
        known_watch=N.contact_watch(e,[f'obstacle{i}' for i in range(len(spec['objects'])-3,len(spec['objects']))]) if spec.get('route_known_objects') else None
        original_step=e.step_command
        def step(*args,**kwargs):
            old=e.physics_monitor
            def monitor(env):
                record.monitor(env)  # Measurement only; the frozen watch decides.
                hit=bool(old(env)) if old is not None and old!=record.monitor else False
                # Appended terrain receives the original any-part contact rule,
                # including in panes whose frozen watch enumerates only the
                # original imagined rocks and known wall.
                return hit or bool(known_watch(env)[0]) if known_watch else hit
            e.physics_monitor=monitor
            try:return original_step(*args,**kwargs)
            finally:
                e.physics_monitor=old
                record.frame('first-segment-control')
        e.step_command=step
        e._route_capture=(record,original_step)
        captures.append((e,record,original_step))
        if not live:live.append((e,record,original_step))
        return e
    def rehearsal_spec(spec,objects,destination):
        result=original_rehearsal(spec,objects,destination)
        # The original generator replaces all obstacles. Append only the new
        # known terrain to every pane, leaving all imagined high-rock candidates.
        result['objects'].extend(copy.deepcopy(scene['objects']))
        result.pop('route_threshold_index',None)
        return result
    class Recorder(original_recorder):
        def frame(self,env,kind,phase):
            self.route_env=env
            return super().frame(env,kind,phase)
        def save(self,path):
            super().save(path)
            env=getattr(self,'route_env',None)
            if env is not None and live and env is not live[0][0]:
                record,original_step=env._route_capture
                record.save(Path(path).parent/'full-record')
                env.step_command=original_step
                captures[:]=[r for r in captures if r[0] is not env]
                del env._route_capture
                del self.route_env
    S.make_env=make_env;IM.rehearsal_spec=rehearsal_spec
    P.Recorder=Recorder
    argv=['beforestep run','--scene',scene['name'],'--controller-model','rules',
          '--policy',policy,'--imagine',imagine,'--out',str(folder),'--tag','segment1']
    if reuse:argv+=['--reuse-lux',str(reuse)]
    if max_looks:argv+=['--max-looks',str(max_looks)]
    sys.argv=argv
    code=0
    try:P.main()
    except SystemExit as error:code=int(error.code or 0)
    finally:
        S.make_env=original_make;IM.rehearsal_spec=original_rehearsal;P.Recorder=original_recorder
    if not live:raise RuntimeError('Pipeline did not create a live environment')
    e,record,original_step=live[0]
    e.step_command=original_step
    output=folder/'segment1'
    output.mkdir(exist_ok=True)
    record.save(output/'full-record')
    save_physical(e,output)
    write(output/'physical-summary.json',record.summary())
    for i,(pane,rec,_) in enumerate(captures[1:]):
        rec.save(output/f'full-rehearsal-{i:02d}')
    if code:raise SystemExit(code)
    summary=json.loads((output/'summary.json').read_text())
    return e,summary,output

def observe_threshold(e, rb, index, destination):
    """One passive RGB-D photograph: use lit, visible threshold pixels only."""
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    vm=VZ.video_model(e,rb,width=1600,height=1200,off=VZ.HI)
    vm.hi_sensor=True;vm.sync(e.data.qpos)
    try:
        rgb,depth=VZ.camera_rgbd(vm)
        cid=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_CAMERA,'front_cam')
        renderer=VZ.hi_renderer(vm)
        renderer.enable_segmentation_rendering()
        renderer.update_scene(vm.d,camera=cid,scene_option=vm.opt)
        seg=renderer.render().copy();renderer.disable_segmentation_rendering()
        target=np.isin(seg[:,:,0],vm.rock_geoms[f'obstacle{index}'])&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
        target=np.asarray(Image.fromarray(target.astype(np.uint8)*255).resize((1600,1200),Image.Resampling.NEAREST))>127
        dark=VZ.dark_mask(rgb,.10)
        snap=Camera.capture(vm.m,vm.d,cid,1600,1200)
        valid=np.where(dark,np.nan,depth).astype(np.float32)
        points,ys,xs=Camera.unproject_depth(valid,snap)
        keep=target[ys,xs]&(points[:,2]>=.04)
        points=points[keep]
        if len(points)<20:raise RuntimeError('Threshold photograph has insufficient visible points')
        mask=np.zeros(depth.shape,dtype=bool);mask[ys[keep],xs[keep]]=True
        Image.fromarray(rgb).save(destination/'raw.png')
        Image.fromarray(mask.astype(np.uint8)*255).save(destination/'mask.png')
        np.save(destination/'depth.npy',valid)
        np.save(destination/'visible_points_world.npy',points)
        write(destination/'camera_world.json',snap)
        save_physical(e,destination)
        geometry=observed_geometry(destination)
        height=max(geometry['high']);depth_m=max(np.array(geometry['far'])-np.array(geometry['near']))
        gate=json.loads((ROOT/'evidence/crossing/calibration/gate.json').read_text())
        # Frozen next-sampled-height capability, exactly as the existing decision.
        limit=.20 if height<=.12 else .15 if height<=.15 else 0.
        decision={'source':'actual passive RGB-D photograph; lit visible threshold only','visible_points':len(points),
            'geometry':geometry,'height_m':height,'depth_m':float(depth_m),'d_max_m':limit,
            'within_frozen_capability':bool(height<=.15 and depth_m<=limit),'lux_tasks':0,
            'action_sha256':sha(ROOT/'experimental/crossing/action.py')}
        write(destination/'geometry-decision.json',decision)
        return geometry,decision
    finally:VZ.release(vm)

def leg_segment(e, scene, rb, index, folder, truth=False):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    rec=Record(e,index);rec.frame('continuous-handoff')
    begin=e.t;e.max_seconds=e.t+300.;e.spec['goal_x']=scene['goal'][0]
    e.nav_base=False;e.tip_deg=60.;e.passed_at=None
    pose=stance_array(STANCE)
    ok=transition(rec,pose,1.,'prepare-normal-stance')
    if ok:ok=goto(rec,pose,scene['staging_xy'],'staging-point')
    if ok:ok=align(rec,pose)
    if truth:
        geometry=scene['truth_geometry'];decision={'source':'true geometry diagnostic','within_frozen_capability':True,'geometry':geometry,'lux_tasks':0}
        write(folder/'geometry-decision.json',decision)
    elif ok:
        geometry,decision=observe_threshold(e,rb,index,folder/'observation')
        if not decision['within_frozen_capability']:ok=False
    else:geometry=None;decision={'source':'photograph not reached','within_frozen_capability':False}
    stages=[]
    if ok:ok=goto(rec,pose,[min(geometry['near'])-.65,0.],'prepare-at-threshold')
    if ok:ok=align(rec,pose)
    if ok:ok,stages=crossing(rec,geometry)
    if ok:ok=goto(rec,stance_array(STANCE_HIGH),scene['goal'],'reach-route-goal',timeout=max(.1,e.max_seconds-e.t))
    contact=rec.summary()
    arrived=bool(ok and np.linalg.norm(e.data.qpos[:2]-scene['goal'])<.3 and min(wheel_positions(e)[:,0])>max(scene['truth_geometry']['far']))
    status=('clean_pass' if arrived and not contact['steps_with_wheel_stone'] else 'wheel_contact_pass' if arrived else
        'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else
        'stopped' if geometry is not None and not decision['within_frozen_capability'] else 'stuck')
    rec.save(folder);save_physical(e,folder)
    result={'schema':'beforestep-crossing-route-leg-segment/v1','status':status,'arrived':arrived,'sim_seconds':e.t-begin,
        'contact':contact,'geometry_decision':decision,'stages':stages,'final_base':e.data.qpos[:7].tolist(),
        'final_wheels':wheel_positions(e).tolist(),'goal':scene['goal'],'last_phase':rec.phase[-1],
        'action_sha256':sha(ROOT/'experimental/crossing/action.py'),'truth_diagnostic':truth}
    write(folder/'result.json',result);return result

def wheel_trial(e,scene,index,folder,stance='fixed',lateral=0.,seconds=240.):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    rec=Record(e,index);rec.frame('wheel-trial-start');start=e.t
    e.max_seconds=start+seconds;e.spec['goal_x']=scene['goal'][0];e.tip_deg=60.;e.nav_base=False;e.passed_at=None
    pose=stance_array(STANCE if stance=='fixed' else STANCE_HIGH)
    ok=transition(rec,pose,2.,'normal' if stance=='fixed' else 'high')
    if ok:ok=align(rec,pose)
    arrived=False
    while ok and e.t-start<seconds:
        if np.linalg.norm(e.data.qpos[:2]-scene['goal'])<.3 and min(wheel_positions(e)[:,0])>max(scene['truth_geometry']['far']):arrived=True;break
        w,x,y,z=e.data.qpos[3:7];yaw=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
        turn=float(np.clip(-.8*yaw+.6*(lateral-e.data.qpos[1]),-.20,.20));v=min(.12,.03+(e.t-start)*.08)
        omega=np.array([(v+(-1 if leg in ['FL','RL'] else 1)*turn*.192)/WHEEL_R for leg in LEG])
        ok=rec.command(pose,np.clip(omega,-.15/WHEEL_R,.15/WHEEL_R),phase='wheel-only')
    contact=rec.summary()
    status=('wheel_contact_pass' if arrived else 'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else 'stuck')
    rec.save(folder);save_physical(e,folder)
    result={'schema':'beforestep-crossing-route-wheel-trial/v1','stance':stance,'lateral_m':lateral,'status':status,
        'arrived':arrived,'sim_seconds':e.t-start,'time_limit_s':seconds,'contact':contact,
        'final_base':e.data.qpos[:7].tolist(),'final_wheels':wheel_positions(e).tolist(),'speed_cap_m_s':.15}
    write(folder/'result.json',result);return result
