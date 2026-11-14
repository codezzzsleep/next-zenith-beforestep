"""Compose only retained shots; audio and captions share one measured script."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_state, resolve, OUT, save, sha, status

WORK = OUT / 'film'
PARTS = WORK / 'parts'
LOGS = WORK / 'logs'
PARTS.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)
plan = json.loads((WORK / 'plan.json').read_text())
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
W, H, FPS = 1920, 1080, 30
parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['plan', 'parts', 'finish', 'all'], default='all')
args = parser.parse_args()
job = {'id': 'beforestep-v6-film-compose', 'pid': os.getpid(), 'status': 'running', 'phase': args.phase,
       'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'completed': [], 'current': None,
       'new_physics_runs': 0, 'new_Lux3D_tasks': 0, 'gpu_shutdown': False}
save(WORK / 'composition-job.json', job)
state = load_state(WORK / 'state.json')
state.update(status='composing_full_film', live_jobs=[{'id': job['id'], 'pid': os.getpid(), 'ledger': str(WORK / 'composition-job.json')}])
save(WORK / 'state.json', state)

def run(command, name):
    with (LOGS / (name + '.log')).open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=log)
        job['current'] = {'stage': name, 'pid': process.pid, 'command': command}
        save(WORK / 'composition-job.json', job)
        rc = process.wait()
    if rc: raise RuntimeError(name + ' failed; inspect ' + str(LOGS / (name + '.log')))
    job['current'] = None
    save(WORK / 'composition-job.json', job)

def quant(seconds): return math.ceil(seconds * FPS - 1e-8) / FPS
def stamp(seconds):
    c = round(seconds * 100)
    return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
def vtt_stamp(seconds):
    m = round(seconds * 1000)
    return f'{m//3600000:02d}:{m//60000%60:02d}:{m//1000%60:02d}.{m%1000:03d}'

def make_timeline():
    groups, parts, captions = [], [], []
    cursor = 0.
    for group in plan['groups']:
        sentences = []
        for sentence in group['sentences']:
            d = json.loads((WORK / 'audio' / (sentence['id'] + '.json')).read_text())
            assert d['status'] == 'complete' and d['request']['text'] == sentence['text']
            assert sha(d['path']) == d['sha256']
            sentences.append({**sentence, 'audio': str(resolve(d['path'])), 'audio_sha256': d['sha256'], 'audio_duration_s': d['duration_s']})
        spoken = sum(s['audio_duration_s'] for s in sentences)
        length = quant(max(group['base_duration_s'], spoken + .35 * (len(sentences) + 1)))
        extra = length - spoken
        gap = min(1.5, extra / (len(sentences) + 1))
        offset = min(.65, gap)
        if group['id'] in ['stopA', 'stopB']:
            offset = max(.2, length - spoken - .2)
        for sentence in sentences:
            sentence.update(start_s=cursor + offset, end_s=cursor + offset + sentence['audio_duration_s'], group=group['id'])
            captions.append(sentence)
            offset += sentence['audio_duration_s'] + gap
        new_group = {**group, 'start_s': cursor, 'end_s': cursor + length, 'duration_s': length, 'sentences': sentences}
        groups.append(new_group)
        pcursor = cursor
        for i, part in enumerate(group['parts']):
            plen = quant(part['base_duration_s'] * length / group['base_duration_s'])
            if i == len(group['parts']) - 1: plen = quant(cursor + length - pcursor)
            parts.append({**part, 'group': group['id'], 'chapter': group['chapter'], 'start_s': pcursor,
                          'duration_s': plen, 'end_s': pcursor + plen})
            pcursor += plen
        assert abs(pcursor - cursor - length) < .001
        cursor += length
    assert 170 <= cursor <= 190, ('Measured narration exceeds final-film duration bounds', cursor)
    comparison = next(g for g in groups if g['id'] == 'comparison')
    cstart, duration = comparison['start_s'], comparison['duration_s']
    imag_at = comparison['sentences'][2]['start_s'] - cstart
    cons_at = comparison['sentences'][3]['start_s'] - cstart
    knots = [[0, 1.2], [min(5, imag_at / 2), 55], [imag_at, plan['r1']['optimistic']],
             [cons_at, plan['r1']['imagination']], [duration - 1.25, plan['r1']['conservative']], [duration, plan['r1']['conservative']]]
    assert all(knots[i][0] < knots[i+1][0] for i in range(len(knots)-1))
    timeline = {'duration_s': cursor, 'frames': round(cursor*FPS), 'groups': groups, 'parts': parts, 'captions': captions,
                'shared_r1_clock': {'knots': knots, 'focus_switches': [imag_at, cons_at], 'order': ['optimistic', 'imagination', 'conservative'],
                                    'video_frame_selection': 'Closest existing encoded frame to common simulation time; terminated policies hold their final frame'},
                'plan_sha256': sha(WORK / 'plan.json'), 'audio_stretched': False, 'music': False}
    save(WORK / 'timeline.json', timeline)
    return timeline

timeline = make_timeline()

def lossless(dest, frames):
    return ['-frames:v', str(frames), '-an', '-r', '30', '-c:v', 'libx264', '-crf', '0', '-preset', 'veryfast',
            '-threads', '2', '-pix_fmt', 'yuv420p', str(dest)]

class Frames:
    def __init__(self, name):
        self.name = name
        self.process = subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(OUT/'shots'/(name+'.mp4')),
                                         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=(LOGS/(name+'-decode.log')).open('w'))
        self.index = -1
        self.frame = None
    def at(self, index):
        assert index >= self.index
        while self.index < index:
            data = self.process.stdout.read(W * H * 3)
            assert len(data) == W * H * 3, (self.name, self.index)
            self.frame = data
            self.index += 1
        return self.frame
    def close(self):
        self.process.stdout.close()
        if self.process.poll() is None: self.process.terminate()
        self.process.wait()

def comparison(part, dest):
    clock = timeline['shared_r1_clock']
    knots = np.array(clock['knots'])
    names = ['s03-optimistic-v2', 's03-conservative-v2', 's03-imagination-v2']
    readers = [Frames(name) for name in names]
    metadata = [plan['selected_shots'][name] for name in names]
    speed = [6., 12., 6.]
    tracks = [np.clip(np.minimum(np.arange(m['frame_count']) / FPS * s, m['sim_requested_range_s'][1]),
                         m['sim_clipped_range_s'][0], m['sim_clipped_range_s'][1]) for m, s in zip(metadata, speed)]
    frame_rows = []
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1920x1080',
               '-framerate', '30', '-i', 'pipe:0', *lossless(dest, round(part['duration_s'] * FPS))]
    log = (LOGS / 'comparison-encode.log').open('w')
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
    job['current'] = {'stage': 'shared-clock-comparison', 'pid': encoder.pid, 'decoder_pids': [r.process.pid for r in readers], 'command': command}
    save(WORK / 'composition-job.json', job)
    try:
        for frame in range(round(part['duration_s'] * FPS)):
            out_time = frame / FPS
            virtual = float(np.interp(out_time, knots[:,0], knots[:,1]))
            focus = 0 if out_time < clock['focus_switches'][0] else 2 if out_time < clock['focus_switches'][1] else 1
            images, indices, selected_times = [], [], []
            for r, track in zip(readers, tracks):
                target = float(np.clip(virtual, track[0], track[-1]))
                if virtual >= track[-1]: index = len(track)-1
                else:
                    right = min(int(np.searchsorted(track, target)), len(track)-1)
                    left = max(0, right-1)
                    index = left if abs(track[left]-target) <= abs(track[right]-target) else right
                index = max(index, r.index)
                images.append(Image.frombytes('RGB', (W,H), r.at(index)))
                indices.append(index); selected_times.append(float(track[index]))
            canvas = Image.new('RGB', (W,H), '#090e11')
            canvas.paste(images[focus].resize((1440,810), Image.Resampling.LANCZOS), (0,80))
            others = [i for i in range(3) if i != focus]
            for j, i in enumerate(others):
                canvas.paste(images[i].resize((480,270), Image.Resampling.LANCZOS), (1440,180+j*390))
            ImageDraw.Draw(canvas).line([(1438,80),(1438,890)], fill='#88bbb6', width=2)
            encoder.stdin.write(canvas.tobytes())
            frame_rows.append({'frame': frame, 'common_sim_time_s': virtual, 'focus': focus,
                               'source_encoded_frames': indices, 'source_sim_time_s': selected_times})
        encoder.stdin.close()
        assert encoder.wait() == 0
    finally:
        if encoder.poll() is None: encoder.kill(); encoder.wait()
        for r in readers: r.close()
        log.close()
    save(WORK / 'comparison-frame-map.json', {'sources': names, 'source_metadata': metadata, 'clock': clock, 'frames': frame_rows,
                                             'quantization_note': 'Existing 6x/12x encoded shots sample simulation at 0.2/0.4 second intervals; nearest frame chosen, never a new physical state.'})

def build_parts():
    for part in timeline['parts']:
        assert shutil.disk_usage(OUT).free > 2_000_000_000, 'Insufficient working disk space'
        dest = PARTS / (part['id'] + '.mkv')
        ledger = PARTS / (part['id'] + '.json')
        ident = hashlib.sha256(json.dumps(part, sort_keys=True).encode()).hexdigest()
        if dest.exists() and ledger.exists():
            old = json.loads(ledger.read_text())
            if old['identity'] == ident and old['sha256'] == sha(dest):
                job['completed'].append(part['id']); save(WORK / 'composition-job.json', job); continue
            history = PARTS / 'history'
            history.mkdir(exist_ok=True)
            dest.rename(history / (dest.stem + '-' + str(time.time_ns()) + '.mkv'))
        temp = PARTS / (part['id'] + '-encoding.mkv')
        if part.get('type') == 'shared_clock': comparison(part, temp)
        else:
            source = OUT / 'shots' / (part['shot'] + '.mp4')
            assert sha(source) == plan['selected_shots'][part['shot']]['sha256']
            span = part['source_span_s'] or (plan['selected_shots'][part['shot']]['duration_s'] - part['source_start_s'])
            filters = ['trim=end_frame=1', 'setpts=PTS-STARTPTS', f'tpad=stop_mode=clone:stop_duration={part["duration_s"]}'] if part['hold_frame'] else [f'trim=duration={span}', f'setpts=(PTS-STARTPTS)*{part["duration_s"]/span:.12f}', 'tpad=stop_mode=clone:stop_duration=1']
            if part.get('crop'):
                x,y,w,h = part['crop']
                filters += [f'crop={w}:{h}:{x}:{y}', 'scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos', 'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x090e11']
            filters += ['fps=30', 'setsar=1']
            command = ['ffmpeg', '-v', 'error', '-y', '-filter_threads', '1', '-threads', '1', '-ss', str(part['source_start_s']),
                       '-i', str(source), '-vf', ','.join(filters), *lossless(temp, round(part['duration_s']*FPS))]
            run(command, part['id'])
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=nb_read_frames,width,height','-of','json',str(temp)], text=True))
        assert int(probe['streams'][0]['nb_read_frames']) == round(part['duration_s']*FPS), part['id']
        temp.replace(dest)
        save(ledger, {'id': part['id'], 'status': 'complete', 'identity': ident, 'source_selection': part, 'path': str(dest), 'sha256': sha(dest),
                      'encoding': 'lossless intermediate, libx264 CRF0; no sharpness or new physical states'})
        job['completed'].append(part['id']); job['current'] = None; save(WORK / 'composition-job.json', job)
        status('成片镜头 ' + part['id'], dest, f'完成：{part["duration_s"]:.3f}s；原shots裁取/变速/终态保持，无新物理')
        print(part['id'], 'complete', flush=True)

def wrap(text):
    font = ImageFont.truetype(FONT, 46)
    if font.getlength(text) <= 1550: return text
    punctuation = [i+1 for i,c in enumerate(text) if c in '，。；：' and len(text)*.25 < i < len(text)*.75]
    positions = punctuation or list(range(len(text)//3, len(text)*2//3))
    split = min(positions, key=lambda i: max(font.getlength(text[:i]), font.getlength(text[i:])))
    assert max(font.getlength(text[:split]), font.getlength(text[split:])) <= 1550, text
    return text[:split] + r'\N' + text[split:]

def subtitles():
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,WenQuanYi Zen Hei,46,&H00FFFFFF,&H00FFFFFF,&H20000000,&H90000000,0,0,0,0,100,100,0,0,1,3,0,2,160,160,38,1
Style: CaptionTop,WenQuanYi Zen Hei,46,&H00FFFFFF,&H00FFFFFF,&H20000000,&H90000000,0,0,0,0,100,100,0,0,1,3,0,8,160,160,150,1
Style: Label,WenQuanYi Zen Hei,28,&H00F2F2F2,&H00FFFFFF,&H70000000,&H90000000,0,0,0,0,100,100,0,0,3,8,0,7,40,40,40,1
Style: Accent,WenQuanYi Zen Hei,36,&H00C0E5D5,&H00FFFFFF,&H50000000,&H90000000,1,0,0,0,100,100,0,0,1,2,0,7,40,40,40,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines = []
    def add(a,b,text,style='Label',prefix=''):
        lines.append(f'Dialogue: 1,{stamp(a)},{stamp(b)},{style},,0,0,0,,{prefix}{text}')
    vtt = ['WEBVTT','']
    for s in timeline['captions']:
        add(s['start_s'],s['end_s'],wrap(s['text']), 'CaptionTop' if s['group']=='connect' else 'Caption', r'{\fad(100,100)}')
        vtt.extend([f'{vtt_stamp(s["start_s"])} --> {vtt_stamp(s["end_s"])}',s['text'],''])
    for part in timeline['parts']:
        a,b=part['start_s'],part['end_s']
        add(a,b,part['chapter'],'Accent',r'{\pos(40,35)\fs32}')
        if part.get('label'): add(a,b,part['label'],prefix=r'{\pos(40,82)\fs25}')
    compare = next(g for g in timeline['groups'] if g['id']=='comparison')
    clock=timeline['shared_r1_clock'];duration=compare['duration_s'];knots=np.array(clock['knots'])
    titles=['乐观：未知当没有','保守：未知当危险','想象：先检验，再走']
    terminals=[plan['r1']['optimistic'],plan['r1']['conservative'],plan['r1']['imagination']]
    outcomes=['碰撞','停车 · 看五眼','到达 · 看一眼']
    for k in range(math.ceil(duration*10)):
        t=k/10;v=float(np.interp(t,knots[:,0],knots[:,1]));a=compare['start_s']+t;b=min(compare['end_s'],a+.1)
        focus=0 if t<clock['focus_switches'][0] else 2 if t<clock['focus_switches'][1] else 1
        other=[i for i in range(3) if i!=focus]
        add(a,b,f'共同仿真时钟 {v:.2f} 秒',prefix=r'{\pos(40,896)\fs25}')
        for i in range(3):
            x,y=(40,130) if i==focus else (1460,145+other.index(i)*390)
            title=titles[i] if v<terminals[i]-.01 else f'{outcomes[i]} · {terminals[i]:.2f}秒'
            add(a,b,title,prefix=f'{{\\pos({x},{y})\\fs{30 if i==focus else 23}}}')
    results=next(g for g in timeline['groups'] if g['id']=='results')
    d=plan['decisive']
    add(results['start_s'],results['start_s']+15,f'预先定义的 {d["count"]} 个决定性场景'+r'\N'+f'到达 {d["arrived"]}  ·  停车 {d["stopped"]}  ·  碰撞 {d["collisions"]}',prefix=r'{\pos(1210,160)\fs28}')
    post=next(g for g in timeline['groups'] if g['id']=='post');d=plan['post']
    add(post['start_s'],post['end_s'],f'赛后修订 · {d["count"]} 场'+r'\N'+f'到达 {d["arrived"]}  ·  停车 {d["stopped"]}  ·  碰撞 {d["collisions"]}'+r'\N已知场景与留出场景合计',prefix=r'{\pos(1180,180)\fs30}')
    leg=next(g for g in timeline['groups'] if g['id']=='leg');d=plan['legs']
    add(leg['start_s'],leg['end_s'],f'轮行：{d["wheel_passes"]} / {d["wheel_trials"]}'+r'\N'+f'逐轮跨越：{d["leg_clean"]} / {d["leg_trials"]}'+r'\N'+f'{d["true_rocks"]} 块真石头也跨过',prefix=r'{\pos(1450,165)\fs28}')
    for ident,vehicle in [('stopA','A'),('stopB','B')]:
        g=next(g for g in timeline['groups'] if g['id']==ident);d=plan['gate'][vehicle]
        add(g['start_s'],g['end_s'],f'执行仿真 {d["seconds"]:.2f} 秒 · {d["looks"]} 眼'+r'\N门槛段未发生',prefix=r'{\pos(40,150)\fs26}')
    ending=next(g for g in timeline['groups'] if g['id']=='ending');a,b=ending['start_s'],ending['end_s'];d=plan['current_lux_counts']
    add(a,b,'BeforeStep','Accent',r'{\pos(45,180)\fs76}')
    add(a,b,'让想象先被检验，再迈步。',prefix=r'{\pos(48,280)\fs38}')
    add(a,b,f'{d["created"]} 次 Lux3D 真实创建'+r'\N'+f'{d["ok"]} 份 GLB  ·  {d["failed"]} 次服务端失败',prefix=r'{\pos(48,385)\fs31}')
    add(a,b,'以上均为 MuJoCo 仿真实录',prefix=r'{\pos(48,500)\fs28}')
    add(a,b,'codezzzsleep.github.io/next-zenith-beforestep/',prefix=r'{\pos(48,850)\fs28}')
    add(0,13,'MuJoCo 仿真实录 · 原运行状态回放',prefix=r'{\an9\pos(1875,45)\fs24}')
    (WORK/'film.ass').write_text(header+'\n'.join(lines)+'\n')
    (OUT/'demo-v6.zh.vtt').write_text('\n'.join(vtt))
    save(WORK/'subtitle-audit.json',{'captions':[{'text':s['text'],'rendered':wrap(s['text']),'start_s':s['start_s'],'end_s':s['end_s'],'audio':s['audio']} for s in timeline['captions']],
                                     'maximum_lines':2,'narration_text_equal':True,'connect_caption_position':'top to preserve original transition annotation'})

def make_audio():
    args=[];filters=[];labels=[]
    for i,s in enumerate(timeline['captions']):
        args+=['-i',str(resolve(s['audio']))]
        label=f'a{i}';labels.append('['+label+']')
        filters.append(f'[{i}:a]aresample=48000,adelay={round(s["start_s"]*1000)}:all=1[{label}]')
    filters.append(''.join(labels)+f'amix=inputs={len(labels)}:normalize=0,apad,atrim=duration={timeline["duration_s"]}[mix]')
    run(['ffmpeg','-v','error','-y','-filter_complex_threads','1',*args,'-filter_complex',';'.join(filters),'-map','[mix]','-ac','1','-ar','48000','-c:a','pcm_s16le',str(WORK/'narration-unmastered.wav')],'voice-align')
    run(['ffmpeg','-v','info','-y','-filter_threads','1','-i',str(WORK/'narration-unmastered.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json',
         '-ar','48000','-ac','1','-c:a','pcm_s16le',str(WORK/'narration.wav')],'voice-master')

def finish():
    subtitles();make_audio()
    for part in timeline['parts']:
        assert (PARTS/(part['id']+'.mkv')).exists()
    listing=WORK/'concat.txt'
    listing.write_text(''.join("file '"+str(PARTS/(p['id']+'.mkv'))+"'\n" for p in timeline['parts']))
    connect=next(g for g in timeline['groups'] if g['id']=='connect')
    vf=f"drawbox=x=0:y=920:w=iw:h=160:color=black@0.64:t=fill:enable='not(between(t,{connect['start_s']},{connect['end_s']}))',drawbox=x=0:y=128:w=iw:h=138:color=black@0.58:t=fill:enable='between(t,{connect['start_s']},{connect['end_s']})',ass={WORK/'film.ass'}"
    temp=OUT/'demo-v6-encoding.mp4'
    run(['ffmpeg','-v','warning','-y','-filter_threads','1','-threads','2','-f','concat','-safe','0','-i',str(listing),'-i',str(WORK/'narration.wav'),
         '-vf',vf,'-map','0:v:0','-map','1:a:0','-frames:v',str(timeline['frames']),'-r','30','-c:v','libx264','-preset','slow','-crf','14','-threads','3',
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','1','-movflags','+faststart',str(temp)],'final-encode')
    dest=OUT/'demo-v6.mp4';temp.replace(dest)
    save(WORK/'delivery.json',{'status':'encoded_pending_verification','path':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size,
                              'duration_s':timeline['duration_s'],'frames':timeline['frames'],'voice_provider':'MiniMax','narration_text_same_as_subtitles':True,
                              'music':False,'plan':str(WORK/'plan.json'),'timeline':str(WORK/'timeline.json'),'selected_shots_only':True,
                              'original_shots_unchanged':True,'new_physics_runs':0,'new_Lux3D_tasks':0,'gpu_shutdown':False})
    status('完整视频编码完成',dest,f'{timeline["duration_s"]:.3f}s/1080p30/H264 CRF14 slow；MiniMax中文配音/同稿烧字；待完整解码及画面复核')
    print('FINAL FILM ENCODED',dest,flush=True)

try:
    status('完整视频剪辑启动',WORK/'timeline.json',f'配音实测后定稿{timeline["duration_s"]:.3f}s；原shots合成、同一R1时钟，GPU保持开机')
    if args.phase in ['parts','all']: build_parts()
    if args.phase in ['finish','all']: finish()
    job.update(status='complete',current=None,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(WORK/'composition-job.json',job)
    state.update(status='encoded_pending_verification' if args.phase in ['finish','all'] else 'lossless_parts_ready',live_jobs=[],next='Verify complete decode, narration/captions and representative frames; package final film')
    save(WORK/'state.json',state)
except BaseException as e:
    job.update(status='failed',error=str(e));save(WORK/'composition-job.json',job)
    state.update(status='composition_error_review_required',live_jobs=[],next='Inspect composition-job and corresponding log; retain completed parts')
    save(WORK/'state.json',state)
    raise
