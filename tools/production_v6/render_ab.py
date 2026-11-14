import sys,time,gc,os,json
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[2]),str(Path(__file__).resolve().parents[2]/'src'),str(Path(__file__).resolve().parent)]
from common import *
import mujoco,numpy as np
from PIL import Image,ImageDraw,ImageFont
from ops.crossing_real_footage_capture import vm_for,original
from ops.crossing_showcase_capture import display_sync
from beforestep.visualization import camera as VZ
from photography import original_actor,quality
DIR=OUT/'render-ab';DIR.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
# a reproduces camera.py's 2-sample offscreen setting; a-v5 separately
# reproduces the actual v5 override to four samples. All tests use identical
# original visual meshes, solar direction, exposure and camera.
variants=[('a',1280,720,4096,2,None,None,None,False),('a-v5',1280,720,4096,4,None,None,None,False),
 ('b',1920,1080,4096,2,None,None,None,False),('c',1920,1080,8192,2,None,None,None,False),
 ('d-extent',1920,1080,8192,2,20,None,None,False),('d-clip',1920,1080,8192,2,20,1.5,None,False),
 ('d-near',1920,1080,8192,2,20,1.5,.001,False),('e',1920,1080,8192,4,20,1.5,.001,False),
 ('e-2x',3840,2160,8192,4,20,1.5,.001,False),('f',1920,1080,8192,4,20,1.5,.001,True),
 ('g-clip',1920,1080,8192,4,None,3,.001,False),('h-center',1920,1080,8192,4,None,3,.001,False),
 ('i-fill',1920,1080,8192,4,None,3,.001,True),('j-2x',3840,2160,8192,4,None,3,.001,True),
 ('k-clip6',1920,1080,8192,4,None,6,.001,False),('l-center6',1920,1080,8192,4,None,6,.001,False),
 ('m-fill6',1920,1080,8192,4,None,6,.001,True),('n-2x6',3840,2160,8192,4,None,6,.001,True),
 ('o-16k',1920,1080,16384,4,None,12,.001,False),('p-fill16k',1920,1080,16384,4,None,12,.001,True),
 ('q-2x16k',3840,2160,16384,4,None,12,.001,True)]
sources=[('leg',ROOT/'outputs/crossing/route/stress_v8_gate/prechecks/x9.00-seed22001/leg/trajectory.npz',57.14,True),
 ('r1-wide',original('stress_v8-imagination')[0],70,False)]
rows=json.loads((DIR/'index.json').read_text())['rows'] if (DIR/'index.json').exists() else [];save(DIR/'job.json',{'status':'running','pid':os.getpid(),'sources':[str(p) for _,p,_,_ in sources]})
for label,source,stamp,gate in sources:
 z=np.load(source);j=int(np.argmin(abs(z['t']-stamp)));q=z['qpos'][j].copy();assert q.shape==(23,)
 for name,w,h,shadow,samples,extent,clip,near,fill in variants:
  dest=DIR/f'{label}-{name}.png'
  if dest.exists():continue
  start=time.monotonic();vm=vm_for('stress_v8',OUT/'render'/label,w,h,gate=gate);original_actor(vm);quality(vm,exposure=True)
  orig={'extent':float(vm.m.stat.extent),'shadowclip':float(vm.m.vis.map.shadowclip),'znear':float(vm.m.vis.map.znear)}
  vm.m.vis.quality.shadowsize=shadow;vm.m.vis.quality.offsamples=samples
  if extent is not None:vm.m.stat.extent=extent
  if clip is not None:vm.m.vis.map.shadowclip=clip
  if near is not None:vm.m.vis.map.znear=near
  tracks=name in ['h-center','i-fill','j-2x','l-center6','m-fill6','n-2x6']
  if tracks:vm.m.stat.center[:]=q[:3]
  if fill:vm.m.vis.headlight.ambient=[.28,.28,.30];vm.m.vis.headlight.diffuse=[.20,.20,.20];vm.m.vis.headlight.specular=[0,0,0]
  display_sync(vm,q);cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
  if gate:cam.azimuth=25;cam.elevation=-12;cam.distance=1.9;cam.lookat[:]=[q[0]+.12,q[1],q[2]*.6]
  else:cam.azimuth=-55;cam.elevation=-25;cam.distance=7;cam.lookat[:]=[5.4,-.1,.22]
  solar=vm.m.light_dir.copy();vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt);rgb=vm.r.render().copy()
  assert np.array_equal(solar,vm.m.light_dir) and np.array_equal(q,vm.d.qpos)
  im=Image.fromarray(rgb)
  if (w,h)!=(1920,1080):im=im.resize((1920,1080),Image.Resampling.LANCZOS)
  raw=DIR/f'{label}-{name}-clean.png';im.save(raw)
  params={'render_resolution':[w,h],'shadowsize':shadow,'offsamples':samples,'extent':float(vm.m.stat.extent),'shadowclip':float(vm.m.vis.map.shadowclip),'znear':float(vm.m.vis.map.znear),'center':vm.m.stat.center.tolist(),'shadow_center_tracks_robot':tracks,'non_shadow_headlight_fill':fill,'unchanged_solar_direction':True,'sharpening':False,'original_settings':orig}
  annotated=Image.new('RGB',(1920,1160),'#111111');annotated.paste(im,(0,80));draw=ImageDraw.Draw(annotated)
  draw.text((16,8),f'{label} / {name} / saved t={float(z["t"][j]):.3f}s / source={w}x{h}',font=font,fill='white')
  draw.text((16,40),f'shadow={shadow}, samples={samples}, extent={params["extent"]:.3f}, clip={params["shadowclip"]}, znear={params["znear"]}, fill={fill}',font=font,fill='white');annotated.save(dest)
  row={'id':label+'-'+name,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_row':j,'saved_sim_s':float(z['t'][j]),'qpos_sha256':__import__('hashlib').sha256(q.tobytes()).hexdigest(),'parameters':params,'file':str(dest),'sha256':sha(dest),'clean_file':str(raw),'clean_sha256':sha(raw),'elapsed_s':time.monotonic()-start};rows.append(row);save(DIR/'index.json',{'status':'in_progress','rows':rows,'acceptance':'Await Claude visual choice; these are display-only experiments, no physics or sensor changes'})
  VZ.release(vm);del vm;gc.collect();print(row['id'],round(row['elapsed_s'],2),flush=True)
 status('B 对照图组 '+label,DIR/'index.json','对照图已完成，待负责人视觉选择参数')
save(DIR/'index.json',{'status':'awaiting_visual_selection','rows':rows,'acceptance':'Claude selects parameters; C must wait','physics_advanced':False,'solar_direction_changed':False})
save(DIR/'job.json',{'status':'complete','rows':len(rows),'acceptance':'pending'})
status('B 全部单变量对照',DIR/'index.json','生成通过；视觉验收待负责人选参')
