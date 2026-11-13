"""Evidence-checked 1080p30 H.264 storyboard composition, with burned captions."""
import argparse,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write,sha
OUT=ROOT/'outputs/crossing/route/video';PAGES=OUT/'pages'
FRAMES=ROOT/'outputs/crossing/route/handoff/frames'
FONT='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
DURATIONS=[8,10,14,14,22,30,30,16,10]

def read(path):return json.loads((ROOT/path).read_text())
def ffprobe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,codec_name,width,height,r_frame_rate','-of','json',str(path)],text=True))

def narrations():
    home=read('site/home-assets/data/site.json');exhibit=read('site/home-assets/data/exhibit.json')
    gate=read('evidence/crossing/calibration/gate.json');summary=read('evidence/crossing/route/summary.json')
    claims={};errors={}
    def check(shot,name,value,expected):
        claims[name]={'shot':shot,'actual':value,'expected':expected,'matches':value==expected}
        if value!=expected:errors.setdefault(shot,[]).append(claims[name])
    wall=exhibit['wall'];check(3,'rejected_models_that_collide',sum(r[1]=='c' for r in wall['tiles']),wall['stats']['rejected_would_crash'])
    check(3,'storyboard_30',wall['stats']['rejected_would_crash'],30)
    error=abs(exhibit['overlays']['anchor'][0]['back_error_grid_m'])
    check(4,'anchor_back_short_m',round(error,2),.70)
    check(5,'all_twelve_rehearsals',len(home['rehearsals']),12)
    check(5,'all_rehearsals_complete_and_safe',all(r['completed'] and not r['collided'] for r in home['rehearsals']),True)
    check(5,'anchor_arrival',home['runs']['imagination']['result'],'arrived')
    check(5,'anchor_looks',home['runs']['imagination']['looks'],1)
    check(5,'anchor_time_s',round(home['runs']['imagination']['sim_time_s'],2),112.84)
    check(6,'wheel_trials',gate['wheel_trials_at_band_heights'],90);check(6,'wheel_passes',gate['wheel_passes_at_band_heights'],0)
    check(6,'leg_trials',gate['band_gait_trials'],24);check(6,'leg_clean_passes',gate['band_gait_clean_trials'],24)
    rows=[r for r in home['known'] if r['classification']=='decisive']+home['holdouts']
    collisions=sum(r['runs']['imagination']['result']=='collision' for r in rows)
    check(8,'original_method_collisions',collisions,4)
    check(8,'strict_method_collisions',sum(r['runs']['imagination_strict']['result']=='collision' for r in rows),0)
    by={r['vehicle']:r for r in summary['rows']};d=by.get('D');branch='7a' if d and d['total_result']=='arrived' else '7b'
    if branch=='7a':
        pieces=['把两种石头放在同一条路上。']
        for v,label in [('B','只信看见的车'),('C','把没看见的都当危险的车'),('A','有想象但没有腿的车'),('D','既有想象又有腿的车')]:
            row=by[v]
            if row['total_result']=='arrived':pieces.append(label+'到了终点。')
            elif row['first_segment_result']!='arrived':pieces.append(label+'没有走完高石头这一段。')
            else:pieces.append(label+'没有跨过门槛。')
        seven=''.join(pieces)
    else:
        seven='把两种石头放在同一条路上。用真实形状检查时，这条路走得通：先绕，再跨。'
        if summary['all_terminal']:
            accidents=[r for r in summary['rows'] if r['total_result']=='collision']
            if all(r['total_result'] in ('stopped','stuck') for r in summary['rows']):
                seven+='换成 Lux3D 的想象，四辆车都没有到达，'+('没有一辆出事。' if not accidents else '实际接触按结果表保留。')
            else:seven+='四车的实际结果逐项保留在表里。'
            seven+='我们把这个结果照实放在这里。'
        else:seven+='四车试验还在进行，结果表展示当前已经终态的运行。'
    text={
        1:'月球南极，太阳贴着地平线。机器人看到一块石头，只看到朝着它的那一面。',
        2:'我们把这一张照片交给 Lux3D。它交回一整块石头，包括相机从没见过的背面。',
        3:f'但想出来的东西不能直接信。几百份生成结果里，我们逐份和看见的部分核对。被拒掉的里面，有 {wall["stats"]["rejected_would_crash"]} 份如果信了，车会撞上。',
        4:f'通过核对的也不一定对。这一份，正面完全吻合，背面比真实的石头短了 {error:.2f} 米。所以每一份想象只是一个假设。',
        5:f'机器人的做法是：生成多份，逐份核对，在每一份想象里先走一遍。全部安全，才真的走。这个场景它只看了{home["runs"]["imagination"]["looks"]}眼，{home["runs"]["imagination"]["sim_time_s"]:.2f} 秒到达。',
        6:f'路上还有另一种石头：十几厘米高，横在窄口里。轮子滚不上去，{gate["wheel_trials_at_band_heights"]} 次试了 {gate["wheel_passes_at_band_heights"]} 次通过。这台车的轮子装在腿上，一次抬一个轮子，{gate["band_gait_clean_trials"]} 次全部跨过。这种石头相机看得全，不需要想象。',
        7:seven,
        8:f'这套方法有效，但不绝对。它到达过，也撞过{collisions}次，每一次都摆在页面上，可以转着看。规则收紧之后不再碰撞，也更常停下。',
        9:'先见一步，BeforeStep。生成的三维，先检验，先预演，机器人才迈步。'}
    provenance=[{'path':p,'sha256':sha(ROOT/p)} for p in ['docs/video.md','site/home-assets/data/site.json','site/home-assets/data/exhibit.json','evidence/crossing/calibration/gate.json','evidence/crossing/route/summary.json']]
    write(OUT/'numeric-audit.json',{'claims':claims,'shot_errors':errors,'branch':branch,'sources':provenance,'all_numbers_read_from_evidence':True})
    return text,branch,errors

def run(args,shot):
    logs=OUT/'logs';logs.mkdir(parents=True,exist_ok=True)
    write(OUT/'live-job.json',{'pid':os.getpid(),'shot':shot,'command':args,'at_unix':time.time()})
    with (logs/f'{shot}.log').open('a') as stream:subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,check=True)

def draw(label,shot):
    if not label:return ''
    path=OUT/f'label-{shot}.txt';path.write_text(label)
    return f',drawtext=fontfile={FONT}:textfile={path}:fontcolor=white:fontsize=30:x=36:y=35:box=1:boxcolor=black@0.72:boxborderw=12'

def encode(args,filters,path,duration,label='',shot='clip'):
    base=['ffmpeg','-hide_banner','-y','-filter_threads','1',*args,'-vf',filters+draw(label,shot),'-t',str(duration),'-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    run(base,shot)

FIT='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x080909,setsar=1'

def page_clip(shot,path,duration=None):
    index=PAGES/f'{shot}.json';data=json.loads(index.read_text());duration=duration or data['duration_s']
    if data['status']=='complete':
        encode(['-ss',str(data['stable_start_s']),'-i',str(ROOT/data['path'])],FIT+',fps=30',path,duration,shot=shot)
    else:
        still=PAGES/f'{shot}-still.jpg'
        if not still.exists():raise RuntimeError(f'No usable corresponding page for shot {shot}')
        encode(['-loop','1','-framerate','30','-i',str(still)],FIT,path,duration,'对应公网页面静帧',shot)

def frame_clip(clip,camera,path,duration,label,start_number=0,source_duration=None):
    index=FRAMES/clip/'index.json';data=json.loads(index.read_text())
    if data['status']!='complete':raise RuntimeError(clip+' frame set still running; leave this shot pending')
    count=sum(r['camera']==camera for r in data['frames'])
    available=(count-start_number)/30;source_duration=source_duration or available
    factor=duration/source_duration
    filters=f'setpts=(PTS-STARTPTS)*{factor:.10f},fps=30,{FIT}'
    args=['-framerate','30','-start_number',str(start_number),'-i',str(FRAMES/clip/camera/'%05d.jpg')]
    encode(args,filters,path,duration,label,clip+'-'+camera)
    return data

def concat(files,path,shot):
    listing=OUT/f'concat-{shot}.txt';listing.write_text(''.join("file '"+str(p)+"'\n" for p in files))
    run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(path)],shot)

def make_shot(shot,branch):
    path=OUT/'shots'/f'{shot}.mp4';path.parent.mkdir(parents=True,exist_ok=True)
    duration=DURATIONS[shot-1]
    if shot==1:
        source=ROOT/'site/media/award/first.png'
        encode(['-loop','1','-framerate','30','-i',str(source)],FIT+",zoompan=z='1+0.0003*on':d=1:s=1920x1080:fps=30",path,duration,'机器人第一眼：原始相机图像','1')
    elif shot in [2,3,4,8,9]:page_clip(str(shot),path,duration)
    elif shot==5:
        parts=[OUT/'shots/5-worlds.mp4',OUT/'shots/5-drive.mp4',OUT/'shots/5-overview.mp4']
        page_clip('5',parts[0],12)
        for source,out in zip(['imagination.mp4','overview.mp4'],parts[1:]):
            p=ROOT/'site/media/video-scene'/source;length=float(ffprobe(p)['format']['duration'])
            encode(['-i',str(p)],f'setpts=(PTS-STARTPTS)*{5/length:.10f},fps=30,'+FIT,out,5,'R1 原运行：真实物理轨迹回放（加速）','5-'+source)
        concat(parts,path,'5')
    elif shot==6:
        left=OUT/'shots/6-wheel.mp4';right=OUT/'shots/6-leg.mp4';split=OUT/'shots/6-split.mp4';close=OUT/'shots/6-close.mp4'
        wheel=read(str((FRAMES/'wheel-stuck/index.json').relative_to(ROOT)));leg=read(str((FRAMES/'leg-cross/index.json').relative_to(ROOT)))
        if wheel['threshold_sha256']!=leg['threshold_sha256'] or wheel['scene_sha256']!=leg['scene_sha256']:raise RuntimeError('Shot 6 sources are not the same scene and sill')
        if wheel['status']!='complete':raise RuntimeError('wheel-stuck still rendering')
        encode(['-framerate','30','-i',str(FRAMES/'wheel-stuck/side_follow/%05d.jpg')],FIT+',tpad=stop_mode=clone:stop_duration=7',left,22,'常规轮行：真实几何预检查（末态定格）','6-wheel')
        length=sum(f['camera']=='side_follow' for f in leg['frames'])/30
        speed=length/22
        frame_clip('leg-cross','side_follow',right,22,f'逐轮跨越：同场同石预检查（{speed:.1f}×）')
        filtergraph='[0:v]scale=960:540,pad=960:1080:0:250:color=0x080909[l];[1:v]scale=960:540,pad=960:1080:0:250:color=0x080909[r];[l][r]hstack=inputs=2[v]'
        run(['ffmpeg','-hide_banner','-y','-filter_complex_threads','1','-i',str(left),'-i',str(right),'-filter_complex',filtergraph,'-map','[v]','-t','22','-an','-c:v','libx264','-preset','veryfast','-crf','21','-threads','1','-pix_fmt','yuv420p',str(split)],'6-split')
        # A complete front-right lift/swing/landing in the recorded close camera.
        import numpy as np
        with np.load(ROOT/leg['source_runs'][0]['path']) as trajectory:
            phase=trajectory['phase'].astype(str);stamps=trajectory['t']
            lift=float(stamps[np.flatnonzero(phase=='front-right-lift')[0]])
            seat=float(stamps[np.flatnonzero(phase=='front-right-seat')[0]])
        begin=leg['time_range_s'][0];start=int(round((lift-begin)*30));span=seat-lift
        frame_clip('sill-close','side_follow',close,8,f'门槛特写：真实几何预检查（{span/8:.1f}×）',start,span)
        concat([split,close],path,'6')
    elif shot==7:
        physical=OUT/'shots/7-run.mp4';table=OUT/'shots/7-table.mp4'
        if branch=='7a':
            frame_clip('D-actual','overhead',physical,22,'D 正式一次运行：保存的物理轨迹回放（加速）')
        else:
            data=read(str((FRAMES/'connect/index.json').relative_to(ROOT)));speed=(data['time_range_s'][1]-data['time_range_s'][0])/22
            frame_clip('connect','overhead',physical,22,f'接通预检查：真实形状，保存末态连续接续（{speed:.1f}×）')
        page_clip('7-table',table,8);concat([physical,table],path,'7')
    return path

def ass_time(seconds):
    centiseconds=int(round(seconds*100));return f'{centiseconds//360000}:{centiseconds//6000%60:02d}:{centiseconds//100%60:02d}.{centiseconds%100:02d}'

def subtitles(text):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,WenQuanYi Zen Hei,42,&H00FFFFFF,&H00FFFFFF,&H88000000,&H88000000,0,0,0,0,100,100,0,0,3,10,0,2,120,120,58,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events=[];offset=0
    for shot,duration in enumerate(DURATIONS,1):
        sentences=[s for s in re.findall(r'.+?[。！？]|.+$',text[shot]) if s.strip()]
        total=sum(len(s) for s in sentences);cursor=offset
        for sentence in sentences:
            length=duration*len(sentence)/total
            # At most two lines, with no subtitle card exceeding 64 characters.
            chunks=[sentence[i:i+60] for i in range(0,len(sentence),60)]
            for chunk in chunks:
                end=cursor+length/len(chunks);line=chunk if len(chunk)<=30 else chunk[:len(chunk)//2]+'\\N'+chunk[len(chunk)//2:]
                events.append(f'Dialogue: 0,{ass_time(cursor)},{ass_time(end)},Default,,0,0,0,,{line}')
                cursor=end
        offset+=duration
    path=OUT/'subtitles.ass';path.write_text(header+'\n'.join(events)+'\n');return path

def render():
    OUT.mkdir(parents=True,exist_ok=True);text,branch,errors=narrations();done=[];pending=[]
    for shot in range(1,10):
        if shot in errors:pending.append({'shot':shot,'numeric_difference':errors[shot]});continue
        try:
            inputs={'text':text[shot],'branch':branch if shot==7 else None,'duration':DURATIONS[shot-1]}
            for name in ([str(shot)] if shot in [2,3,4,5,8,9] else ['7-table'] if shot==7 else []):
                p=PAGES/f'{name}.json';inputs[name]=sha(p) if p.exists() else None
            if shot in [6,7]:
                for name in ['wheel-stuck','leg-cross','sill-close'] if shot==6 else ['D-actual' if branch=='7a' else 'connect']:
                    p=FRAMES/name/'index.json';inputs[name]=sha(p) if p.exists() else None
            signature=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest();meta=OUT/'shots'/f'{shot}.json';path=OUT/'shots'/f'{shot}.mp4'
            old=json.loads(meta.read_text()) if meta.exists() else {}
            if old.get('signature')!=signature or not path.exists():
                path=make_shot(shot,branch);write(meta,{'shot':shot,'signature':signature,'inputs':inputs,'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
            done.append(path)
        except Exception as error:pending.append({'shot':shot,'reason':str(error)});print(json.dumps(pending[-1],ensure_ascii=False),flush=True)
    write(OUT/'render-state.json',{'pid':os.getpid(),'completed_shots':[int(p.stem) for p in done],'pending':pending,'branch':branch})
    if pending:return
    joined=OUT/'all-shots.mp4';concat(done,joined,'all')
    caption=subtitles(text);destination=ROOT/'site/media/demo-v2.mp4';temporary=destination.with_name('demo-v2-rendering.mp4')
    encode(['-i',str(joined)],f'ass={caption}',temporary,sum(DURATIONS),shot='burn-captions')
    metadata=ffprobe(temporary);video=[s for s in metadata['streams'] if s['codec_type']=='video'];assert len(video)==1
    assert (video[0]['codec_name'],video[0]['width'],video[0]['height'],video[0]['r_frame_rate'])==('h264',1920,1080,'30/1')
    assert not any(s['codec_type']=='audio' for s in metadata['streams']);assert abs(float(metadata['format']['duration'])-sum(DURATIONS))<.1
    temporary.replace(destination);cover=ROOT/'site/media/demo-v2-cover.jpg'
    run(['ffmpeg','-hide_banner','-y','-ss','10','-i',str(destination),'-frames:v','1','-q:v','2',str(cover)],'cover')
    report={'schema':'beforestep-demo-video-v2/v1','path':'site/media/demo-v2.mp4','sha256':sha(destination),'bytes':destination.stat().st_size,
        'duration_s':float(metadata['format']['duration']),'video':video[0],'audio':False,'subtitles_burned':True,'agent_composed':True,
        'responsible_reviewer_status':'待负责人看片','branch':branch,'numeric_audit':str((OUT/'numeric-audit.json').relative_to(ROOT)),
        'source_clips':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in done],
        'precheck_not_formal':True,'cover':str(cover.relative_to(ROOT))}
    write(ROOT/'evidence/crossing/route/video-v2.json',report);write(OUT/'render-state.json',{'status':'complete','video':report})
    print(json.dumps({k:report[k] for k in ['path','duration_s','bytes','branch','responsible_reviewer_status']},ensure_ascii=False),flush=True)

if __name__=='__main__':render()
