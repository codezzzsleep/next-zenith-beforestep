"""Render 720p/30-fps JPEG frames from recorded states, never encode video."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import mujoco
import numpy as np
from PIL import Image
from beforestep import scene as S
from beforestep.geometry import imagination as IM
from beforestep.visualization import camera as VZ
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE,make

def inputs(scene,vehicle,kind):
    base=ROUTE/scene['name']/vehicle
    if kind=='rehearsal':
        candidates=sorted((base/'segment1').glob('rehearsal/look*/pane*/full-record/trajectory.npz'))
        pane=candidates[0].parents[1] if candidates else base/'segment1/rehearsal/look1/pane0'
        p=pane/'full-record/trajectory.npz'
        if not p.exists():p=pane/'traj.npz'
        return p,pane
    if kind=='closeup':return base/'segment2/trajectory.npz',None
    return base/'segment1/full-record/trajectory.npz',None

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--vehicle',choices=['A','B','D'],required=True)
    ap.add_argument('--kind',choices=['actual','rehearsal','closeup'],default='actual');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
    scene=json.loads((EVIDENCE/'scene-stress_v8_gate.json').read_text());source,pane=inputs(scene,a.vehicle,a.kind)
    if not source.exists():raise RuntimeError('Requested physical recording does not exist; never substitute another run')
    folder=ROUTE/'handoff/frames'/f'{a.vehicle}-{a.kind}'
    index=folder/'index.json'
    if index.exists() and json.loads(index.read_text())['status']=='complete':print('Terminal frame artifact exists; skipped');sys.exit(0)
    shadow_size=json.loads(index.read_text()).get('shadow_map_size',8192) if index.exists() else 2048
    folder.mkdir(parents=True,exist_ok=True)
    with np.load(source) as data:t=data['t'].copy();q=data['qpos'].copy();phase=data['phase'].copy()
    if a.kind=='closeup':
        ix=np.flatnonzero(np.char.startswith(phase.astype(str),'front-right'))
        if not len(ix):raise RuntimeError('D has no recorded front-right crossing; this clip is incomplete')
        begin=max(float(t[0]),float(t[ix[0]])-1.);end=min(float(t[-1]),float(t[ix[-1]])+1.)
    elif a.vehicle=='B':begin=max(float(t[0]),float(t[-1])-18.);end=float(t[-1])
    elif a.vehicle=='A':
        begin=max(float(t[0]),float(t[-1])-10.);end=float(t[-1])+10.
        other=ROUTE/scene['name']/'A/segment2/fixed/trajectory.npz'
        if other.exists():
            with np.load(other) as d:t=np.r_[t,d['t']];q=np.concatenate([q,d['qpos']]);phase=np.r_[phase,d['phase']]
            end=min(end,float(t[-1]))
        else:end=float(t[-1])
    elif a.kind=='actual' and a.vehicle=='D':
        begin=float(t[0]);end=float(t[-1])
        second=ROUTE/scene['name']/'D/segment2/trajectory.npz'
        if second.exists():
            with np.load(second) as d:t=np.r_[t,d['t'][1:]];q=np.concatenate([q,d['qpos'][1:]]);phase=np.r_[phase,d['phase'][1:]]
            end=float(t[-1])
    else:begin=max(float(t[0]),float(t[-1])-35.);end=max(begin,float(t[-1])-15.)
    samples=begin+np.arange(int(np.floor((end-begin)*30))+1)/30.
    e,rb,meta,threshold=make(scene)
    if pane:
        definition=json.loads((pane/'pane.json').read_text())
        base_spec=json.loads((ROUTE/scene['name']/'D/segment1/world-spec.json').read_text())
        spec=IM.rehearsal_spec(base_spec,definition['objects'],folder/'render-world')
        known_start=len(spec['objects']);spec['objects'].extend(scene['objects'])
        e=S.make_env(spec);rb={f'obstacle{known_start+i}':p['rock'] for i,p in enumerate(scene['provenance'])}
    vm=VZ.video_model(e,rb,width=1280,height=720,off=(1280,720))
    vm.m.vis.quality.shadowsize=shadow_size
    if pane:
        for i in range(len(definition['objects'])):
            body=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_BODY,f'obstacle{i}')
            for gi in range(vm.m.ngeom):
                if vm.m.geom_bodyid[gi]==body:vm.m.geom_rgba[gi]=[.25,.65,.72,1.]
    camera=mujoco.MjvCamera();camera.type=mujoco.mjtCamera.mjCAMERA_FREE
    records={'schema':'beforestep-route-jpeg-frames/v1','status':'running','vehicle':a.vehicle,'kind':a.kind,
        'width':1280,'height':720,'fps':30,'time_range_s':[float(samples[0]),float(samples[-1])],
        'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'physics_advanced':False,'encoded_video':False,
        'shadow_map_size':shadow_size,'sensor_inputs_unchanged':True,'cameras':{},'frames':[]}
    records['sources']=[{'path':str(source.relative_to(ROOT)),'sha256':sha(source)}]
    second=ROUTE/scene['name']/a.vehicle/'segment2/trajectory.npz'
    if a.kind=='actual' and a.vehicle=='D' and second.exists():records['sources'].append({'path':str(second.relative_to(ROOT)),'sha256':sha(second)})
    write(index,records)
    try:
        for ci,name in enumerate(['side_follow','overhead']):
            target=folder/name;target.mkdir(exist_ok=True)
            distance=(1.6 if ci==0 else 2.6) if a.kind=='closeup' else (2.5 if ci==0 else 5.)
            records['cameras'][name]={'azimuth_deg':25. if ci==0 else -90.,'elevation_deg':-25. if ci==0 else -89.,'distance_m':distance}
            camera.azimuth=records['cameras'][name]['azimuth_deg'];camera.elevation=records['cameras'][name]['elevation_deg'];camera.distance=records['cameras'][name]['distance_m']
            for i,stamp in enumerate(samples[:1] if a.preview else samples):
                path=target/f'{i:05d}.jpg'
                if not path.exists():
                    j=min(max(int(np.searchsorted(t,stamp)),1),len(t)-1);u=float(np.clip((stamp-t[j-1])/max(1e-12,t[j]-t[j-1]),0,1))
                    position=q[j-1]*(1-u)+q[j]*u;position[3:7]/=np.linalg.norm(position[3:7])
                    # Display-only state assignment; no physics or command runs.
                    vm.sync(position)
                    camera.lookat[:]=[position[0]+(.05 if ci==0 else .5),position[1] if ci==0 else 0.,position[2]+.12 if ci==0 else .1]
                    for g in range(6):vm.opt.geomgroup[g]=1 if g in (0,1,2) else 0
                    renderer=vm.r;renderer.update_scene(vm.d,camera=camera,scene_option=vm.opt)
                    rgb=renderer.render().copy();temporary=path.with_suffix('.tmp')
                    Image.fromarray(rgb).save(temporary,format='JPEG',quality=88,subsampling=0);temporary.replace(path)
                records['frames'].append({'camera':name,'index':i,'physics_time_s':float(stamp),'path':str(path.relative_to(ROUTE/'handoff')),'bytes':path.stat().st_size,'sha256':sha(path)})
                if i%60==0:write(index,records);print(json.dumps({'clip':folder.name,'camera':name,'rendered':i+1,'total':len(samples)}),flush=True)
            write(index,records)
        records['status']='preview' if a.preview else 'complete';records['finished_at_unix']=time.time();write(index,records)
    finally:VZ.release(vm)
    print(json.dumps({'clip':folder.name,'status':records['status'],'jpg_count':len(records['frames'])}),flush=True)
