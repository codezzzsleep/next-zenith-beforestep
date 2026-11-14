"""Verify the completed film and make a portable, explicitly selected ZIP."""
import argparse
import datetime
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import zipfile
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_state, resolve, OUT, ROOT, sha, save, status

WORK=OUT/'film'
QC=WORK/'qc';QC.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['verify','package'],default='verify');parser.add_argument('--reuse-protected-samples',action='store_true');args=parser.parse_args()
video=OUT/'demo-v6.mp4'
plan=json.loads((WORK/'plan.json').read_text())
timeline=json.loads((WORK/'timeline.json').read_text())

if args.phase=='verify':
    job={'id':'v6-film-final-verification','pid':os.getpid(),'status':'running','current':None,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(WORK/'verification-job.json',job)
    state=load_state(WORK / 'state.json');state.update(status='final_film_verification',live_jobs=[{'id':job['id'],'pid':os.getpid(),'ledger':str(WORK/'verification-job.json')}]);save(WORK/'state.json',state)
    digest=sha(video)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],text=True))
    v=[r for r in probe['streams'] if r['codec_type']=='video'];a=[r for r in probe['streams'] if r['codec_type']=='audio']
    assert len(v)==len(a)==1
    assert (v[0]['codec_name'],v[0]['width'],v[0]['height'],v[0]['pix_fmt'],v[0]['avg_frame_rate'])==('h264',1920,1080,'yuv420p','30/1')
    assert int(v[0]['nb_frames'])==timeline['frames']
    assert abs(float(probe['format']['duration'])-timeline['duration_s'])<.1
    assert a[0]['codec_name']=='aac' and int(a[0]['sample_rate'])==48000
    assert 170<=float(probe['format']['duration'])<=190
    assert sha(WORK/'plan.json')==timeline['plan_sha256']
    for name,source in plan['selected_shots'].items(): assert sha(OUT/'shots'/(name+'.mp4'))==source['sha256']
    subtitles=json.loads((WORK/'subtitle-audit.json').read_text())
    assert subtitles['narration_text_equal'] and subtitles['maximum_lines']==2
    assert len(subtitles['captions'])==len(timeline['captions'])==27
    for s,c in zip(timeline['captions'],subtitles['captions']):
        assert s['text']==c['text'] and c['rendered'].replace(r'\N','')==s['text']
        assert c['rendered'].count(r'\N')<=1
        assert 0<=s['start_s']<s['end_s']<=timeline['duration_s']
        assert sha(s['audio'])==s['audio_sha256']
    assert all(a['end_s']<=b['start_s'] for a,b in zip(timeline['captions'],timeline['captions'][1:]))
    assert not any('%' in s['text'] or '证明想象必要' in s['text'] for s in timeline['captions'])
    decode=WORK/'logs/full-decode.log';progress=WORK/'logs/full-decode-progress.txt'
    command=['ffmpeg','-hide_banner','-v','info','-threads','2','-i',str(video),'-vf','blackdetect=d=0.2:pix_th=0.015:pic_th=0.985',
             '-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-progress',str(progress),'-nostats','-f','null','-']
    with decode.open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=log);job['current']={'pid':process.pid,'stage':'full_video_and_audio_decode','log':str(decode)};save(WORK/'verification-job.json',job);assert process.wait()==0
    decoded=progress.read_text();assert 'progress=end' in decoded
    frame_counts=re.findall(r'^frame=(\d+)$',decoded,re.M);assert int(frame_counts[-1])==timeline['frames']
    black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',decode.read_text())
    assert not black, black
    samples=[]
    correction=json.loads((WORK/'title-correction-job.json').read_text()) if args.reuse_protected_samples else None
    prior=json.loads((WORK/'verification.json').read_text()) if args.reuse_protected_samples else None
    if correction:
        assert correction['status']=='complete' and correction['outside_GOP_decoded_frames_identical']
        assert correction['final_sha256']==digest and correction['original_sha256']==prior['sha256']
    for part in timeline['parts']:
        for ratio in ([.15,.5,.9] if part['id'] in ['comparison','failure','lift','connect','close','stopA','stopB','ending'] else [.5]):
            t=part['start_s']+part['duration_s']*ratio
            dest=QC/(part['id']+'-'+str(round(ratio*100))+'.jpg')
            reuse=bool(correction and dest.exists() and not correction['reencoded_GOP_interval_s'][0]<=t<correction['reencoded_GOP_interval_s'][1])
            if not reuse:subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(dest)],check=True)
            samples.append({'part':part['id'],'time_s':t,'path':str(dest),'sample_sha256':sha(dest),'reused_after_identical_decoded_frame_proof':reuse})
    connect=next(p for p in timeline['parts'] if p['id']=='connect')
    transition=QC/'connect-transition.jpg'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(connect['start_s']+6.3),'-i',str(video),'-frames:v','1','-q:v','2',str(transition)],check=True)
    for group_no,start in enumerate(range(0,len(samples),9)):
        canvas=Image.new('RGB',(1920,1152),'#080b0d');draw=ImageDraw.Draw(canvas)
        for i,row in enumerate(samples[start:start+9]):
            img=Image.open(row['path']);img=img.resize((640,360),Image.Resampling.LANCZOS)
            x,y=i%3*640,i//3*384;canvas.paste(img,(x,y));draw.text((x+12,y+361),f'{row["part"]}  {row["time_s"]:.2f}s',fill='white')
        canvas.save(QC/f'contact-{group_no+1}.jpg',quality=92)
    report={'status':'technical_verification_passed_visual_review_pending','passed':True,'path':str(video),'sha256':digest,'bytes':video.stat().st_size,
            'probe':probe,'duration_s':timeline['duration_s'],'decoded_frames':int(frame_counts[-1]),'full_audio_and_video_decode':True,'black_intervals':black,
            'subtitle_maximum_lines':2,'narration_caption_text_equal':True,'narration_sentences':27,'original_source_shots_SHA_unchanged':True,
            'source_shots_count':len(plan['selected_shots']),'samples':samples,'transition_sample':str(transition),'music':False,
            'new_physics_runs':0,'new_Lux3D_tasks':0,'gpu_shutdown':False,'full_decode_log':str(decode),
            'verification_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(WORK/'verification.json',report)
    status('成片完整解码与字幕核验',WORK/'verification.json',f'通过：{timeline["frames"]}帧/{timeline["duration_s"]:.3f}s，H2641080p30+AAC配音；全片解码、无黑屏、27句同稿且每屏最多两行；待抽帧目测/实际播放')
    job.update(status='complete',current=None);save(WORK/'verification-job.json',job)
    state.update(status='technical_verification_passed_visual_review_pending',live_jobs=[],next='View final-film contact sheets and transition; test browser playback; package after review');save(WORK/'state.json',state)
    print(json.dumps({'technical_verification_passed':True,'duration_s':timeline['duration_s'],'frames':timeline['frames'],'bytes':video.stat().st_size,'sample_count':len(samples)},ensure_ascii=False))
else:
    verification=json.loads((WORK/'verification.json').read_text());review=json.loads((WORK/'visual-review.json').read_text());playback=json.loads((WORK/'playback.json').read_text())
    assert verification['passed'] and review['passed'] and playback['passed']
    assert sha(video)==verification['sha256']
    assert playback['video_sha256']==review['video_sha256']==verification['sha256']
    verification.update(status='complete_verified',visual_review=str(WORK/'visual-review.json'),playback=str(WORK/'playback.json'))
    save(WORK/'verification.json',verification)
    ending=next(p for p in timeline['parts'] if p['id']=='ending')
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(ending['start_s']+1),'-i',str(video),'-frames:v','1','-q:v','2',str(OUT/'demo-v6.jpg')],check=True)
    cut=['# BeforeStep 最终成片镜头表','',f'时长 {timeline["duration_s"]:.3f} 秒，MiniMax 中文配音，与烧录字幕同稿。','',
         '| 起点 | 终点 | 镜头 | 原素材 |','| ---: | ---: | --- | --- |']
    for part in timeline['parts']: cut.append(f'| {part["start_s"]:.3f}s | {part["end_s"]:.3f}s | {part["id"]} | {part.get("shot","s03-* 三车共同仿真时钟")} |')
    cut += ['', '所有运动画面均来自原保存状态的回放，网页片段来自已有真实浏览器录屏。',
            '连接预检查使用真实形状，不能当作正式 D 或 Lux3D 到达成绩；F3_002 的 A/D 第一段停车，未使用腿。',
            '网页素材 r04 复用旧录屏；r01 为原公开叠合页面的事后诊断；来源限制保留在原 shots 元数据中。',
            '原运行、原生成模型、碰撞与停车证据保留。没有新物理、Lux3D 生成或网站发布。']
    (WORK/'CUT_LIST.md').write_text('\n'.join(cut)+'\n')
    readme='''# BeforeStep 视频交付

`demo-v6.mp4` 是完整成片：3 分 05 秒、1920×1080、30 fps、H.264 CRF14 slow、AAC 中文配音，无配乐。字幕已烧入视频，`demo-v6.zh.vtt` 另供播放器使用。

配音来自 MiniMax，与 `narration.md`、VTT 和烧录字幕同稿。镜头、数字和来源见 CUT_LIST.md、timeline.json、facts.json 及 verification.json。

第五幕的连接预检查与正式车分别标明：真实形状预检查先绕后跨；正式 F3_002 A/D 在高石段停车，正式门槛段未发生。

全部视觉素材取自已交付 shots；原版与 v2 素材保留。无新物理/Lux3D任务、无配乐、无锐化、无网站发布。GPU 未执行关机。

MANIFEST.json 记录每个包内成员的 SHA256。该包不含任何凭据。
'''
    (WORK/'README.md').write_text(readme)
    members={
        'demo-v6.mp4':video,'demo-v6.zh.vtt':OUT/'demo-v6.zh.vtt','demo-v6.jpg':OUT/'demo-v6.jpg',
        'README.md':WORK/'README.md','CUT_LIST.md':WORK/'CUT_LIST.md','narration.md':WORK/'narration.md',
        'timeline.json':WORK/'timeline.json','facts.json':WORK/'facts.json','verification.json':WORK/'verification.json',
        'visual-review.json':WORK/'visual-review.json','playback.json':WORK/'playback.json'}
    manifest={name:{'sha256':sha(path),'bytes':path.stat().st_size} for name,path in members.items()}
    dest=OUT/'BeforeStep-demo-v6.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,path in members.items(): z.write(path,name)
        z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,row in manifest.items(): assert hashlib.sha256(z.read(name)).hexdigest()==row['sha256']
    packet={'status':'complete','passed':True,'path':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'members':manifest,'credentials_included':False,'CRC_and_member_SHA_passed':True}
    save(WORK/'package.json',packet)
    (dest.with_suffix('.zip.sha256')).write_text(packet['sha256']+'  '+dest.name+'\n')
    delivery=json.loads((WORK/'delivery.json').read_text());delivery.update(status='complete_verified',verification=str(WORK/'verification.json'),visual_review=str(WORK/'visual-review.json'),playback=str(WORK/'playback.json'),package=str(dest));save(WORK/'delivery.json',delivery)
    state=load_state(WORK / 'state.json');state.update(status='full_film_complete_verified_packaged',live_jobs=[],next='用户下载和播放成片；大文件ZIP可代传。未执行GPU关机，未发布任何网站。',film=str(video),package=str(dest),completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save(WORK/'state.json',state)
    status('完整视频与压缩包交付',dest,f'通过：185秒中文配音成片完整解码/实际播放/抽帧核验；ZIP CRC与逐成员SHA通过，{packet["bytes"]}字节；无凭据，供用户代传；未执行GPU关机')
    print(json.dumps({'video':str(video),'package':str(dest),'package_bytes':packet['bytes'],'sha256':packet['sha256'],'complete':True},ensure_ascii=False))
