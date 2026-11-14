"""Repair the recorded-page title using a keyframe-bounded video splice."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import load_state, resolve, OUT,sha,save,status

work=OUT/'film';source=OUT/'demo-v6.mp4';splice=work/'title-splice';splice.mkdir(exist_ok=True)
history=work/'history/before-photo-title-cleanup';history.mkdir(parents=True,exist_ok=True)
original_sha=sha(source)
packets=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-show_packets',
    '-show_entries','stream=time_base:packet=pts,dts,flags','-of','json',str(source)],text=True))
num,den=map(int,packets['streams'][0]['time_base'].split('/'));tb=num/den
keys=[p for p in packets['packets'] if 'K' in p['flags']]
first=next(p for p in keys if abs(p['pts']*tb-41)<1e-5)
last=next(p for p in keys if p['pts']*tb>=51)
start=first['pts']*tb;end=last['pts']*tb
start_frame=round(start*30);end_frame=round(end*30);middle_frames=end_frame-start_frame
job={'id':'photo-title-keyframe-correction','pid':os.getpid(),'status':'running','original_sha256':original_sha,
     'corrected_picture_interval_s':[41,51],'reencoded_GOP_interval_s':[start,end],'reencoded_frames':middle_frames,
     'current':None,'new_physics_runs':0,'new_Lux3D_tasks':0,'gpu_shutdown':False}
save(work/'title-correction-job.json',job)
state=load_state(work / 'state.json');state.update(status='correcting_recorded_page_title',live_jobs=[{'id':job['id'],'pid':job['pid'],'ledger':str(work/'title-correction-job.json')}]);save(work/'state.json',state)
def run(command,label):
    with (splice/(label+'.log')).open('w') as log:
        p=subprocess.Popen(command,stdout=log,stderr=log);job['current']={'stage':label,'pid':p.pid,'command':command};save(work/'title-correction-job.json',job)
        assert p.wait()==0,label
def frames(path):
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames:format=duration','-of','json',str(path)],text=True))
    return int(p['streams'][0]['nb_frames']),float(p['format']['duration'])
def frame_hashes(path,label):
    dest=splice/(label+'.framemd5')
    run(['ffmpeg','-v','error','-y','-threads','2','-i',str(path),'-map','0:v:0','-f','framemd5',str(dest)],label)
    return [line.rsplit(',',1)[1].strip() for line in dest.read_text().splitlines() if line and not line.startswith('#')]

try:
    before=splice/'before.mp4';after=splice/'after.mp4';middle=splice/'middle.mp4'
    run(['ffmpeg','-v','error','-y','-i',str(source),'-map','0:v:0','-an','-c','copy','-t',f'{first["dts"]*tb:.9f}',
         '-avoid_negative_ts','disabled',str(before)],'copy-before')
    assert frames(before)[0]==start_frame,(frames(before),start_frame)
    run(['ffmpeg','-v','error','-y','-ss',f'{end:.9f}','-i',str(source),'-map','0:v:0','-an','-c','copy','-avoid_negative_ts','disabled',str(after)],'copy-after')
    assert frames(after)[0]==5550-end_frame,(frames(after),5550-end_frame)
    mini=splice/'raw-model-shots.txt';mini.write_text(''.join("file '"+str(work/'parts'/(name+'.mkv'))+"'\n" for name in ['photo','glbA','glbB']))
    filters=f"setpts=PTS+{start}/TB,drawbox=x=0:y=0:w=iw:h=120:color=0x090e11:t=fill:enable='lt(t,51)',drawbox=x=0:y=920:w=iw:h=160:color=black@0.64:t=fill,ass={work/'film.ass'},setpts=PTS-STARTPTS"
    run(['ffmpeg','-v','warning','-y','-filter_threads','1','-threads','2','-f','concat','-safe','0','-i',str(mini),'-vf',filters,
         '-frames:v',str(middle_frames),'-an','-r','30','-c:v','libx264','-crf','14','-preset','slow','-threads','3','-pix_fmt','yuv420p',str(middle)],'encode-corrected-page-header')
    assert frames(middle)[0]==middle_frames
    listing=splice/'splice.txt';listing.write_text(''.join("file '"+str(p)+"'\n" for p in [before,middle,after]))
    corrected=splice/'demo-v6-corrected.mp4'
    run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(source),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','copy','-movflags','+faststart',str(corrected)],'mux-corrected-film')
    count,duration=frames(corrected);assert count==5550 and abs(duration-185)<.1,(count,duration)
    old_hashes=frame_hashes(source,'original-frames');new_hashes=frame_hashes(corrected,'corrected-frames')
    assert len(old_hashes)==len(new_hashes)==5550
    mismatches=[i for i,(a,b) in enumerate(zip(old_hashes,new_hashes)) if a!=b and not start_frame<=i<end_frame]
    assert not mismatches,mismatches[:20]
    old_audio=splice/'original-audio.aac';new_audio=splice/'corrected-audio.aac'
    for src,dest in [(source,old_audio),(corrected,new_audio)]:run(['ffmpeg','-v','error','-y','-i',str(src),'-map','0:a:0','-c','copy',str(dest)],dest.stem)
    assert sha(old_audio)==sha(new_audio)
    assert sha(source)==original_sha
    source.rename(history/'demo-v6-first-encode.mp4');corrected.replace(source)
    job.update(status='complete',current=None,final_sha256=sha(source),protected_frames=5550-middle_frames,
               outside_GOP_decoded_frames_identical=True,AAC_packets_identical=True,original_film=str(history/'demo-v6-first-encode.mp4'),
               finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(work/'title-correction-job.json',job)
    delivery=json.loads((work/'delivery.json').read_text());delivery.update(status='corrected_pending_final_verification',sha256=sha(source),bytes=source.stat().st_size,
              title_layout_correction=str(work/'title-correction-job.json'));save(work/'delivery.json',delivery)
    state.update(status='title_layout_corrected_pending_final_verification',live_jobs=[],next='Repeat final decode/representative frames and browser seek on this final SHA; finish ZIP');save(work/'state.json',state)
    status('照片转模型页头修正完成',work/'title-correction-job.json',f'通过：仅41–51s清旧页头；{middle_frames}帧GOP重压，其他{5550-middle_frames}帧逐解码hash完全相同，AAC原包完全相同；185秒/5550帧，首版保全')
    print(json.dumps({'passed':True,'reencoded_frames':middle_frames,'protected_frames':5550-middle_frames,'sha256':job['final_sha256']},ensure_ascii=False))
except BaseException as e:
    job.update(status='failed',error=str(e));save(work/'title-correction-job.json',job)
    state.update(status='title_correction_error_review_required',live_jobs=[],next='Inspect splice logs; source first film retained untouched until all checks pass');save(work/'state.json',state)
    raise
