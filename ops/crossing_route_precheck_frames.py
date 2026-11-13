"""Replay the four authorized diagnostics; never advance physical simulation."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import mujoco
import numpy as np
import trimesh
from PIL import Image
from beforestep.visualization import camera as VZ
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE,make

def load(path):
    with np.load(path) as data:return {key:data[key].copy() for key in data.files}

def specification(scene,clip):
    base=ROUTE/scene['name'];pre=base/'prechecks'/scene['attempt']
    leg=pre/'leg/trajectory.npz'
    if clip=='wheel-stuck':
        source=pre/'wheel-fixed-center/trajectory.npz';data=load(source)
        contacts=load(source.parent/'contacts.npz')
        # Contacts are recorded at physics frequency, including the first touch.
        columns=contacts['counts'];keys=['wheel_ground','wheel_threshold','body_stone','unstable']
        touches=columns[:,keys.index('wheel_threshold')]>0
        first=float(contacts['t'][np.flatnonzero(touches)[0]])
        return [source],data,max(float(data['t'][0]),first-3),min(float(data['t'][-1]),first+12),1,first
    if clip in ('leg-cross','sill-close'):
        data=load(leg);phases=data['phase'].astype(str)
        lifted=np.flatnonzero(np.char.endswith(phases,'-lift'))
        begin=float(data['t'][lifted[0]])
        edge=trimesh.load(ROOT/scene['mesh_paths'][0],force='mesh',process=False).bounds[1,0]
        passed=np.flatnonzero(np.min(data['wheel_centres'][:,:,0]-.084,axis=1)>edge)
        end=float(data['t'][passed[passed>lifted[0]][0]])
        return [leg],data,begin,end,1,None
    first=pre/'detour/segment1/full-record/trajectory.npz'
    second=base/'connection-precheck/observed-leg-segment/trajectory.npz'
    a,b=load(first),load(second)
    assert np.allclose(a['qpos'][-1],b['qpos'][0],atol=1e-12)
    assert np.allclose(a['qvel'][-1],b['qvel'][0],atol=1e-12)
    data={k:np.concatenate([a[k],b[k][1:]]) for k in ['t','qpos','phase']}
    return [first,second],data,float(data['t'][0]),float(data['t'][-1]),4,None

def render(clip,preview=False):
    scene=json.loads((EVIDENCE/'scene-stress_v8_gate.json').read_text())
    folder=ROUTE/'handoff/frames'/clip;folder.mkdir(parents=True,exist_ok=True);index=folder/'index.json'
    old=json.loads(index.read_text()) if index.exists() else {}
    if old.get('status')=='complete':print(clip+' complete; skipped',flush=True);return
    sources,data,begin,end,speed,contact=specification(scene,clip)
    stamps=begin+np.arange(int((end-begin)*30/speed)+1)*speed/30
    record={'schema':'beforestep-route-jpeg-frames/v1','status':'running','clip':clip,'width':1280,'height':720,'fps':30,
        'source_runs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sources],
        'source':'recorded zero-paid precheck; real physics, true scanned sill geometry',
        'formal_vehicle_run':False,'scene':scene['name'],'scene_sha256':sha(EVIDENCE/'scene-stress_v8_gate.json'),
        'threshold_sha256':sha(ROOT/scene['mesh_paths'][0]),'physics_advanced':False,
        'time_range_s':[begin,end],'playback_speed':speed,'first_wheel_contact_s':contact,'cameras':{},'frames':[]}
    write(index,record)
    e,rb,_,_=make(scene);vm=VZ.video_model(e,rb,width=1280,height=720,off=(1280,720))
    vm.m.vis.quality.shadowsize=2048
    cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
    cameras=['overhead'] if clip=='connect' else ['side_follow','overhead']
    t,q=data['t'],data['qpos']
    try:
        for name in cameras:
            target=folder/name;target.mkdir(exist_ok=True)
            close=clip=='sill-close';side=name=='side_follow'
            cam.azimuth=25 if side else -90;cam.elevation=-18 if side else -89
            cam.distance=(1.65 if side else 2.3) if close else 2.5 if side else 5
            record['cameras'][name]={'azimuth_deg':cam.azimuth,'elevation_deg':cam.elevation,'distance_m':cam.distance,'closeup':close}
            for i,stamp in enumerate(stamps[:1] if preview else stamps):
                path=target/f'{i:05d}.jpg'
                if not path.exists():
                    j=int(np.clip(np.searchsorted(t,stamp),1,len(t)-1));u=float(np.clip((stamp-t[j-1])/(t[j]-t[j-1]),0,1))
                    position=q[j-1]*(1-u)+q[j]*u;position[3:7]/=np.linalg.norm(position[3:7])
                    vm.sync(position)
                    cam.lookat[:]=[9.08,0,.16] if close else [position[0]+(.05 if side else .5),position[1] if side else 0,position[2]+.12 if side else .1]
                    for g in range(6):vm.opt.geomgroup[g]=1 if g in (0,1,2) else 0
                    vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt)
                    tmp=path.with_suffix('.tmp');Image.fromarray(vm.r.render().copy()).save(tmp,format='JPEG',quality=88,subsampling=0);tmp.replace(path)
                record['frames'].append({'camera':name,'index':i,'physics_time_s':float(stamp),'path':str(path.relative_to(ROUTE/'handoff')),'sha256':sha(path),'bytes':path.stat().st_size})
                if i%60==0:write(index,record);print(json.dumps({'clip':clip,'camera':name,'done':i+1,'total':len(stamps)}),flush=True)
            write(index,record)
        record.update(status='preview' if preview else 'complete',finished_at_unix=time.time());write(index,record)
    finally:VZ.release(vm)
    print(json.dumps({'clip':clip,'status':record['status'],'jpg_count':len(record['frames'])}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--clip',choices=['wheel-stuck','leg-cross','sill-close','connect','all'],default='all');p.add_argument('--preview',action='store_true');a=p.parse_args()
    for clip in ['wheel-stuck','leg-cross','sill-close','connect'] if a.clip=='all' else [a.clip]:render(clip,a.preview)
