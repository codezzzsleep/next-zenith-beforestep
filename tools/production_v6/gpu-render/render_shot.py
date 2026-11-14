"""Render one saved-state shot directly into an H.264 ffmpeg pipe."""
import argparse
import gc
import hashlib
import json
import math
import shutil
import subprocess
import time
from PIL import Image
from bootstrap import *
from common import save, sha

parser=argparse.ArgumentParser()
parser.add_argument('--shot',required=True)
args=parser.parse_args()
gate=json.loads((OUT/'gpu-render/gpu-consistency.json').read_text())
acceptance=json.loads((OUT/'gpu-render/gpu-acceptance.json').read_text())
assert acceptance['accepted'] and acceptance['visual_pair_accepted_by_owner'],'Owner acceptance is required'
assert gate['mean_absolute_channel_difference']<=2 and gate['pixels_exceeding_8_fraction']<=.01,'Updated GPU consistency gate has not passed'
assert acceptance['gpu_frame_sha256']==gate['output_sha256'],'Acceptance must match this GPU frame'
assert 'RTX 4090 D' in gate['GL_RENDERER']
plan=json.loads((OUT/'gpu-render/shot-plan.json').read_text())
shot=next(x for x in plan['shots'] if x['id']==args.shot)
directory=OUT/'shots'
directory.mkdir(exist_ok=True)
ledger=directory/(args.shot+'.json')
dest=directory/(args.shot+'.mp4')
if dest.exists() and ledger.exists():
    previous=json.loads(ledger.read_text())
    if previous.get('status')=='complete' and previous.get('sha256')==sha(dest):
        print(json.dumps(previous,ensure_ascii=False));raise SystemExit(0)

assert shutil.disk_usage('/').used<=20_000_000_000,'GPU used disk exceeds20GB; stop and inspect'

def states(sources):
    times=[];poses=[];original=[]
    for row in sources:
        p=ROOT/row['path']
        assert sha(p)==row['sha256'],p
        z=np.load(p)
        t=z['t'];q=z['qpos']
        assert q.ndim==2 and q.shape[1]==23
        keep=np.ones(len(t),dtype=bool) if not times else t>times[-1][-1]+1e-8
        if keep.any():
            times.append(t[keep]);poses.append(q[keep])
        original.append({'path':row['path'],'sha256':row['sha256'],'saved_range_s':[float(t[0]),float(t[-1])],'median_saved_dt_s':float(np.median(np.diff(t)))})
    t=np.concatenate(times);q=np.concatenate(poses)
    assert np.all(np.diff(t)>0)
    return t,q,original

def interpolate(t,q,requested):
    clipped=float(np.clip(requested,t[0],t[-1]))
    right=int(np.clip(np.searchsorted(t,clipped),1,len(t)-1));left=right-1
    u=float(np.clip((clipped-t[left])/(t[right]-t[left]),0,1))
    pose=q[left]*(1-u)+q[right]*u
    end=q[right,3:7].copy()
    if np.dot(q[left,3:7],end)<0:
        end=-end
    pose[3:7]=q[left,3:7]*(1-u)+end*u
    pose[3:7]/=np.linalg.norm(pose[3:7])
    return pose,clipped,left,right,u

if shot['camera']=='original_sensor_rgb':
    source=ROOT/shot['original_rgb']['path'];assert sha(source)==shot['original_rgb']['sha256']
    image=Image.open(source).convert('RGB');width,height=image.size;count=90;raw=image.tobytes()
    tmp=dest.with_name(dest.stem+'-recording.mp4')
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate','30','-i','pipe:0','-vf','scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2','-an','-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
    metadata={'id':args.shot,'status':'rendering','pid':os.getpid(),'frame_count':count,'duration_s':3,'camera':'original_sensor_rgb','sources':[shot['original_rgb'],shot['original_camera']],'sim_requested_range_s':[16.08,16.08],'original_sensor_inputs_changed':False,'physics_advanced':False,'source_qpos_dimensions':23,'display_interpolation':'Original single RGB photograph held for3s','parameters':{'source_resolution':[width,height],'output_resolution':[1920,1080],'fps':30,'frame_files':False,'sharpening':False,'additional_fill':False,'solar_direction_changed':False,'CG_supersampling':'not applied to original sensor photograph'},'owner_acceptance':acceptance,'ffmpeg_command':command}
    save(ledger,metadata);started=time.monotonic();log=(directory/(args.shot+'-ffmpeg.log')).open('w');process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log,stdout=log)
    try:
        for i in range(count):process.stdin.write(raw)
        process.stdin.close();assert process.wait()==0
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(tmp)]));assert len(probe['streams'])==1 and int(probe['streams'][0]['nb_frames'])==count
        subprocess.run(['ffmpeg','-v','error','-i',str(tmp),'-f','null','-'],check=True);tmp.replace(dest);elapsed=time.monotonic()-started
        metadata.update(status='complete',rendered_frames=count,elapsed_s=elapsed,render_seconds=0,render_seconds_per_frame=0,total_seconds_per_frame=elapsed/count,sha256=sha(dest),bytes=dest.stat().st_size,ffprobe=probe);metadata.pop('pid',None);save(ledger,metadata)
        print(json.dumps({'id':args.shot,'status':'complete','seconds_per_frame':elapsed/count,'sha256':metadata['sha256']}),flush=True)
    finally:
        if process.poll() is None:process.kill();process.wait()
        log.close()
    raise SystemExit(0)

grid=args.shot=='s05-world-grid'
models=[];sequences=[]
if grid:
    for w in shot['worlds']:
        t,q,src=states([w['source']]);sequences.append((t,q,src))
        objects=[str(ROOT/x['path']) for x in w['objects']]
        models.append(build_model(objects=objects,width=960,height=720))
else:
    t,q,src=states(shot['sources']);sequences.append((t,q,src))
    objects=[str(ROOT/x['path']) for x in shot['objects']] if shot.get('objects') else None
    models.append(build_model(shot['scene'],route=shot.get('route'),objects=objects,width=3840,height=2160))

t,q,_=sequences[0]
start=float(t[0] if shot.get('sim_start') is None else shot['sim_start'])
end=float(t[-1] if shot.get('sim_end') is None else shot['sim_end'])
hold=float(shot.get('terminal_hold_s',0))
speed=shot.get('speed')
if speed:
    moving_frames=math.ceil((end-start)/speed*30)
    count=moving_frames+round(hold*30)
    requests=np.minimum(start+np.arange(count)/30*speed,end)
else:
    count=round(shot['duration_s']*30)
    moving=count-round(hold*30)
    requests=np.r_[np.linspace(start,end,moving),np.full(count-moving,end)]

tmp=dest.with_name(dest.stem+'-recording.mp4')
command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
         '-video_size','3840x2160','-framerate','30','-i','pipe:0','-vf','scale=1920:1080:flags=lanczos',
         '-an','-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
if shot.get('transition_annotation'):
    annotation=shot['transition_annotation'];textfile=directory/(args.shot+'-transition.txt');textfile.write_text(annotation['text'])
    import glob
    fonts=glob.glob('/usr/share/fonts/truetype/wqy/*.ttc')+glob.glob('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    assert fonts,'Transition font unavailable'
    filter_index=command.index('-vf')+1
    command[filter_index]+=f",drawtext=fontfile='{fonts[0]}':textfile='{textfile}':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.62:boxborderw=16:x=(w-tw)/2:y=h-th-70:enable='between(t,{annotation['start_s']},{annotation['end_s']})'"
metadata={'id':args.shot,'status':'rendering','pid':os.getpid(),'frame_count':count,'duration_s':count/30,
          'sources':[item for _,_,rows in sequences for item in rows],'camera':shot['camera'],'camera_spec':shot.get('camera_spec'),'base_version':shot.get('base_version'),
          'sim_requested_range_s':[start,end],'sim_clipped_range_s':[float(np.clip(start,t[0],t[-1])),float(np.clip(end,t[0],t[-1]))],
          'display_interpolation':'linear position and hinges; normalized linear quaternion with shortest sign',
          'source_qpos_dimensions':23,'physics_advanced':False,'physics_step_guard_active':True,
          'original_sensor_inputs_changed':False,'parameters':{'render_resolution':[3840,2160],'output_resolution':[1920,1080],
          'shadowsize':8192,'offsamples':4,'shadowclip':3,'znear':.001,'shadow_center_tracks_robot':True,
          'additional_fill':False,'solar_direction_changed':False,'sharpening':False,'frame_files':False},
          'ffmpeg_command':command,'consistency':gate,'owner_acceptance':acceptance,'timing_note':shot.get('timing_note'),
          'transition_annotation':shot.get('transition_annotation'),'source_classification':shot.get('source_classification'),'handoff':shot.get('handoff'),'terminal_hold_s':hold,'models':[],'display_samples':[]}
for vm in models:
    metadata['models'].append({'solar_directions':vm.m.light_dir.tolist(),'extent':float(vm.m.stat.extent),
                              'nq':int(vm.m.nq),'ngeom':int(vm.m.ngeom)})
save(ledger,metadata)
cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
cid=None
if shot['camera']=='front_cam':
    cid=mujoco.mj_name2id(models[0].m,mujoco.mjtObj.mjOBJ_CAMERA,'front_cam');assert cid>=0
started=time.monotonic();render_seconds=0;state_digest=hashlib.sha256()
log=(directory/(args.shot+'-ffmpeg.log')).open('w')
process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log,stdout=log)
try:
    for i,stamp in enumerate(requests):
        if i%30==0:
            assert shutil.disk_usage('/').used<=20_000_000_000,'GPU used disk exceeds20GB'
        frame_start=time.monotonic()
        canvas=np.empty((2160,3840,3),dtype=np.uint8) if grid else None
        for n,(vm,(times,poses,_)) in enumerate(zip(models,sequences)):
            pose,clipped,left,right,u=interpolate(times,poses,float(stamp))
            solar=vm.m.light_dir.copy()
            vm.m.stat.center[:]=pose[:3]
            display_sync(vm,pose);vm.d.time=clipped
            cam.azimuth=-40;cam.elevation=-17;cam.distance=2.1
            cam.lookat[:]=[pose[0]+.12,pose[1],pose[2]*.65]
            if shot['camera']=='low':
                cam.azimuth=25;cam.elevation=-12;cam.distance=1.9;cam.lookat[2]=pose[2]*.6
            elif shot['camera']=='failure':
                cam.azimuth=25;cam.elevation=-16;cam.distance=2.05
            elif shot['camera']=='opening':
                f=float(np.clip((i/30-2)/3,0,1));f=f*f*(3-2*f)
                cam.distance=3.3*(1-f)+2.1*f;cam.elevation=-24*(1-f)-17*f
                initial=poses[0]
                cam.lookat[:]=np.array([initial[0]+.6,initial[1],.22])*(1-f)+np.array([pose[0]+.12,pose[1],pose[2]*.65])*f
            elif shot['camera']=='overview':
                cam.azimuth=-90;cam.elevation=-65;cam.distance=5.4
                cam.lookat[:]=[pose[0]+.35,pose[1],.22]
            if shot.get('camera_spec'):
                cs=shot['camera_spec'];cam.azimuth=cs['azimuth'];cam.elevation=cs['elevation'];cam.distance=cs['distance']
                cam.lookat[:]=[pose[0]+cs.get('x_offset',.08),pose[1]+cs.get('y_offset',0),pose[2]*cs.get('z_scale',.65)+cs.get('z_offset',0)]
                if cs.get('kind')=='opening':
                    u=float(np.clip((i/30-5)/3,0,1));u=u*u*(3-2*u)
                    cam.distance=3.3*(1-u)+cs['distance']*u;cam.elevation=-24*(1-u)+cs['elevation']*u
                    far=np.array([poses[0,0]+.6,poses[0,1],.22]);cam.lookat[:]=far*(1-u)+cam.lookat*u
                elif cs.get('kind')=='gate_overview':
                    cam.lookat[0]=pose[0]+cs.get('x_offset',.35)
            vm.r.update_scene(vm.d,camera=cid if cid is not None else cam,scene_option=vm.opt)
            rgb=vm.r.render()
            if i==0 and n==0:
                from OpenGL import GL
                metadata['GL_RENDERER']=GL.glGetString(GL.GL_RENDERER).decode()
                assert 'RTX 4090 D' in metadata['GL_RENDERER']
            assert np.array_equal(vm.m.light_dir,solar)
            assert np.array_equal(vm.d.qpos,pose)
            state_digest.update(pose.tobytes())
            if grid:
                y,x=divmod(n,4);canvas[y*720:(y+1)*720,x*960:(x+1)*960]=rgb
            else:
                canvas=rgb
            if i in (0,count//2,count-1):
                metadata['display_samples'].append({'frame':i,'world':n,'requested_sim_s':float(stamp),'clipped_sim_s':clipped,'left_row':left,'right_row':right,'interpolation_u':u,'qpos_sha256':hashlib.sha256(pose.tobytes()).hexdigest(),'camera':{'azimuth':float(cam.azimuth),'elevation':float(cam.elevation),'distance':float(cam.distance),'lookat':cam.lookat.tolist()} if cid is None else {'fixed_camera_id':cid}})
        render_seconds+=time.monotonic()-frame_start
        process.stdin.write(canvas.tobytes())
        if i%90==0:
            metadata.update(rendered_frames=i+1,elapsed_s=time.monotonic()-started);save(ledger,metadata)
            print(args.shot,i+1,'/',count,flush=True)
    process.stdin.close()
    assert process.wait()==0,'ffmpeg failed'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(tmp)]))
    streams=probe['streams'];assert len(streams)==1
    stream=streams[0]
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert stream['width']==1920 and stream['height']==1080 and stream['r_frame_rate']=='30/1'
    assert int(stream['nb_frames'])==count
    subprocess.run(['ffmpeg','-v','error','-i',str(tmp),'-f','null','-'],check=True)
    tmp.replace(dest)
    elapsed=time.monotonic()-started
    metadata.update(status='complete',rendered_frames=count,elapsed_s=elapsed,
                    render_seconds=render_seconds,render_seconds_per_frame=render_seconds/count,
                    total_seconds_per_frame=elapsed/count,sha256=sha(dest),bytes=dest.stat().st_size,
                    interpolated_display_state_sha256=state_digest.hexdigest(),ffprobe=probe)
    metadata.pop('pid',None);save(ledger,metadata)
    print(json.dumps({'id':args.shot,'status':'complete','seconds_per_frame':elapsed/count,'sha256':metadata['sha256']},ensure_ascii=False),flush=True)
except BaseException as error:
    metadata.update(status='failed',error=str(error),elapsed_s=time.monotonic()-started)
    save(ledger,metadata)
    if process.poll() is None:
        process.kill();process.wait()
    raise
finally:
    log.close()
    for vm in models:
        VZ.release(vm)
    del models;gc.collect()
