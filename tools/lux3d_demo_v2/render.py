"""Stream the retained Demo through presentation animation, then mux its new soundtrack."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from PIL import Image
from common import OUT,BASE,save,sha,now
from motion import Animator,W,H,FPS,tl,source

parser=argparse.ArgumentParser()
parser.add_argument('--preview',nargs=2,type=float,metavar=('START','END'))
args=parser.parse_args()
start,end=args.preview or (0,tl['duration_s'])
start_frame=round(start*FPS);end_frame=round(end*FPS);count=end_frame-start_frame
assert 0<=start_frame<end_frame<=tl['frames']
assert (OUT/'soundtrack.wav').is_file(),'Prepare the complete soundtrack before rendering'
name=f'preview-{start:g}-{end:g}' if args.preview else 'BeforeStep-Lux3D-Demo-v2'
destination=OUT/(name+'.mp4');assert not destination.exists(),'Preserve completed versions before rebuilding'
temporary=OUT/(name+'-encoding.mp4')
job={'id':name,'status':'running','pid':os.getpid(),'started_utc':now(),'frames':count,'done':0,
     'source_sha256':sha(source),'new_physics_runs':0,'new_Lux3D_tasks':0,'new_TTS_requests':0}
save(OUT/'render-job.json',job)
state={'status':'rendering_preview' if args.preview else 'rendering_final','live_jobs':[{'id':name,'pid':os.getpid(),'ledger':str(OUT/'render-job.json')}],
       'next':'Inspect motion and music, then encode full revised Demo' if args.preview else 'Verify complete decode, transition frames, mix and playback'}
save(OUT/'state.json',state)
animator=Animator()
decode_log=(OUT/'logs'/(name+'-decode.log')).open('w')
encode_log=(OUT/'logs'/(name+'-encode.log')).open('w')
decoder=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-ss',str(start_frame/FPS),'-i',str(source),
    '-frames:v',str(count),'-an','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=decode_log)
encoder=subprocess.Popen(['ffmpeg','-v','warning','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080',
    '-framerate','30','-i','pipe:0','-ss',str(start_frame/FPS),'-i',str(OUT/'soundtrack.wav'),
    '-map','0:v:0','-map','1:a:0','-frames:v',str(count),'-t',str(count/FPS),'-c:v','libx264',
    '-crf','18' if args.preview else '14','-preset','veryfast' if args.preview else 'slow','-threads','3',
    '-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-movflags','+faststart',str(temporary)],
    stdin=subprocess.PIPE,stdout=encode_log,stderr=encode_log)
job.update(decoder_pid=decoder.pid,encoder_pid=encoder.pid);save(OUT/'render-job.json',job)
started=time.monotonic()
try:
    for frame in range(start_frame,end_frame):
        raw=decoder.stdout.read(W*H*3)
        assert len(raw)==W*H*3,('Source decode ended early',frame,len(raw))
        output=animator.step(frame,raw)
        if frame%30==0 and not 134.033<=frame/FPS<148.0334:
            # The spoken captions are presentation-critical and must keep the exact original pixels before encoding.
            assert output[W*932*3:]==raw[W*932*3:],'Caption band changed unexpectedly'
        encoder.stdin.write(output)
        if (frame-start_frame)%150==0:
            job.update(done=frame-start_frame,elapsed_s=time.monotonic()-started)
            save(OUT/'render-job.json',job);print(name,'frames',job['done'],'/',count,flush=True)
    encoder.stdin.close();decoder.stdout.close()
    assert encoder.wait()==0,'Inspect encoder log'
    assert decoder.wait()==0,'Inspect decoder log'
    temporary.replace(destination)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(destination)],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert int(video['nb_frames'])==count and abs(float(video['duration'])-count/FPS)<.001
    job.update(status='complete',done=count,sha256=sha(destination),bytes=destination.stat().st_size,completed_utc=now())
    save(OUT/'render-job.json',job)
    if args.preview:
        save(OUT/(name+'.json'),{'status':'complete','file':str(destination),'source_range_s':[start_frame/FPS,end_frame/FPS],
            'sha256':sha(destination),'duration_s':count/FPS,'music':True,'semantic_transitions':True})
        state.update(status='preview_ready',live_jobs=[])
    else:
        save(OUT/'delivery.json',{'status':'encoded_pending_verification','file':str(destination),'bytes':destination.stat().st_size,
            'sha256':sha(destination),'duration_s':tl['duration_s'],'frames':count,'encoding':'1920x1080 / 30fps / H264 CRF14 slow / stereo AAC 48k',
            'music':'Fluidscape — Kevin MacLeod — CC BY 4.0','music_ducked_below_speech':True,'transition_count':17,
            'other_21_voice_and_caption_timings_preserved':True,'closing_copy_refined_for_viewer_purpose':True,
            'source_video_sha256':sha(source),'new_physics_runs':0,'new_Lux3D_tasks':0,'new_TTS_requests':2})
        def stamp(t):
            n=round(t*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d}.{n%1000:03d}'
        vtt=['WEBVTT','']
        for sentence in tl['captions']:vtt.extend([stamp(sentence['start_s'])+' --> '+stamp(sentence['end_s']),sentence['text'],''])
        (OUT/'BeforeStep-Lux3D-Demo-v2.zh.vtt').write_text('\n'.join(vtt))
        state.update(status='encoded_pending_verification',live_jobs=[])
    save(OUT/'state.json',state)
    print('ENCODE COMPLETE',destination,job['bytes'],job['sha256'],flush=True)
except BaseException as error:
    job.update(status='failed',error=str(error));save(OUT/'render-job.json',job)
    state.update(status='render_failed_review_required',live_jobs=[],next='Inspect retained decoder/encoder log before retrying')
    save(OUT/'state.json',state)
    raise
finally:
    if decoder.poll() is None:decoder.terminate();decoder.wait()
    if encoder.poll() is None:encoder.terminate();encoder.wait()
    decode_log.close();encode_log.close()
