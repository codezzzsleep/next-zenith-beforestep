"""Rerecord original states with legible cameras and no physics steps."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,gc
from common import ROOT, OUT as PRODUCTION_OUT, TOOLS
WORK=PRODUCTION_OUT/'legacy-capture';OUT=WORK/'media'
WORK.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(TOOLS)]
import mujoco,numpy as np
from PIL import Image
from ops.crossing_real_footage_capture import vm_for,original
from ops.crossing_showcase_capture import display_sync,verify_display_sync
from beforestep.visualization import camera as VZ
from photography import original_actor,quality
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2));tmp.replace(p)
def record(name,vm,source,requests,camera,extra=()):
 fps=30;count=len(requests);dest=OUT/(name+'.mp4');ledger=WORK/'captures'/(name+'.json')
 if dest.exists() and ledger.exists() and json.loads(ledger.read_text()).get('status')=='complete':return
 a=np.load(source);t=a['t'];q=a['qpos'];assert q.shape[1]==23
 right=np.searchsorted(t,np.clip(requests,t[0],t[-1])).clip(0,len(t)-1);left=(right-1).clip(0,len(t)-1)
 indices=np.where(abs(t[right]-requests)<abs(t[left]-requests),right,left);indices[requests>=t[-1]]=len(t)-1
 camera_spec={'source_resolution':[1280,720],'fps':30,'shadowsize':4096,'offsamples':4,'original_robot_visual_meshes':True,'same_sun_direction':True,'external_exposure_and_fill_only':True}
 meta={'status':'recording','pid':os.getpid(),'id':name,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'qpos_dimensions':23,'exact_saved_qpos':True,'physics_advanced':False,'source_time_range_s':[float(t[indices[0]]),float(t[indices[-1]])],'duration_s':count/fps,'camera':camera,'photography':camera_spec,'original_sensor_images_unchanged':True,'extra_sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in extra],'frame_map':[{'output_s':i/fps,'requested_sim_s':float(requests[i]),'source_row':int(j),'saved_sim_s':float(t[j])} for i,j in enumerate(indices)]}
 meta['transform_verification']=verify_display_sync(vm,[q[indices[k]] for k in (0,count//2,count-1)]);save(ledger,meta);OUT.mkdir(exist_ok=True);(WORK/'qc').mkdir(exist_ok=True)
 cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
 tmp=dest.with_name(dest.stem+'-recording.mp4');started=time.monotonic()
 cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x720','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-crf','18','-preset','veryfast','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for i,j in enumerate(indices):
   pose=q[j];display_sync(vm,pose);cam.azimuth=-40;cam.elevation=-17;cam.distance=2.1;cam.lookat[:]=[pose[0]+.12,pose[1],pose[2]*.65]
   if camera=='opening' and i<60:
    cam.distance=3.3;cam.elevation=-24;cam.lookat[:]=[q[indices[0]][0]+.6,q[indices[0]][1],.22]
   elif camera=='low':cam.azimuth=25;cam.elevation=-12;cam.distance=1.9;cam.lookat[2]=pose[2]*.6
   elif camera=='failure':cam.azimuth=25;cam.elevation=-16;cam.distance=2.05
   vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt);rgb=vm.r.render().copy();proc.stdin.write(rgb.tobytes())
   if i in (0,count//2,count-1):Image.fromarray(rgb).save(WORK/'qc'/f'{name}-{i}.jpg',quality=94)
   if i%90==0:meta['rendered_frames']=i+1;save(ledger,meta);print(name,i+1,'/',count,'elapsed',round(time.monotonic()-started),flush=True)
  proc.stdin.close();assert proc.wait()==0
 except BaseException:
  proc.kill();proc.wait();raise
 tmp.replace(dest);meta.update(status='complete',rendered_frames=count,sha256=sha(dest),path=str(dest),elapsed_s=round(time.monotonic()-started,2));meta.pop('pid');save(ledger,meta);print('COMPLETE',name,flush=True)
def model(scene,objects=None,gate=False):
 vm=vm_for(scene,WORK/'render'/scene,1280,720,objects=objects,gate=gate);original_actor(vm);quality(vm,exposure=True);return vm
def stamps(a,b,seconds,clamp=False):
 n=round(seconds*30);return np.minimum(a+np.arange(n)/30,b) if clamp else np.linspace(a,b,n)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--group',choices=['main','worlds','comparison'],required=True);group=ap.parse_args().group
 save(WORK/f'worker-{group}.json',{'status':'recording','pid':os.getpid(),'group':group})
 if group=='main':
  p=original('stress_v8-imagination')[0];vm=model('stress_v8')
  try:
   for name,start,end,duration,camera in [('opening',1.2,16.08,15,'opening'),('observation',14.08,16.08,8,'close'),('tail',98,112.84,17,'close')]:record(name,vm,p,stamps(start,end,duration,clamp=True),camera)
  finally:VZ.release(vm);del vm;gc.collect()
  base=ROOT/'outputs/crossing/route/stress_v8_gate/prechecks/x9.00-seed22001';vm=model('stress_v8',gate=True)
  try:
   record('wheel',vm,base/'wheel-fixed-center/trajectory.npz',stamps(6.654,11.654,5,clamp=True),'low')
   record('lift',vm,base/'leg/trajectory.npz',stamps(50.14,64.14,14,clamp=True),'low')
   record('depart',vm,base/'leg/trajectory.npz',stamps(167.08,173.08,6,clamp=True),'low')
  finally:VZ.release(vm);del vm;gc.collect()
  p=original('suite_r2_v4_F3_004-imagination')[0];vm=model('suite_r2_v4_F3_004')
  try:record('failure',vm,p,stamps(70.14,82.14,12),'failure',extra=(p.parent/'summary.json',))
  finally:VZ.release(vm)
 elif group=='worlds':
  for i in range(12):
   source,identity=original(f'world-{i:02d}');pane=ROOT/identity['world_source']['pane'];data=json.loads(pane.read_text());vm=model('stress_v8',objects=data['objects'])
   try:record(f'world-{i:02d}',vm,source,stamps(0,96.18,18) if i==0 else stamps(25,41,2),'close',extra=(pane,))
   finally:VZ.release(vm);del vm;gc.collect()
 else:
  request=np.interp(np.arange(1260)/30,[0,18*40/42,22*40/42,28*40/42,33*40/42,37*40/42,40,42],[1.2,75,82.5,107,114.5,138,142.2,142.2]);request[-1]=142.2;vm=model('stress_v8')
  try:
   for policy in ['optimistic','conservative','imagination']:record('comparison-'+policy,vm,original('stress_v8-'+policy)[0],request,'close')
  finally:VZ.release(vm)
 save(WORK/f'worker-{group}.json',{'status':'complete','group':group})
if __name__=='__main__':main()
