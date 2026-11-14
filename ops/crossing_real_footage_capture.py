"""Camera recordings of exact saved joint states for the 180-second film."""
import argparse,gc,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
WORK=ROOT.parent/'real-footage-180';OUT=ROOT/'site/media/real-footage'
import mujoco,numpy as np
from PIL import Image
from beforestep import scene as S
from beforestep.visualization import camera as VZ
from beforestep.geometry import imagination as IM
from ops.crossing_showcase_capture import display_sync,verify_display_sync

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2));tmp.replace(p)
def original(name):
 manifest=json.loads((ROOT/'site/data/footage.json').read_text());c=manifest['clips'][name]
 p=ROOT/c['source'];assert sha(p)==c['source_sha256'];return p,c
def vm_for(scene,folder,width,height,objects=None,gate=False):
 S.configure('stress_v8' if gate else scene);spec,rb,_=S.scene_spec(folder)
 if gate:
  d=json.loads((ROOT/'evidence/crossing/route/scene-stress_v8_gate.json').read_text())
  for item,pr in zip(d['objects'],d['provenance']):rb[f'obstacle{len(spec["objects"])}']=pr['rock'];spec['objects'].append(item)
  spec['goal_x']=d['goal'][0]
 if objects is not None:spec=IM.rehearsal_spec(spec,objects,folder/'imagined-world');rb={}
 env=S.make_env(spec);vm=VZ.video_model(env,rb,width=width,height=height,off=(width,height));vm.m.vis.quality.shadowsize=1024
 if objects:
  for gi in range(vm.m.ngeom):
   name=mujoco.mj_id2name(vm.m,mujoco.mjtObj.mjOBJ_BODY,int(vm.m.geom_bodyid[gi])) or ''
   if name.startswith('obstacle'):vm.m.geom_rgba[gi]=[.43,.46,.48,1]
 for g in range(6):vm.opt.geomgroup[g]=int(g in (0,1,2))
 return vm

def record(name,source,scene,duration,requested,width=1280,height=720,camera='follow',objects=None,gate=False,extra=()):
 dest=OUT/(name+'.mp4');ledger=WORK/'captures'/(name+'.json')
 if ledger.exists() and dest.exists() and json.loads(ledger.read_text()).get('status')=='complete':return
 fps=15;count=round(duration*fps);assert len(requested)==count
 a=np.load(source);times=a['t'];poses=a['qpos'];assert poses.shape[1]==23
 clipped=np.clip(requested,times[0],times[-1]);right=np.searchsorted(times,clipped).clip(0,len(times)-1);left=(right-1).clip(0,len(times)-1)
 indices=np.where(np.abs(times[right]-clipped)<np.abs(times[left]-clipped),right,left);indices[requested>=times[-1]]=len(times)-1
 vm=vm_for(scene,WORK/'render'/name,width,height,objects,gate)
 meta={'status':'recording','id':name,'pid':os.getpid(),'scene':scene,'camera':camera,'camera_source_resolution':[width,height],'output_fps':30,'render_sample_fps':fps,'duration_s':duration,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_time_range_s':[float(clipped[0]),float(clipped[-1])],'source_qpos_dimension':23,'exact_saved_qpos':True,'physics_advanced':False,'new_physics_runs':0,'new_generation_tasks':0,'path':str(dest.relative_to(ROOT/'site')),'frame_map':[{'output_s':i/fps,'requested_sim_s':float(requested[i]),'saved_sim_s':float(times[j]),'source_row':int(j),'terminal_hold':bool(requested[i]>times[-1])} for i,j in enumerate(indices)],'additional_sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in extra]}
 meta['display_transform_verification']=verify_display_sync(vm,[poses[indices[i]] for i in (0,count//2,count-1)])
 if gate:meta.update(formal_vehicle_run=False,scene_sha256=sha(ROOT/'evidence/crossing/route/scene-stress_v8_gate.json'))
 if objects:meta['candidate_meshes']=[{'path':str(Path(p).relative_to(ROOT)),'sha256':sha(p)} for p in objects]
 if camera=='front_cam':
  cid=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_CAMERA,'front_cam');assert cid>=0
  snapshot=json.loads((ROOT/'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/camera_world.json').read_text())
  j=int(np.argmin(np.abs(times-16.08)));display_sync(vm,poses[j]);position_error=float(np.max(np.abs(vm.d.cam_xpos[cid]-np.array(snapshot['world_pos']))));assert position_error<1e-6,position_error
  meta['original_camera_position_error_m']=position_error;meta['original_camera_fovy_deg']=float(vm.m.cam_fovy[cid]);assert abs(vm.m.cam_fovy[cid]-snapshot['fovy_deg'])<1e-6
 save(ledger,meta);OUT.mkdir(parents=True,exist_ok=True);(WORK/'qc').mkdir(exist_ok=True);(WORK/'logs').mkdir(exist_ok=True)
 tmp=dest.with_name(dest.stem+'-recording.mp4');cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate',str(fps),'-i','pipe:0','-vf','fps=30','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
 cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
 try:
  with (WORK/'logs'/(name+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,stdout=log)
   try:
    for i,j in enumerate(indices):
     pos=poses[j];display_sync(vm,pos);vm.d.time=float(times[j])
     cam.azimuth=-40;cam.elevation=-27;cam.distance=3.7;cam.lookat[:]=[pos[0]+.4,pos[1],pos[2]+.12]
     if camera=='opening':
      cam.azimuth=-55;cam.elevation=-22;cam.distance=4.2;cam.lookat[:]=[pos[0]+.5,pos[1],pos[2]+.12]
      if i<2*fps:cam.lookat[:]=[poses[indices[0]][0]+.5,poses[indices[0]][1],poses[indices[0]][2]+.12]
     elif camera=='fixed-establishing':cam.azimuth=-55;cam.elevation=-24;cam.distance=5.2;cam.lookat[:]=[1.35,-.45,.22]
     elif camera=='side_follow':cam.azimuth=25;cam.elevation=-18;cam.distance=2.5;cam.lookat[:]=[pos[0]+.22,pos[1],pos[2]+.07]
     elif camera=='failure':cam.azimuth=25;cam.elevation=-23;cam.distance=2.5;cam.lookat[:]=[pos[0]+.25,pos[1],pos[2]+.1]
     elif camera=='comparison':cam.azimuth=-40;cam.elevation=-32;cam.distance=3.5;cam.lookat[:]=[pos[0]+.38,pos[1],pos[2]+.1]
     actual_camera=cid if camera=='front_cam' else cam
     vm.r.update_scene(vm.d,camera=actual_camera,scene_option=vm.opt);rgb=vm.r.render().copy();proc.stdin.write(rgb.tobytes())
     if i in (0,count//2,count-1):Image.fromarray(rgb).save(WORK/'qc'/f'{name}-{i}.jpg',quality=94)
     if i%60==0:meta['rendered_frames']=i+1;save(ledger,meta);print(name,i+1,'/',count,flush=True)
    proc.stdin.close();assert proc.wait()==0
   finally:
    if proc.poll() is None:proc.kill();proc.wait()
  tmp.replace(dest);meta.update(status='complete',sha256=sha(dest),bytes=dest.stat().st_size,rendered_frames=count);meta.pop('pid',None)
  Image.open(WORK/'qc'/f'{name}-{count//2}.jpg').save(OUT/(name+'.jpg'),quality=92);meta['poster']=str((OUT/(name+'.jpg')).relative_to(ROOT/'site'));save(ledger,meta)
  save(ROOT/'site/data/real-footage-sources'/(name+'.json'),meta);print('RECORDED',name,flush=True)
 finally:VZ.release(vm);del vm;gc.collect()

def stamps(start,end,seconds,speed=None):
 n=round(seconds*15)
 if speed is None:return np.linspace(start,end,n)
 return np.minimum(start+np.arange(n)/15*speed,end)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--group',choices=['depart','r1','comparison','world-failure','establish'],required=True);group=ap.parse_args().group
 WORK.mkdir(exist_ok=True);save(WORK/('worker-'+group+'.json'),{'status':'recording','pid':os.getpid(),'group':group,'physics_advanced':False})
 if group=='depart':
  p=ROOT/'outputs/crossing/route/stress_v8_gate/prechecks/x9.00-seed22001/leg/trajectory.npz';record('low-stone-depart',p,'stress_v8_gate',6,stamps(167.08,173.08,6),camera='side_follow',gate=True)
 elif group=='r1':
  p,c=original('stress_v8-imagination')
  record('r1-opening',p,'stress_v8',15,stamps(1.2,16.08,15,1),camera='opening')
  record('r1-tail',p,'stress_v8',17,stamps(98,112.84,17,1),camera='follow')
  record('r1-observation-external',p,'stress_v8',8,stamps(14.08,16.08,8,1),camera='follow')
  record('r1-first-person',p,'stress_v8',6,stamps(14.08,16.08,6,1),width=960,height=720,camera='front_cam',extra=(ROOT/'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/camera_world.json',))
 elif group=='comparison':
  out=np.arange(42*15)/15;requested=np.interp(out,[0,18,22,28,33,37,42],[1.2,75,82.5,107,114.5,138,142.2]);requested[-1]=142.2
  save(WORK/'comparison-clock.json',{'seconds':42,'output_knots_s':[0,18,22,28,33,37,42],'sim_knots_s':[1.2,75,82.5,107,114.5,138,142.2],'shared_clock':True,'camera':'same follow camera parameters and initial view','terminal_holds_at_each_original_end':True})
  for policy in ['optimistic','conservative','imagination']:
   p,c=original('stress_v8-'+policy);record('r1-synchronised-'+policy,p,'stress_v8',42,requested,width=416,height=702,camera='comparison')
 elif group=='establish':
  p,c=original('stress_v8-imagination');record('r1-opening-fixed',p,'stress_v8',15,stamps(1.2,16.08,15,1),camera='fixed-establishing');record('r1-opening-follow',p,'stress_v8',15,stamps(1.2,16.08,15,1),camera='follow')
 else:
  p,c=original('world-00');pane=ROOT/c['world_source']['pane'];d=json.loads(pane.read_text());assert d['completed'] and not d['collided'];record('rehearsal-full-00',p,'stress_v8',18,stamps(0,96.18,18),objects=d['objects'],extra=(pane,))
  p,c=original('suite_r2_v4_F3_004-imagination');record('f3-004-contact',p,'suite_r2_v4_F3_004',12,stamps(70.14,82.14,12),camera='failure',extra=(p.parent/'summary.json',))
 save(WORK/('worker-'+group+'.json'),{'status':'complete','group':group})
if __name__=='__main__':main()
