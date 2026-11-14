"""Film the original recorded states in their actual MuJoCo/Lux3D worlds.

No integration, planning, new observations, or generation calls. Video is a
camera recording of saved runs; source meshes, joints, times and outcomes stay fixed.
"""
import argparse,copy,gc,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
WORK=ROOT.parent/'showcase-real-footage';OUT=ROOT/'site/media/footage'
import numpy as np
import mujoco
from PIL import Image
from beforestep import scene as S
from beforestep.visualization import camera as VZ
from beforestep.geometry import imagination as IM

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2));t.replace(p)
def display_sync(vm,qpos):
 # Recorded states need coordinate transforms and camera/light positions only.
 # Recomputing a collision solver while filming advances no useful display state.
 vm.d.qpos[:]=qpos;vm.d.qvel[:]=0
 mujoco.mj_kinematics(vm.m,vm.d);mujoco.mj_comPos(vm.m,vm.d);mujoco.mj_camlight(vm.m,vm.d)
def verify_display_sync(vm,poses):
 rows=[]
 for q in poses:
  vm.sync(q)
  expected={k:getattr(vm.d,k).copy() for k in ('xpos','xmat','geom_xpos','geom_xmat','cam_xpos','cam_xmat','light_xpos','light_xdir')}
  display_sync(vm,q)
  errors={k:float(np.max(np.abs(getattr(vm.d,k)-a))) if a.size else 0 for k,a in expected.items()}
  assert max(errors.values())<1e-12,errors;rows.append(errors)
 return {'passed':True,'states_checked':len(rows),'maximum_transform_error':max(max(x.values()) for x in rows),'no_physics_solver_during_display':True}
def film(vm,source,name,scene,seconds=14,world_source=None,arrays=None,extra_sources=()):
 OUT.mkdir(parents=True,exist_ok=True);index=WORK/'clips'/f'{name}.json';dest=OUT/f'{name}.mp4'
 if index.exists() and dest.exists() and json.loads(index.read_text()).get('status')=='complete':return json.loads(index.read_text())
 if arrays is None:
  a=np.load(source);t=a['t'];q=a['qpos']
 else:t,q=arrays
 fps=12;count=int(seconds*fps)
 vm.m.vis.quality.shadowsize=1024
 record={'status':'running','pid':os.getpid(),'id':name,'scene':scene,'path':str(dest.relative_to(ROOT/'site')),
 'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_time_range_s':[float(t[0]),float(t[-1])],
 'clip_duration_s':seconds,'sample_fps':fps,'video_fps':30,'width':864,'height':486,'physics_advanced':False,
 'recording_type':'original_saved_MuJoCo_states_rendered_in_original_world','approx_speed':float((t[-1]-t[0])/seconds)}
 if world_source:record['world_source']=world_source
 record['source_files']=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [source,*extra_sources]]
 record['display_transform_verification']=verify_display_sync(vm,[q[0],q[len(q)//2],q[-1]])
 save(index,record);log=WORK/'logs'/f'{name}.log';tmp=dest.with_name(dest.stem+'-recording.mp4')
 cmd=['ffmpeg','-hide_banner','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','864x486','-framerate',str(fps),'-i','pipe:0','-an','-vf','fps=30','-c:v','libx264','-preset','veryfast','-crf','20','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
 cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
 for g in range(6):vm.opt.geomgroup[g]=1 if g in (0,1,2) else 0
 with log.open('w') as stream:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stream,stderr=stream)
  try:
   for i,stamp in enumerate(np.linspace(float(t[0]),float(t[-1]),count)):
    j=min(max(int(np.searchsorted(t,stamp)),1),len(t)-1);u=float(np.clip((stamp-t[j-1])/max(1e-12,t[j]-t[j-1]),0,1))
    pos=q[j-1]*(1-u)+q[j]*u;pos[3:7]/=np.linalg.norm(pos[3:7]);display_sync(vm,pos)
    cam.azimuth=-40.;cam.elevation=-30.;cam.distance=3.5;cam.lookat[:]=[pos[0]+.45,pos[1],pos[2]+.12]
    # A real second camera angle, taken from the same recorded states.
    if i>=count*.65:cam.azimuth=-80.;cam.elevation=-62.;cam.distance=4.8
    if world_source and world_source.get('diagnostic_not_formal'):
     cam.azimuth=25.;cam.elevation=-25.;cam.distance=2.4;cam.lookat[:]=[pos[0]+.22,pos[1],pos[2]+.1]
    vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt);rgb=vm.r.render().copy();proc.stdin.write(rgb.tobytes())
    if i in (0,count//2,count-1):Image.fromarray(rgb).save(WORK/'qc'/f'{name}-{i}.jpg',quality=92)
    if i%60==0:record['rendered_frames']=i+1;save(index,record)
   proc.stdin.close();assert proc.wait()==0,'ffmpeg failed'
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
 tmp.replace(dest);record.update(status='complete',sha256=sha(dest),bytes=dest.stat().st_size,rendered_frames=count)
 Image.open(WORK/'qc'/f'{name}-0.jpg').save(OUT/f'{name}.jpg',quality=90)
 record['poster']=str((OUT/f'{name}.jpg').relative_to(ROOT/'site'));save(index,record)
 print('FILMED',name,flush=True);return record

def model(scene,folder,objects=None):
 S.configure(scene);spec,rb,_=S.scene_spec(folder)
 if objects is not None:
  spec=IM.rehearsal_spec(spec,objects,folder/'imagined-world');rb={}
 env=S.make_env(spec);vm=VZ.video_model(env,rb,width=864,height=486,off=(864,486));vm.m.vis.quality.shadowsize=2048
 if objects:
  for i in range(len(spec['objects'])):
   bid=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_BODY,f'obstacle{i}')
   for gi in range(vm.m.ngeom):
    if vm.m.geom_bodyid[gi]==bid:vm.m.geom_rgba[gi]=[.43,.46,.48,1]
 return vm

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--group',choices=['worlds','levels','holdouts','routes','rejected'],required=True);a=ap.parse_args()
 WORK.mkdir(exist_ok=True);(WORK/'qc').mkdir(exist_ok=True);(WORK/'logs').mkdir(exist_ok=True)
 save(WORK/f'worker-{a.group}.json',{'status':'running','pid':os.getpid(),'group':a.group,'new_physics_runs':0,'new_generation_tasks':0})
 if a.group=='worlds':
  base=ROOT/'evidence/reviews/beforestep_r1/lux/original_b/rehearsal/look1'
  for i in range(12):
   f=base/f'pane{i}';d=json.loads((f/'pane.json').read_text());assert d['completed'] and not d['collided']
   if (WORK/'clips'/f'world-{i:02d}.json').exists() and json.loads((WORK/'clips'/f'world-{i:02d}.json').read_text()).get('status')=='complete':continue
   vm=model('stress_v8',WORK/'render/worlds'/str(i),d['objects'])
   try:film(vm,f/'traj.npz',f'world-{i:02d}','stress_v8',12,{'pane':str((f/'pane.json').relative_to(ROOT)),'sha256':sha(f/'pane.json'),'candidate_meshes':[{'path':str(Path(p).relative_to(ROOT)),'sha256':sha(p)} for p in d['objects']]})
   finally:VZ.release(vm);del vm;gc.collect()
 elif a.group=='rejected':
  ledger=ROOT/'outputs/suite/counterfactuals/suite_r2_v4_F0_001/counterfactuals.json';d=json.loads(ledger.read_text());case=d['runs']['look1_T2_A1'];candidate=next(c for c in d['candidates'] if c['look']==1 and c['target']=='T2' and c['candidate']=='A1')
  assert case['executed'] and case['collision'] and case['prefix_verification']['passed']
  assert candidate['original_rejection']['admitted'] is False
  vm=model('suite_r2_v4_F0_001',WORK/'render/rejected')
  try:film(vm,ROOT/case['run']/'traj.npz','rejected-6339854','suite_r2_v4_F0_001',14,{'diagnostic_not_formal':True,'task_id':6339854,'rejected_in_original_run':True,'ledger':str(ledger.relative_to(ROOT)),'sha256':sha(ledger),'prefix_verified':True,'source_decision':candidate['source_decision']})
  finally:VZ.release(vm);del vm;gc.collect()
 elif a.group=='routes':
  for scene_path in sorted((ROOT/'evidence/crossing/route').glob('scene-*.json')):
   scene=json.loads(scene_path.read_text())
   if scene.get('name') not in ['stress_v8_gate','suite_r2_v4_F1_003_gate','suite_r2_v4_F2_001_gate','suite_r2_v4_F2_007_gate']:continue
   S.configure(scene['base_scene']);spec,rb,_=S.scene_spec(WORK/'render/routes'/scene['name'])
   for item,pr in zip(scene['objects'],scene['provenance']):
    rb[f'obstacle{len(spec["objects"])}']=pr['rock'];spec['objects'].append(item)
   spec['goal_x']=scene['goal'][0];env=S.make_env(spec);vm=VZ.video_model(env,rb,width=864,height=486,off=(864,486));vm.m.vis.quality.shadowsize=2048
   try:
    for vehicle in ['A','B','C','D']:
     base=ROOT/'outputs/crossing/route'/scene['name']/vehicle;p1=base/'segment1/full-record/trajectory.npz'
     if not p1.exists():raise RuntimeError(str(p1))
     data=np.load(p1);t=data['t'];q=data['qpos'];extra=[]
     parts=[base/'segment2/trajectory.npz'] if vehicle in ['B','D'] else [base/'segment2/fixed/trajectory.npz',base/'segment2/high/trajectory.npz'] if vehicle=='A' else []
     for p in parts:
      if not p.exists():continue
      d=np.load(p);ix=np.flatnonzero(d['t']>t[-1]+1e-8)
      if len(ix):t=np.r_[t,d['t'][ix]];q=np.concatenate([q,d['qpos'][ix]]);extra.append(p)
     film(vm,p1,scene['name']+'-'+vehicle,scene['name'],18,{'scene':str(scene_path.relative_to(ROOT)),'sha256':sha(scene_path)},(t,q),extra)
   finally:VZ.release(vm);del vm;gc.collect()
 else:
  data=json.loads((ROOT/'site/data/levels.json').read_text())['levels']
  if a.group=='holdouts':
   summary=json.loads((ROOT/'evidence/reviews/beforestep_r3/summary.json').read_text())
   data=[{'id':r['scene'],'runs':{k:{'source':v['run']} for k,v in r['runs'].items() if k in ('imagination','imagination_strict') and v.get('run')}} for r in summary['holdouts']]
  for row in data:
   scene=row['id'];vm=None
   try:
    for policy,run in row['runs'].items():
     if policy not in ('optimistic','conservative','imagination','imagination_strict'):continue
     name=scene+'-'+policy
     if (WORK/'clips'/f'{name}.json').exists() and json.loads((WORK/'clips'/f'{name}.json').read_text()).get('status')=='complete':continue
     if vm is None:vm=model(scene,WORK/'render'/scene)
     film(vm,ROOT/run['source']/'traj.npz',name,scene)
   finally:
    if vm:VZ.release(vm);del vm;gc.collect()
 save(WORK/f'worker-{a.group}.json',{'status':'complete','pid':os.getpid(),'group':a.group})
if __name__=='__main__':main()
