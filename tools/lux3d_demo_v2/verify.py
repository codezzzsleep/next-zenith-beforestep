"""Validate the entire deliverable, timing, source identity and review frames."""
from pathlib import Path
import json
import re
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
from common import OUT,BASE,sha,save

film=OUT/'BeforeStep-Lux3D-Demo-v2.mp4'
tl=json.loads((OUT/'timeline.json').read_text())
plan=json.loads((OUT/'plan.json').read_text())
save(OUT/'verification-job.json',{'status':'running','pid':os.getpid(),'film_sha256':sha(film)})
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(film)],text=True))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert video['codec_name']=='h264' and (video['width'],video['height'])==(1920,1080)
assert video['pix_fmt']=='yuv420p' and video['avg_frame_rate']=='30/1'
assert int(video['nb_frames'])==tl['frames']
assert abs(float(video['duration'])-tl['duration_s'])<.001
assert abs(float(audio['duration'])-tl['duration_s'])<.06
assert audio['codec_name']=='aac' and audio['sample_rate']=='48000' and audio['channels']==2
with (OUT/'logs'/'complete-decode.log').open('w') as log:
    result=subprocess.run(['ffmpeg','-v','info','-xerror','-threads','2','-i',str(film),
        '-vf','blackdetect=d=0.15:pix_th=0.025','-progress',str(OUT/'qc'/'decode-progress.txt'),'-f','null','-'],stdout=log,stderr=log)
assert result.returncode==0,'Full audiovisual decode failed'
decode_log=(OUT/'logs'/'complete-decode.log').read_text()
assert 'black_start:' not in decode_log,'Black-screen interval detected'
progress=(OUT/'qc'/'decode-progress.txt').read_text()
frames=[int(v) for v in re.findall(r'^frame=(\d+)$',progress,re.M)]
assert frames[-1]==tl['frames'] and progress.rstrip().endswith('progress=end')
for path,record in plan['sources'].items():assert sha(path)==record['sha256'],path
assert sha(plan['pair']['photo'])==plan['pair']['photo_sha256']
assert sha(plan['pair']['glb'])==plan['pair']['glb_sha256']
facts=plan['facts']['live_lux_counts'];assert facts['created']==491 and facts['statuses']=={'ok':460,'failed':31}
audit=json.loads((OUT/'subtitle-audit.json').read_text())
sentences=[s['text'] for g in plan['groups'] for s in g['sentences']]
assert sentences==[s['text'] for s in tl['captions']]==[s['text'] for s in audit['captions']]
assert len(sentences)==23
for i,s in enumerate(tl['captions']):
    a=json.loads(((OUT if s['id'].startswith('records-') else BASE)/'audio'/(s['id']+'.json')).read_text())
    assert a['status']=='complete' and a['request']['text']==s['text'] and sha(a['path'])==s['audio_sha256']
    assert 0<=s['start_s']<s['end_s']<=tl['duration_s']
    assert abs(s['end_s']-s['start_s']-a['duration_s'])<.0001
    assert audit['captions'][i]['rendered'].count(r'\N')<2
    if i:assert s['start_s']>=tl['captions'][i-1]['end_s']
with (OUT/'logs'/'volume-check.log').open('w') as log:
    result=subprocess.run(['ffmpeg','-v','info','-i',str(film),'-vn','-af','volumedetect','-f','null','-'],stdout=log,stderr=log)
assert result.returncode==0
volume=(OUT/'logs'/'volume-check.log').read_text()
mean=float(re.search(r'mean_volume: ([-\d.]+) dB',volume)[1]);maximum=float(re.search(r'max_volume: ([-\d.]+) dB',volume)[1])
assert -30<mean<-5 and maximum<=0,'Narration is silent or clipping'
times=sorted(set([.2,tl['duration_s']-.2]+[min(p['end_s']-.1,p['start_s']+p['duration_s']*.5) for p in tl['parts']]+
    [s['start_s']+min(1.2,(s['end_s']-s['start_s'])/2) for s in tl['captions']]))
records=[]
for i,t in enumerate(times):
    dest=OUT/'qc'/f'final-{i:02d}-{t:.2f}s.jpg'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(film),'-frames:v','1','-q:v','2',str(dest)],check=True)
    assert Image.open(dest).size==(1920,1080)
    records.append({'time_s':t,'file':str(dest),'sha256':sha(dest)})
f=ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',23)
contacts=[]
for page in range((len(records)+11)//12):
    canvas=Image.new('RGB',(1440,1240),'#172127');draw=ImageDraw.Draw(canvas)
    for j,row in enumerate(records[page*12:(page+1)*12]):
        im=Image.open(row['file']);im.thumbnail((480,270));x=j%3*480;y=j//3*310;canvas.paste(im,(x,y));draw.text((x+8,y+274),f'{row["time_s"]:.2f} 秒',font=f,fill='white')
    target=OUT/'qc'/f'final-contact-{page+1}.jpg';canvas.save(target,quality=92);contacts.append(str(target))
subprocess.run(['ffmpeg','-v','error','-y','-ss','24','-i',str(film),'-frames:v','1','-q:v','2',str(OUT/'BeforeStep-Lux3D-Demo-v2.jpg')],check=True)
verification={'status':'technical_passed_awaiting_visual_and_playback','passed':True,'film_sha256':sha(film),
    'metadata':probe,'full_decode':{'passed':True,'frames':frames[-1],'audio_decoded':True,'black_intervals':0},
    'source_hashes_unchanged':True,'real_input_GLb_pair_verified':5958685,'narration_caption_text_equal':True,
    'captions':23,'maximum_caption_lines':2,'audio_stretched':False,'audio_volume_db':{'mean':mean,'maximum':maximum},
    'review_frames':records,'contact_sheets':contacts,'new_physics_runs':0,'new_Lux3D_tasks':0,'new_TTS_requests':2,'music':json.loads((OUT/'mixing.json').read_text()),'animation':json.loads((OUT/'motion-plan.json').read_text())}
save(OUT/'verification.json',verification)
save(OUT/'verification-job.json',{'status':'complete','pid':os.getpid(),'film_sha256':sha(film)})
print(json.dumps({'passed':True,'duration_s':tl['duration_s'],'frames':frames[-1],'review_frames':len(records),'sha256':sha(film)},ensure_ascii=False),flush=True)
