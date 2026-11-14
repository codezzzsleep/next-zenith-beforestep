"""Edit retained, verified footage into a Lux3D-centered submission Demo."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps

from common import OUT, save, sha, status

W, H, FPS = 1920, 1080, 30
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
plan = json.loads((OUT / 'plan.json').read_text())
for directory in ['assets', 'parts', 'logs', 'qc']:
    (OUT / directory).mkdir(exist_ok=True)
job = {'id': 'lux3d-demo-compose', 'pid': os.getpid(), 'status': 'running',
       'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'completed': [], 'current': None, 'new_physics_runs': 0, 'new_Lux3D_tasks': 0}


def font(size):
    return ImageFont.truetype(FONT, size)


def run(command, name):
    with (OUT / 'logs' / (name + '.log')).open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=log)
        job['current'] = {'name': name, 'pid': process.pid, 'command': command}
        save(OUT / 'composition-job.json', job)
        rc = process.wait()
    if rc:
        raise RuntimeError(name + ' failed; inspect its log')
    job['current'] = None
    save(OUT / 'composition-job.json', job)


def stamp(t):
    c = round(t * 100)
    return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'


def vttstamp(t):
    c = round(t * 1000)
    return f'{c//3600000:02d}:{c//60000%60:02d}:{c//1000%60:02d}.{c%1000:03d}'


def wrap(text):
    f = font(46)
    if f.getlength(text) <= 1650:
        return text
    candidates = [i + 1 for i, c in enumerate(text) if c in '，。；：' and len(text)*.2 < i < len(text)*.8]
    if not candidates:
        candidates = list(range(len(text)//3, len(text)*2//3))
    split = min(candidates, key=lambda i: max(f.getlength(text[:i]), f.getlength(text[i:])))
    assert max(f.getlength(text[:split]), f.getlength(text[split:])) <= 1650, text
    return text[:split] + r'\N' + text[split:]


def timeline():
    groups, parts, captions = [], [], []
    cursor = 0
    for group in plan['groups']:
        spoken = []
        for sentence in group['sentences']:
            data = json.loads((OUT/'audio'/(sentence['id']+'.json')).read_text())
            assert data['status'] == 'complete' and data['request']['text'] == sentence['text']
            assert sha(data['path']) == data['sha256']
            spoken.append({**sentence, 'audio': data['path'], 'audio_sha256': data['sha256'],
                           'audio_duration_s': data['duration_s']})
        voice = sum(s['audio_duration_s'] for s in spoken)
        frames = math.ceil(max(group['base_duration_s'], voice + .45*(len(spoken)+1))*FPS)
        duration = frames / FPS
        gap = min(1.25, (duration-voice)/(len(spoken)+1))
        offset = min(.6, gap)
        for sentence in spoken:
            captions.append({**sentence, 'group': group['id'], 'start_s': cursor/FPS+offset,
                             'end_s': cursor/FPS+offset+sentence['audio_duration_s']})
            offset += sentence['audio_duration_s'] + gap
        assert offset-gap <= duration+.001
        groups.append({**group, 'start_s': cursor/FPS, 'end_s': (cursor+frames)/FPS,
                       'duration_s': duration, 'frames': frames})
        allocated = 0
        for i, part in enumerate(group['parts']):
            count = round(part['base_duration_s']/group['base_duration_s']*frames)
            if i == len(group['parts'])-1:
                count = frames-allocated
            parts.append({**part, 'group': group['id'], 'chapter': group['chapter'], 'frames': count,
                          'start_s': (cursor+allocated)/FPS, 'end_s': (cursor+allocated+count)/FPS,
                          'duration_s': count/FPS})
            allocated += count
        assert allocated == frames
        cursor += frames
    assert 145 <= cursor/FPS <= 185, cursor/FPS
    result = {'groups': groups, 'parts': parts, 'captions': captions, 'duration_s': cursor/FPS,
              'frames': cursor, 'plan_sha256': sha(OUT/'plan.json'), 'audio_stretched': False,
              'all_video_sources_retained': True, 'new_physics_runs': 0, 'new_Lux3D_tasks': 0}
    save(OUT/'timeline.json', result)
    return result


def assets(part):
    kind = part['kind']
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 139), fill=(8, 16, 20, 240))
    draw.rectangle((0, 932, W, H), fill=(8, 16, 20, 233))
    draw.text((48, 17), '先见一步  /  BeforeStep', font=font(25), fill='#ecf2ef')
    label = 'MuJoCo 仿真运行 · 真实生成资产'
    draw.text((W-48-font(24).getlength(label), 17), label, font=font(24), fill='#a3b4b4')
    draw.text((48, 57), part['chapter'], font=font(38), fill='#d2eee5')
    draw.text((50, 108), '照片  →  Lux3D 模型  →  核对  →  路线预演  →  行动',
              font=font(23), fill='#8eaaa5')
    draw.line((0, 139, W, 139), fill=(104, 150, 142, 180), width=1)
    if kind == 'pair':
        draw.text((1000, 883), 'Lux3D 返回的原始 3D 模型', font=font(29), fill='#d8e6e3')
    canvas.save(OUT/'assets'/(part['id']+'-overlay.png'))
    background = Image.new('RGB', (W, H), '#0b1419')
    draw = ImageDraw.Draw(background)
    if kind in ['pair', 'ending']:
        if kind == 'pair':
            draw.rectangle((50, 175, 835, 875), fill='#141f24')
            photo = ImageOps.contain(Image.open(plan['pair']['photo']).convert('RGB'), (735, 610), Image.Resampling.LANCZOS)
            background.paste(photo, (75+(735-photo.width)//2, 210+(610-photo.height)//2))
            draw.text((77, 824), '机器人原始照片', font=font(30), fill='#d8e6e3')
            draw.text((858, 469), '→', font=font(74), fill='#89d8c0')
            draw.text((978, 156), '官方 Aholo Viewer · 旋转查看背面', font=font(26), fill='#a5c6bc')
            draw.text((78, 883), '真实任务 5958685 · 照片与返回模型一一对应', font=font(25), fill='#a2b8b2')
        else:
            draw.text((70, 228), '先见一步', font=font(98), fill='#eff7f3')
            draw.text((74, 361), '照片 → 3D → 判断 → 行动', font=font(43), fill='#9cdec8')
            draw.text((77, 465), 'Lux3D：491 个真实任务', font=font(37), fill='#eef3f1')
            draw.text((77, 526), '460 份模型 · 31 次服务端失败', font=font(30), fill='#a9bbb7')
            draw.text((77, 613), '官方 Aholo Viewer · 原始模型可旋转', font=font(30), fill='#e5edeb')
            draw.text((77, 695), '源码、模型与实验记录公开可查', font=font(29), fill='#a9bbb7')
            draw.text((77, 755), 'codezzzsleep.github.io/', font=font(27), fill='#d2e2dc')
            draw.text((77, 795), 'next-zenith-beforestep/', font=font(27), fill='#d2e2dc')
    background.save(OUT/'assets'/(part['id']+'-background.png'))


ASSHEADER = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,WenQuanYi Zen Hei,46,&H00FFFFFF,&H00FFFFFF,&H20000000,&H90000000,0,0,0,0,100,100,0,0,1,2,0,2,130,130,36,1
Style: Label,WenQuanYi Zen Hei,27,&H00E9F2EE,&H00FFFFFF,&H50000000,&H90000000,0,0,0,0,100,100,0,0,3,5,0,7,40,40,40,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''


def subtitles(part, tl):
    lines = []
    def add(a, b, text, style='Label', prefix=''):
        if b > a:
            lines.append(f'Dialogue: 1,{stamp(a)},{stamp(b)},{style},,0,0,0,,{prefix}{text}')
    for sentence in tl['captions']:
        a = max(sentence['start_s'], part['start_s'])-part['start_s']
        b = min(sentence['end_s'], part['end_s'])-part['start_s']
        add(a, b, wrap(sentence['text']), 'Caption', r'{\fad(80,80)}')
    labels = {
        'viewer-ui': '真实网页与原始返回模型',
        'viewer-close': '真实任务 5958685 · 官方 Aholo Viewer 录屏',
        'check-model': '石头 B · 返回五份模型，其中两份准入',
        'question-rgb': '原始相机照片 · 背面没有被拍到',
        'world-main': '一份准入模型中的完整物理预演 · 加速回放',
        'world-grid': 'R1：12 个真实预演世界 · 全部安全才出发',
        'action-route': 'R1 · 一眼 · 112.84 仿真秒到达 · 加速回放',
        'back-error': 'R1 原模型与真实形状叠合 · 事后检查：背面短约 0.70 米',
        'safe-stop': '另场 F3_002 · 候选不可信，停车 · 门槛段未发生',
        'versions': 'V6 / V7 / V8 / v0.1 / v0.2 / v0.3 · 原照片与真实资产',
    }
    if part['id'] in labels:
        add(0, part['duration_s'], labels[part['id']], prefix=r'{\pos(48,161)}')
    if part['kind'] == 'comparison':
        previous = json.loads(Path('evidence/production-v6/film/timeline.json').read_text())['shared_r1_clock']
        knots = previous['knots']
        def interpolate(t):
            for (a, x), (b, y) in zip(knots, knots[1:]):
                if a <= t <= b:
                    return x+(y-x)*(t-a)/(b-a)
            return knots[-1][1]
        titles = ['乐观：未知当作没有', '保守：未知当作危险', '想象：Lux3D 模型先被检验']
        outcomes = ['碰撞 · 80.87 秒', '停车 · 五眼 · 142.20 秒', '到达 · 一眼 · 112.84 秒']
        terminal = [80.87, 142.2, 112.84]
        for i in range(math.ceil(part['duration_s']*10)):
            a = i/10; b = min(part['duration_s'], a+.1)
            original = a*part['span']/part['duration_s']; virtual = interpolate(original)
            focus = 0 if original < previous['focus_switches'][0] else 2 if original < previous['focus_switches'][1] else 1
            others = [j for j in range(3) if j != focus]
            for j in range(3):
                x, y = (38, 157) if j == focus else (1452, 145+others.index(j)*390)
                txt = titles[j] if virtual < terminal[j]-.01 else outcomes[j]
                add(a, b, txt, prefix=f'{{\\pos({x},{y})\\fs{27 if j==focus else 21}}}')
            add(a, b, f'共同仿真时钟 {virtual:.2f} 秒 · 终态保持', prefix=r'{\pos(38,901)\fs24}')
    target = OUT/'assets'/(part['id']+'.ass')
    target.write_text(ASSHEADER+'\n'.join(lines)+'\n')
    return target


def encode(part, tl, preview=False):
    assets(part)
    ass = subtitles(part, tl)
    overlay = OUT/'assets'/(part['id']+'-overlay.png')
    background = OUT/'assets'/(part['id']+'-background.png')
    command = ['ffmpeg', '-v', 'warning', '-y', '-filter_complex_threads', '1']
    kind = part['kind']
    if kind == 'image':
        command += ['-loop', '1', '-framerate', '30', '-i', part['source']]
    else:
        command += ['-threads', '1', '-ss', str(part.get('start', 0)), '-i', part['source']]
    command += ['-loop', '1', '-framerate', '30', '-i', str(overlay),
                '-loop', '1', '-framerate', '30', '-i', str(background)]
    if kind != 'image':
        base = f'[0:v]trim=duration={part["span"]},setpts=(PTS-STARTPTS)*{part["duration_s"]/part["span"]:.12f},fps=30,tpad=stop_mode=clone:stop_duration=1'
    else:
        base = '[0:v]setpts=PTS-STARTPTS,fps=30'
    if kind in ['pair', 'ending']:
        base += ',crop=555:480:410:189,scale=830:718:flags=lanczos,setsar=1[content]'
        graph = base+';[2:v][content]overlay=x=983:y=203:shortest=1[canvas]'
    elif kind == 'viewer':
        base += ',crop=555:480:410:189,scale=1540:745:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[content]'
        graph = base+';[2:v][content]overlay=x=(W-w)/2:y=174:shortest=1[canvas]'
    elif kind == 'image':
        crop = ',crop='+':'.join(map(str, [part['crop'][2],part['crop'][3],part['crop'][0],part['crop'][1]])) if part.get('crop') else ''
        base += crop+',scale=1820:720:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[content]'
        graph = base+';[2:v][content]overlay=x=(W-w)/2:y=180+(720-h)/2:shortest=1[canvas]'
    elif part.get('crop'):
        base += ',crop='+':'.join(map(str,[part['crop'][2],part['crop'][3],part['crop'][0],part['crop'][1]]))+',scale=1780:750:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[content]'
        graph = base+';[2:v][content]overlay=x=(W-w)/2:y=170+(750-h)/2:shortest=1[canvas]'
    else:
        graph = base+',setsar=1[canvas]'
    graph += f';[canvas][1:v]overlay=0:0:shortest=1,ass={ass}[v]'
    if preview:
        dest = OUT/'qc'/(part['id']+'-preview.jpg')
        command += ['-filter_complex', graph, '-map', '[v]', '-ss', str(min(part['duration_s']/2, 3)),
                    '-frames:v', '1', '-q:v', '2', str(dest)]
        run(command, part['id']+'-preview')
        return
    dest = OUT/'parts'/(part['id']+'.mp4')
    ledger = dest.with_suffix('.json')
    identity = hashlib.sha256(json.dumps(part, sort_keys=True).encode()+ass.read_bytes()+overlay.read_bytes()+background.read_bytes()).hexdigest()
    if dest.exists() and ledger.exists():
        old = json.loads(ledger.read_text())
        if old['identity'] == identity and old['sha256'] == sha(dest):
            job['completed'].append(part['id']); return
        history = OUT/'parts'/'history'; history.mkdir(exist_ok=True)
        stamp_id = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
        dest.rename(history/(part['id']+'-'+stamp_id+'.mp4'))
        ledger.rename(history/(part['id']+'-'+stamp_id+'.json'))
    temp = OUT/'parts'/(part['id']+'-encoding.mp4')
    command += ['-filter_complex', graph, '-map', '[v]', '-frames:v', str(part['frames']), '-an',
                '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-threads', '3',
                '-pix_fmt', 'yuv420p', '-r', '30', '-movflags', '+faststart', str(temp)]
    run(command, part['id'])
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'stream=nb_frames,width,height,duration', '-of', 'json', str(temp)], text=True))['streams'][0]
    assert int(probe['nb_frames']) == part['frames'], (part['id'],probe)
    temp.replace(dest)
    save(ledger, {'status':'complete','identity':identity,'sha256':sha(dest),'bytes':dest.stat().st_size,
                  'source_selection':part,'frame_count':part['frames'],'encoding':'H264 CRF14 slow; no sharpening'})
    job['completed'].append(part['id']); save(OUT/'composition-job.json',job)
    print(part['id'], part['duration_s'], 'complete', flush=True)


def finish(tl):
    inputs=[]; filters=[]; labels=[]
    for i,s in enumerate(tl['captions']):
        inputs += ['-i',s['audio']];labels.append(f'[a{i}]')
        filters.append(f'[{i}:a]aresample=48000,adelay={round(s["start_s"]*1000)}:all=1[a{i}]')
    filters.append(''.join(labels)+f'amix=inputs={len(labels)}:normalize=0,apad,atrim=duration={tl["duration_s"]},loudnorm=I=-16:TP=-1.5:LRA=7[mix]')
    run(['ffmpeg','-v','warning','-y','-filter_complex_threads','1',*inputs,'-filter_complex',';'.join(filters),
         '-map','[mix]','-ac','1','-ar','48000','-c:a','pcm_s16le',str(OUT/'narration.wav')],'audio-master')
    listing=OUT/'concat.txt';listing.write_text(''.join("file '"+str(OUT/'parts'/(p['id']+'.mp4'))+"'\n" for p in tl['parts']))
    temp=OUT/'BeforeStep-Lux3D-Demo-encoding.mp4'
    run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'narration.wav'),
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
         '-t',str(tl['duration_s']),'-movflags','+faststart',str(temp)],'final-mux')
    dest=OUT/'BeforeStep-Lux3D-Demo.mp4';assert not dest.exists(),'Preserve any prior final film before rebuilding'
    temp.replace(dest)
    vtt=['WEBVTT','']
    for s in tl['captions']:
        vtt += [f'{vttstamp(s["start_s"])} --> {vttstamp(s["end_s"])}',s['text'],'']
    (OUT/'BeforeStep-Lux3D-Demo.zh.vtt').write_text('\n'.join(vtt))
    save(OUT/'delivery.json',{'status':'encoded_pending_verification','file':str(dest),'bytes':dest.stat().st_size,
         'sha256':sha(dest),'duration_s':tl['duration_s'],'frames':tl['frames'],'encoding':'1920x1080 / 30fps / H264 CRF14 slow / AAC 48k',
         'Chinese_voice':True,'burned_captions':True,'same_text_as_narration':True,'new_physics_runs':0,'new_Lux3D_tasks':0})
    save(OUT/'subtitle-audit.json',{'maximum_lines':2,'narration_text_equal':True,'captions':[
         {k:s[k] for k in ['id','text','start_s','end_s','audio_sha256']}|{'rendered':wrap(s['text'])} for s in tl['captions']]})
    (OUT/'CUT_LIST.md').write_text('# Lux3D Demo 镜头表\n\n| 秒 | 画面 | 原来源 |\n| --- | --- | --- |\n'+''.join(
         f'| {p["start_s"]:.2f}–{p["end_s"]:.2f} | {p["chapter"]} / {p["id"]} | {p["source"]} |\n' for p in tl['parts']))
    print('FILM ENCODED',str(dest),tl['duration_s'],'seconds',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--finish',action='store_true');parser.add_argument('--parts-only',action='store_true');args=parser.parse_args()
    save(OUT/'composition-job.json',job)
    state=json.loads((OUT/'state.json').read_text());state.update(status='composing_Lux3D_demo',live_jobs=[{'id':job['id'],'pid':os.getpid(),'ledger':str(OUT/'composition-job.json')}]);save(OUT/'state.json',state)
    try:
        for path,record in plan['sources'].items():assert sha(path)==record['sha256'],path
        tl=timeline()
        if args.finish:finish(tl)
        else:
            for p in tl['parts']:
                assert shutil.disk_usage(OUT).free>1_500_000_000,'Insufficient working disk'
                encode(p,tl,preview=args.preview)
            if not args.preview and not args.parts_only:finish(tl)
        job.update(status='complete',current=None);save(OUT/'composition-job.json',job)
        state.update(status='layout_previews_ready' if args.preview else 'parts_ready' if args.parts_only else 'encoded_pending_verification',live_jobs=[],next='Inspect previews' if args.preview else 'Finish mux' if args.parts_only else 'Complete audiovisual verification and package');save(OUT/'state.json',state)
    except BaseException as error:
        job.update(status='failed',error=str(error));save(OUT/'composition-job.json',job)
        state.update(status='compose_failed_review_required',live_jobs=[],next='Inspect log; preserve completed parts');save(OUT/'state.json',state)
        raise
