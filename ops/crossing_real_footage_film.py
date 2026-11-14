"""Build the low-stone proof clip and the eight source-bound film chapters."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'real-footage-180';PARTS=WORK/'parts';PARTS.mkdir(exist_ok=True)
OUT=ROOT/'site/media/real-footage';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(p)],text=True))
def run(cmd,name):
 save(WORK/'film-live.json',{'stage':name,'command':cmd});(WORK/'logs').mkdir(exist_ok=True)
 with (WORK/'logs'/(name+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=f,check=True)
def output(p,seconds):return ['-frames:v',str(round(seconds*30)),'-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','19','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(p)]
FIT='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x080b0d,setsar=1'
def encode(name,source,seconds,start=0,span=None,crop=None):
 assert source.exists(),source;span=span or float(probe(source)['format']['duration'])-start
 vf=(f'crop={crop},' if crop else '')+f'trim=duration={span},setpts=(PTS-STARTPTS)*{seconds/span:.12f},fps=30,'+FIT+',tpad=stop_mode=clone:stop_duration=1'
 p=PARTS/(name+'.mp4');run(['ffmpeg','-v','error','-y','-filter_threads','1','-ss',str(start),'-i',str(source),'-vf',vf,*output(p,seconds)],name);return p
def concat(names,name,dest=None):
 paths=[p if isinstance(p,Path) else PARTS/(p+'.mp4') for p in names];listing=PARTS/(name+'.txt');listing.write_text(''.join("file '"+str(p)+"'\n" for p in paths));dest=dest or PARTS/(name+'.mp4')
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(dest)],name);return dest
def frames(name,group,start,count):
 base=ROOT/'outputs/crossing/route/handoff/frames'/group;index=base/'index.json';d=json.loads(index.read_text());rows=[x for x in d['frames'] if x['camera']=='side_follow' and start<=x['index']<start+count];assert len(rows)==count
 selected=[]
 for row in rows:
  p=base/'side_follow'/f'{row["index"]:05d}.jpg';assert sha(p)==row['sha256'];selected.append({'path':str(p.relative_to(ROOT)),'sha256':row['sha256'],'source_s':row['physics_time_s']})
 p=OUT/(name+'.mp4');run(['ffmpeg','-v','error','-y','-filter_threads','1','-framerate','30','-start_number',str(start),'-i',str(base/'side_follow/%05d.jpg'),'-vf',FIT,*output(p,count/30)],name)
 meta={'id':name,'scene':'stress_v8_gate','formal_vehicle_run':False,'recording_type':'original_recorded_state_camera_frames','physics_advanced':False,'source_index':str(index.relative_to(ROOT)),'source_index_sha256':sha(index),'source_files':d['source_runs'],'source_resolution':[1280,720],'output_resolution':[1920,1080],'playback_speed':1,'duration_s':count/30,'camera':d['cameras']['side_follow'],'source_time_range_s':[rows[0]['physics_time_s'],rows[-1]['physics_time_s']],'selected_frames':selected,'path':str(p.relative_to(ROOT/'site')),'sha256':sha(p)}
 save(ROOT/'site/data/real-footage-sources'/(name+'.json'),meta);return p
def low_parts():
 frames('low-stone-wheel','wheel-stuck',0,150)
 frames('low-stone-full-lift','sill-close',750,420)
 encode('low-depart-6',OUT/'low-stone-depart.mp4',6)
def preview():
 low_parts();encode('preview-wheel',OUT/'low-stone-wheel.mp4',5);encode('preview-lift',OUT/'low-stone-full-lift.mp4',14)
 clean=concat(['preview-wheel','preview-lift','low-depart-6'],'preview-clean',OUT/'low-stone-preview-clean.mp4')
 events=[(0,5,'轮行：接触门槛，停在这里。'),(5,19,'换成轮腿：完整抬轮、越过、落地。'),(19,25,'同一条预检查记录，随后整车离开门槛。')]
 ass=write_ass('preview',events,[(0,25,'stress_v8_gate / 同石独立预检查 / 原速片段剪辑')]);dest=OUT/'low-stone-preview.mp4'
 run(['ffmpeg','-v','error','-y','-filter_threads','1','-i',str(clean),'-vf',f'ass={ass}',*output(dest,25)],'preview-captions')
 run(['ffmpeg','-v','error','-y','-ss','11','-i',str(dest),'-frames:v','1',str(OUT/'low-stone-preview.jpg')],'preview-poster')
 save(WORK/'preview.json',{'status':'complete','path':str(dest.relative_to(ROOT/'site')),'clean':str(clean.relative_to(ROOT/'site')),'duration_s':25,'metadata':probe(dest),'sha256':sha(dest),'continuous_complete_lift_source_s':[50.14,64.10666666668],'source_scene':'stress_v8_gate','formal_vehicle_run':False,'all_actions_from_original_records':True});print('25 SECOND ORIGINAL ACTION PREVIEW COMPLETE',flush=True)
def at(s):
 c=round(s*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
def write_ass(name,captions,labels,extra=()):
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,WenQuanYi Zen Hei,43,&H00FFFFFF,&H00FFFFFF,&HA8000000,&HA8000000,0,0,0,0,100,100,0,0,3,8,0,2,90,90,42,1
Style: Label,WenQuanYi Zen Hei,30,&H00FFFFFF,&H00FFFFFF,&HA8000000,&HA8000000,0,0,0,0,100,100,0,0,3,7,0,7,35,35,28,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 lines=[]
 if name=='film':header=header.replace('Hei,43,','Hei,62,')
 for a,b,text in captions:
  if len(text)>(26 if name=='film' else 35):
   points=[i+1 for i,c in enumerate(text) if c in '，。；：' and len(text)*.3<i<len(text)*.7];k=min(points,key=lambda i:abs(i-len(text)/2)) if points else len(text)//2;text=text[:k]+'\\N'+text[k:]
  lines.append(f'Dialogue: 0,{at(a)},{at(b)},Caption,,0,0,0,,{text}')
 for a,b,text in labels:lines.append(f'Dialogue: 1,{at(a)},{at(b)},Label,,0,0,0,,{text}')
 lines.extend(extra);p=WORK/(name+'.ass');p.write_text(header+'\n'.join(lines)+'\n');return p
def base():
 encode('01-fixed',OUT/'r1-opening-fixed.mp4',2,span=2);encode('01-follow',OUT/'r1-opening-follow.mp4',13,start=2,span=13);concat(['01-fixed','01-follow'],'01')
 encode('02-wheel',OUT/'low-stone-wheel.mp4',4,span=4);encode('02-lift',OUT/'low-stone-full-lift.mp4',14);encode('02-depart',OUT/'low-stone-depart.mp4',2,start=4,span=2);concat(['02-wheel','02-lift','02-depart'],'02')
 encode('03-eye',OUT/'r1-first-person.mp4',6)
 image=ROOT/'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/rgb.png';run(['ffmpeg','-v','error','-y','-filter_threads','1','-loop','1','-i',str(image),'-vf',FIT,*output(PARTS/'03-input.mp4',4)],'03-input')
 save(ROOT/'site/data/real-footage-sources/r1-observation-input.json',{'id':'r1-observation-input','scene':'stress_v8','recording_type':'original_observation_single_frame','source':str(image.relative_to(ROOT)),'source_sha256':sha(image),'original_sim_time_s':16.08,'duration_s':4,'purpose':'原观测单帧，明确静止展示；不作为运动或到达尾镜','physics_advanced':False})
 encode('03-external',OUT/'r1-observation-external.mp4',8);concat(['03-eye','03-input','03-external'],'03')
 encode('04',OUT/'r1-candidate-records.mp4',22)
 encode('05-full',OUT/'rehearsal-full-00.mp4',18)
 for k in range(3):
  files=[ROOT/'site/media/footage'/f'world-{i:02d}.mp4' for i in range(1+k*4,min(1+(k+1)*4,12))];count=len(files)
  inputs=[];filters=[]
  for i,f in enumerate(files):inputs+=['-ss','3','-i',str(f)];filters.append(f'[{i}:v]trim=duration=4,setpts=PTS-STARTPTS,scale=960:540,setsar=1[v{i}]')
  filters.append('[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|960_0|0_540|960_540[v]' if count==4 else '[v0][v1][v2]xstack=inputs=3:layout=0_0|960_0|480_540:fill=0x080b0d[v]')
  run(['ffmpeg','-v','error','-y','-filter_complex_threads','1',*inputs,'-filter_complex',';'.join(filters),'-map','[v]',*output(PARTS/f'05-other-{k}.mp4',4)],f'05-other-{k}')
 concat(['05-full','05-other-0','05-other-1','05-other-2'],'05')
def late():
 inputs=[];filters=[]
 for i,p in enumerate(['optimistic','conservative','imagination']):inputs+=['-i',str(OUT/f'r1-synchronised-{p}.mp4')];filters.append(f'[{i}:v]setpts=PTS*40/42,fps=30,tpad=stop_mode=clone:stop_duration=2,scale=640:1080,setsar=1[v{i}]')
 filters.append('[v0][v1][v2]hstack=inputs=3[v]');run(['ffmpeg','-v','error','-y','-filter_complex_threads','1',*inputs,'-filter_complex',';'.join(filters),'-map','[v]',*output(PARTS/'06.mp4',42)],'06')
 encode('07-overlay',ROOT/'outputs/crossing/route/video/shots/4.mp4',4,start=3,span=4,crop='660:500:400:200');encode('07-failure',OUT/'f3-004-contact.mp4',12);concat(['07-overlay','07-failure'],'07')
 source=ROOT/'outputs/crossing/route/video/shots/4.mp4';overlay=ROOT/'site/home-assets/glb/overlay/stress_v8-T2-A2.glb';save(ROOT/'site/data/real-footage-sources/r1-overlay.json',{'id':'r1-overlay','scene':'stress_v8','diagnostic_only':True,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_file_time_s':[3,7],'overlay':str(overlay.relative_to(ROOT)),'overlay_sha256':sha(overlay),'back_short_m':.7,'not_the_error_of_f3_004':True,'recording_type':'original_3D_overlay_browser_recording'})
 encode('08',OUT/'r1-tail.mp4',17)
def finish():
 durations=[15,20,18,22,30,42,16,17]
 for i,n in enumerate(durations,1):assert int(probe(PARTS/f'{i:02d}.mp4')['streams'][0]['nb_frames'])==n*30
 clean=concat([f'{i:02d}' for i in range(1,9)],'master-clean',ROOT/'site/media/demo-v4-clean.mp4')
 captions=[(0,15,'前往目标点。先看清这条路。'),(15,19,'换到独立低石预检查：轮行在门槛前受阻。'),(19,33,'同一块石头，完整抬轮、越过、落地。'),(33,35,'随后，整车离开门槛。'),(35,45,'从这里，我只能看见它的一面。'),(45,53,'外部机位只给观众解释，机器人没有获得背面真值。'),(53,64,'这是已有任务返回的原模型，输入与任务号逐项对应。'),(64,75,'另一块石头也有自己的原观测和候选。'),(75,93,'先在一个真实候选世界中，完整开到终点。'),(93,105,'六种 A 与两种 B，十二个组合都完成原预演。'),(105,123,'回到同一条 R1 路。三种策略，共用一条仿真时钟。'),(123,133,'直冲车实际碰到了石头，画面停在它的原终态。'),(133,142,'想象车绕过去，到达目标点。'),(142,147,'保守车没有到达，总共进行了五次观测。'),(147,151,'R1 事后核对：这一份背面短了 0.70 米。'),(151,157,'另一个场景 F3_004：预演通过，仍不能保证真实执行。'),(157,163,'接触前后连续保留；原记录到碰撞就结束。'),(163,176,'回到 R1，连续看完到达尾段。'),(176,180,'先在假设里走一步。有效，也有边界。')]
 labels=[(0,15,'R1 / 原运行状态回放 / 约 1×'),(15,35,'stress_v8_gate / 同石独立预检查 / 原速片段剪辑'),(35,41,'R1 / 原相机方向 / 仿真 14.08–16.08 秒'),(41,45,'R1 / 原始输入单帧 / 仿真 16.08 秒'),(45,53,'R1 / 同时刻外部解释机位'),(53,75,'R1 / 已有任务产物的实际加载与旋转录屏'),(75,93,'原预演组合 1 / 完整原轨迹约 5.34×'),(93,97,'原预演组合 2 / 3 / 4 / 5'),(97,101,'原预演组合 6 / 7 / 8 / 9'),(101,105,'原预演组合 10 / 11 / 12'),(105,147,'R1 / 同场同机位 / 同步变速回放，关键段减速'),(147,151,'仅 R1 的原扫描与生成模型叠合 / 事后诊断'),(151,163,'另一个场景 F3_004 / 原事故记录 / 约 1× / 终止即停'),(163,176,'R1 / 仿真 98.00–112.84 秒连续原记录 / 1×'),(176,180,'codezzzsleep.github.io/next-zenith-beforestep/')]
 extra=[];clock=json.loads((WORK/'comparison-clock.json').read_text());clock['capture_output_knots_s']=clock['output_knots_s'][:];clock['output_knots_s']=[x*40/42 for x in clock['output_knots_s']]+[42];clock['sim_knots_s']=clock['sim_knots_s']+[clock['sim_knots_s'][-1]];clock['final_original_terminal_hold_s']=2
 for k in range(3):
  first=2+k*4;count=min(4,13-first)
  for j in range(count):
   x,y=(35+(j%2)*960,85+(j//2)*540) if count==4 else (35+(j%2)*960,85) if j<2 else (515,625)
   extra.append(f'Dialogue: 2,{at(93+k*4)},{at(97+k*4)},Label,,0,0,0,,{{\\pos({x},{y})\\fs28}}组合 {first+j} / 原预演')
 import numpy as np
 ends=[80.866,142.2,112.84];names=['直冲','保守','先想象'];results=['碰撞','未到达 · 共5次观测','到达']
 for k in range(420):
  a=k/10;b=(k+1)/10;t=float(np.interp(a,clock['output_knots_s'],clock['sim_knots_s']))
  extra.append(f'Dialogue: 2,{at(105+a)},{at(105+b)},Label,,0,0,0,,{{\\pos(35,75)}}共同仿真时钟 {t:.2f} 秒')
  for i in range(3):
   text=names[i] if t<ends[i] else f'{names[i]} / {results[i]} / 终态 {ends[i]:.2f} 秒'
   extra.append(f'Dialogue: 2,{at(105+a)},{at(105+b)},Label,,0,0,0,,{{\\pos({35+i*640},120)\\fs27}}{text}')
 extra.append(f'Dialogue: 2,{at(177.84)},{at(180)},Label,,0,0,0,,{{\\pos(35,78)}}到达目标点 / 仿真 112.84 秒 / 原终态停帧')
 ass=write_ass('film',captions,labels,extra);dest=ROOT/'site/media/demo-v4.mp4';run(['ffmpeg','-v','error','-y','-filter_threads','1','-i',str(clean),'-vf',f'ass={ass}',*output(dest,180)],'final-captions')
 save(WORK/'captions.json',{'captions':captions,'labels':labels});vtt=['WEBVTT','']
 for a,b,t in captions:vtt+=[f'{a//3600:02d}:{a//60%60:02d}:{a%60:02d}.000 --> {b//3600:02d}:{b//60%60:02d}:{b%60:02d}.000',t,'']
 (ROOT/'site/media/demo-v4.zh.vtt').write_text('\n'.join(vtt))
 save(WORK/'delivery.json',{'status':'complete','path':str(dest.relative_to(ROOT/'site')),'clean_master':str(clean.relative_to(ROOT/'site')),'duration_s':180,'metadata':probe(dest),'sha256':sha(dest),'clean_sha256':sha(clean),'no_diagram_substitutes':True,'shared_r1_clock':clock,'original_records_only':True,'new_physics_runs':0,'new_generation_tasks':0});print('180 SECOND ORIGINAL RECORDING FILM COMPLETE',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['preview','early','late','base','finish','all'],required=True);a=p.parse_args()
 if a.stage=='preview':preview()
 if a.stage in ('early','base','all'):base()
 if a.stage in ('late','base','all'):late()
 if a.stage in ('finish','all'):finish()
