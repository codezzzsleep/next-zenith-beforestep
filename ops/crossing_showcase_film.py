"""A 150-second film made entirely of recorded simulation and real GLB screen footage."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage';CLIPS=WORK/'film';CLIPS.mkdir(exist_ok=True)
SRC=ROOT/'site/media/footage';OLD=ROOT/'outputs/crossing/route/video/shots'
FONT='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc';DURATION=[8,32,14,24,18,18,18,10,8]
FIT='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x080b0d,setsar=1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,name):
 (WORK/'film-live.json').write_text(json.dumps({'phase':name,'command':cmd},indent=2))
 with (WORK/'logs'/f'film-{name}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,nb_frames,codec_name,codec_type,r_frame_rate','-of','json',str(p)],text=True))
def args(path,seconds):return ['-frames:v',str(round(seconds*30)),'-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','20','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
def encode(name,source,seconds,crop=None,start=0,span=None):
 assert source.exists(),str(source)+' is still being filmed'
 span=span or float(probe(source)['format']['duration'])-start
 vf=(f'crop={crop},' if crop else '')+f'trim=duration={span},setpts=(PTS-STARTPTS)*{seconds/span:.10f},fps=30,'+FIT+',tpad=stop_mode=clone:stop_duration=1'
 path=CLIPS/f'{name}.mp4';run(['ffmpeg','-hide_banner','-y','-filter_threads','1','-ss',str(start),'-i',str(source),'-vf',vf,*args(path,seconds)],name);return path
def concat(names,name):
 listing=CLIPS/f'{name}.txt';listing.write_text(''.join("file '"+str(CLIPS/(n+'.mp4'))+"'\n" for n in names));p=CLIPS/(name+'.mp4')
 run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(p)],name);return p
def multiple(name,files,seconds,rows=1,vertical=False,span=None,start=0,hold=0):
 inputs=[];chains=[]
 for i,f in enumerate(files):
  assert f.exists(),str(f)+' is still being filmed';inputs+=['-ss',str(start),'-i',str(f)]
  length=span or float(probe(f)['format']['duration'])-start
  scale='scale=-1:1080,crop=640:1080:(iw-640)/2:0' if vertical else 'scale=-1:1080,crop=960:1080:(iw-960)/2:0' if len(files)==2 else 'scale=960:540'
  ratio=1.0 if vertical else (seconds-hold)/length
  chains.append(f'[{i}:v]trim=duration={length},setpts=(PTS-STARTPTS)*{ratio:.12f},fps=30,tpad=stop_mode=clone:stop_duration=4,{scale},setsar=1[v{i}]')
 n=len(files)
 if vertical:chains.append(''.join(f'[v{i}]' for i in range(n))+f'hstack=inputs={n}[v]')
 else:
  assert n in (2,4)
  if n==2:chains.append('[v0][v1]hstack=inputs=2[v]')
  else:chains.append('[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|960_0|0_540|960_540[v]')
 p=CLIPS/f'{name}.mp4';run(['ffmpeg','-hide_banner','-y','-filter_complex_threads','1',*inputs,'-filter_complex',';'.join(chains),'-map','[v]',*args(p,seconds)],name);return p
def base():
 encode('01',SRC/'leg-close.mp4',8)
 multiple('02-duel',[SRC/'wheel-stuck.mp4',SRC/'leg-cross.mp4'],22)
 encode('02-close',SRC/'leg-close.mp4',10);concat(['02-duel','02-close'],'02')
 encode('03',OLD/'2.mp4',14,crop='1280:630:320:260')
 encode('04-one',SRC/'world-02.mp4',12)
 for g in range(3):multiple(f'04-four-{g}',[SRC/f'world-{i:02d}.mp4' for i in range(g*4,g*4+4)],4,start=4,span=4)
 concat(['04-one','04-four-0','04-four-1','04-four-2'],'04')
 multiple('05',[SRC/f'stress_v8-{p}.mp4' for p in ['optimistic','conservative','imagination']],18,vertical=True)
 encode('06-overlay',OLD/'4.mp4',12,crop='660:500:400:200')
 encode('07',SRC/'suite_r2_v4_F1_003_gate-D.mp4',18)
 encode('08',SRC/'suite_r2_v4_F0_002-imagination_strict.mp4',10)
 encode('09',SRC/'suite_r2_v4_F1_003_gate-D.mp4',8,start=14,span=4)
def remaining():
 assert json.loads((WORK/'recolor-queue.json').read_text())['status']=='complete','Wait for the retained world colour study to finish'
 multiple('04-four-0',[SRC/f'world-{i:02d}.mp4' for i in range(4)],4,start=4,span=4)
 concat(['04-one','04-four-0','04-four-1','04-four-2'],'04')
 encode('03-input',OLD/'2.mp4',8,crop='1280:630:320:260')
 encode('03-rejected',SRC/'rejected-6339854.mp4',6,start=8,span=6);concat(['03-input','03-rejected'],'03')
 multiple('07',[SRC/'suite_r2_v4_F1_003_gate-B.mp4',SRC/'suite_r2_v4_F1_003_gate-D.mp4'],18,hold=2)
 encode('06-collision',SRC/'suite_r2_v4_F3_004-imagination.mp4',6,start=8,span=6);concat(['06-overlay','06-collision'],'06')
def polish():
 encode('03-input',OLD/'2.mp4',8,crop='1280:630:320:260');concat(['03-input','03-rejected'],'03')
 encode('06-overlay',OLD/'4.mp4',12,crop='660:500:400:200');concat(['06-overlay','06-collision'],'06')
def at(t):
 c=round(t*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
def subtitles():
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,WenQuanYi Zen Hei,42,&H00FFFFFF,&H00FFFFFF,&HA8000000,&HA8000000,0,0,0,0,100,100,0,0,3,9,0,2,100,100,45,1
Style: Label,WenQuanYi Zen Hei,32,&H00FFFFFF,&H00FFFFFF,&HA8000000,&HA8000000,0,0,0,0,100,100,0,0,3,8,0,7,45,45,35,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 captions=[(0,8,'一辆轮腿小车。能滚，也能迈。'),(8,17,'碰到矮门槛，轮子滚不上去。'),(17,30,'同一块石头，轮腿逐轮抬起，跨过去。'),(30,40,'抬起，前送，落地。动作来自真实的原仿真运行。'),(40,48,'高石头的背面看不到。照片交给 Lux3D，得到整块三维。'),(48,54,'想出来的不能直接信。另一份被拒的模型，强行用它就会撞。'),(54,66,'先检查生成的石头，再让车在它构成的世界里试走。'),(66,78,'十二份原物理预演，都完整跑过。这里播放实际录像节选。'),(78,96,'同一个 R1 锚点，三种看法，三种实际结局。'),(96,102,'但通过检查的想象，背面仍然可能错。'),(102,108,'转到背面，这一份短了 0.70 米。'),(108,114,'原方法确实撞过。每一次都保留，也拍给你看。'),(114,132,'一条路上，先绕高石，再跨门槛。B 和 D 都到了。'),(132,142,'没把握，就停下。更安全，也可能走不到终点。'),(142,150,'先见一步。先检验，先预演，再迈步。')]
 labels=[(0,8,'BeforeStep / 原物理运行回放拍摄'),(8,40,'同场同石 / 原预检查 / 加速回放'),(40,48,'实际输入与实际 Lux3D 模型的公网页面录屏'),(48,54,'被拒模型的事后强制信任诊断 / 非正式运行'),(54,78,'在生成模型构成的世界里试走 / 真实预演录像'),(78,96,'R1 原三策略 / 各自完整轨迹加速 / 末态定格'),(96,108,'原扫描与原生成模型的实际 3D 叠合'),(108,114,'F3_004 / 原想象方法的实际碰撞回放'),(114,132,'F1_003 / B 与 D 的原正式运行 / 分别加速'),(132,142,'留出 F0_002 / 收紧方法的原停车回放'),(142,150,'codezzzsleep.github.io/next-zenith-beforestep/')]
 events=[]
 for a,b,t in captions:
  if len(t)>34:t=t[:len(t)//2]+'\\N'+t[len(t)//2:]
  events.append(f'Dialogue: 0,{at(a)},{at(b)},Caption,,0,0,0,,{t}')
 for a,b,t in labels:events.append(f'Dialogue: 1,{at(a)},{at(b)},Label,,0,0,0,,{t}')
 for x,t in [(45,'直接走'),(685,'谨慎走'),(1325,'先想象，再走')]:events.append(f'Dialogue: 2,{at(78)},{at(96)},Label,,0,0,0,,{{\\pos({x},100)}}{t}')
 for x,t in [(45,'没有看见的，当作空地'),(685,'看不清，先停下'),(1325,'先检查，逐世界试走')]:events.append(f'Dialogue: 2,{at(78)},{at(92)},Label,,0,0,0,,{{\\pos({x},155)\\fs27}}{t}')
 for x,t in [(45,'碰撞 · 仿真 80.87 秒'),(685,'未到达 · 仿真 142.20 秒'),(1325,'到达 · 仿真 112.84 秒')]:events.append(f'Dialogue: 2,{at(92)},{at(96)},Label,,0,0,0,,{{\\pos({x},155)\\fs28}}{t}')
 events.append(f'Dialogue: 2,{at(114)},{at(132)},Label,,0,0,0,,{{\\pos(45,100)}}B / 只信看见的，有腿')
 events.append(f'Dialogue: 2,{at(114)},{at(132)},Label,,0,0,0,,{{\\pos(1030,100)}}D / 想象，有腿')
 events.append(f'Dialogue: 2,{at(130)},{at(132)},Label,,0,0,0,,{{\\pos(45,160)}}B：到达')
 events.append(f'Dialogue: 2,{at(130)},{at(132)},Label,,0,0,0,,{{\\pos(1030,160)}}D：到达')
 events.append(f'Dialogue: 2,{at(8)},{at(30)},Label,,0,0,0,,{{\\pos(45,180)}}轮行')
 events.append(f'Dialogue: 2,{at(8)},{at(30)},Label,,0,0,0,,{{\\pos(1030,180)}}逐轮跨越')
 p=WORK/'film-captions.ass';p.write_text(header+'\n'.join(events)+'\n');(WORK/'film-caption-timing.json').write_text(json.dumps({'duration':150,'captions':captions,'labels':labels,'no_diagram_shots':True},ensure_ascii=False,indent=2));return p
def finish():
 for i,d in enumerate(DURATION,1):
  p=CLIPS/f'{i:02d}.mp4';m=probe(p);assert int(m['streams'][0]['nb_frames'])==d*30,(i,m)
 joined=concat([f'{i:02d}' for i in range(1,10)],'all');ass=subtitles();dest=ROOT/'site/media/demo-v3.mp4';tmp=dest.with_name('demo-v3-recording.mp4')
 run(['ffmpeg','-hide_banner','-y','-filter_threads','1','-i',str(joined),'-vf',f'ass={ass}',*args(tmp,150)],'captions');tmp.replace(dest)
 used=[SRC/(x+'.mp4') for x in ['wheel-stuck','leg-cross','leg-close','rejected-6339854','stress_v8-optimistic','stress_v8-conservative','stress_v8-imagination','suite_r2_v4_F3_004-imagination','suite_r2_v4_F1_003_gate-B','suite_r2_v4_F1_003_gate-D','suite_r2_v4_F0_002-imagination_strict']]+[SRC/f'world-{i:02d}.mp4' for i in range(12)]+[OLD/'2.mp4',OLD/'4.mp4']
 data={'status':'complete','path':'media/demo-v3.mp4','duration_s':150,'metadata':probe(dest),'bytes':dest.stat().st_size,'sha256':sha(dest),'no_diagram_shots':True,'sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in used],'new_experiments':0,'new_generation_tasks':0,'screen_recordings':['outputs/crossing/route/video/pages/2.json','outputs/crossing/route/video/pages/4.json']}
 (WORK/'film-delivery.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('REAL FOOTAGE FILM COMPLETE',dest,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['base','finish','all','polish'],default='all');a=p.parse_args()
 if a.stage in ('base','all'):base()
 if a.stage in ('finish','all'):remaining();finish()
 if a.stage=='polish':polish();finish()
