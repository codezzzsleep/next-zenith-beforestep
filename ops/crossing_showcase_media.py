"""Encode retained real cameras and assemble a public source-bound film index."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage';OUT=ROOT/'site/media/footage'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def retained(name,source,source_fps,seconds,origins,time_range,start=0,span=None):
 target=OUT/f'{name}.mp4';index=WORK/'clips'/f'{name}.json'
 if target.exists() and index.exists() and json.loads(index.read_text()).get('status')=='complete':return
 n=len(list(source.glob('*.jpg')));span=span or (n-start)/source_fps
 command=['ffmpeg','-hide_banner','-y','-filter_threads','1','-framerate',str(source_fps),'-start_number',str(start),'-i',str(source/'%05d.jpg'),'-vf',f'trim=duration={span},setpts=(PTS-STARTPTS)*{seconds/span:.12f},fps=30,tpad=stop_mode=clone:stop_duration=1','-frames:v',str(round(seconds*30)),'-an','-c:v','libx264','-preset','veryfast','-crf','20','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
 save(WORK/'encoding.json',{'status':'running','name':name,'command':command})
 with (WORK/'logs'/f'{name}.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
 poster=OUT/f'{name}.jpg';subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',str(target),'-frames:v','1',str(poster)],check=True)
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,nb_frames:format=duration','-of','json',str(target)],text=True))
 row={'status':'complete','id':name,'path':str(target.relative_to(ROOT/'site')),'poster':str(poster.relative_to(ROOT/'site')),'source_files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in origins],'source':str(origins[0].relative_to(ROOT)),'source_sha256':sha(origins[0]),'source_time_range_s':time_range,'physics_advanced':False,'recording_type':'retained_camera_frames_of_original_recorded_MuJoCo_states','approx_speed':(time_range[1]-time_range[0])/seconds,'clip_duration_s':seconds,'sha256':sha(target),'bytes':target.stat().st_size,'metadata':meta}
 save(index,row);print('ENCODED',name,flush=True)
def base():
 OUT.mkdir(parents=True,exist_ok=True);(WORK/'logs').mkdir(parents=True,exist_ok=True)
 fr=ROOT/'outputs/crossing/route/handoff/frames'
 for group,name,dur in [('wheel-stuck','wheel-stuck',15),('leg-cross','leg-cross',34)]:
  index=fr/group/'index.json';d=json.loads(index.read_text());origins=[index]+[ROOT/x['path'] for x in d['source_runs']];retained(name,fr/group/'side_follow',30,dur,origins,d['time_range_s'])
 index=fr/'sill-close/index.json';d=json.loads(index.read_text());source=ROOT/d['source_runs'][0]['path'];a=np.load(source);phase=a['phase'].astype(str);begin=float(a['t'][np.flatnonzero(phase=='front-right-lift')[0]]);end=float(a['t'][np.flatnonzero(phase=='front-right-seat')[-1]])
 start=round((begin-d['time_range_s'][0])*30);retained('leg-close',fr/'sill-close/side_follow',30,12,[index,source],[begin,end],start,end-begin)
 src=ROOT.parent/'video-eight-chapters/frames/f1-route';d=json.loads((src/'index.json').read_text());retained('suite_r2_v4_F1_003_gate-D',src,15,18,[ROOT/x['path'] for x in d['sources']],d['time_range_s'])
def manifest():
 clips={json.loads(p.read_text())['id']:{k:v for k,v in json.loads(p.read_text()).items() if k not in ('pid','rendered_frames')} for p in (WORK/'clips').glob('*.json') if json.loads(p.read_text()).get('status')=='complete'}
 for clip_id,c in clips.items():
  source=ROOT/c['source'];parent=source.parent
  summary=next((p for folder in [parent,parent.parent,parent.parent.parent] for p in [folder/'summary.json',folder/'result.json'] if p.exists()),None)
  if '/segment1/full-record/' in str(source) and (parent.parent.parent/'result.json').exists():summary=parent.parent.parent/'result.json'
  safe={}
  if summary:
   original=json.loads(summary.read_text());safe={k:original[k] for k in ['scene_id','policy','vehicle','status','result','total_result','sim_time_s','sim_seconds','looks','collision','reason','legs_used'] if k in original}
  if c.get('world_source',{}).get('pane'):
   summary=ROOT/c['world_source']['pane'];original=json.loads(summary.read_text());safe={k:original[k] for k in ['completed','collided','reason','contact'] if k in original}
  save(ROOT/'site/data/recordings'/f'{clip_id}.json',{'recording':c,'original_result':safe,'original_result_path':str(summary.relative_to(ROOT)) if summary else None,'original_result_sha256':sha(summary) if summary else None})
 levels=[]
 for row in read('site/data/levels.json')['levels']:
  levels.append({'id':row['id'],'runs':{k:{'clip':row['id']+'-'+k,'result':v['result'],'evidence':'data/recordings/'+row['id']+'-'+k+'.json'} for k,v in row['runs'].items() if k in ('optimistic','conservative','imagination')}})
 routes=[]
 for p in sorted((ROOT/'evidence/crossing/route').glob('summary*.json')):
  d=json.loads(p.read_text())
  if d.get('scene') not in ['stress_v8_gate','suite_r2_v4_F1_003_gate','suite_r2_v4_F2_001_gate','suite_r2_v4_F2_007_gate']:continue
  routes.append({'id':d['scene'],'runs':{v['vehicle']:{'clip':d['scene']+'-'+v['vehicle'],'result':v['total_result'],'evidence':'data/recordings/'+d['scene']+'-'+v['vehicle']+'.json'} for v in d['rows']}})
 failures=[]
 for scene in ['suite_r2_v4_F1_020','suite_r2_v4_F3_004']:
  row=next(r for r in levels if r['id']==scene);failures.append({'id':scene,'label':scene.replace('suite_r2_v4_','')+' · 原方法碰撞','runs':{'imagination':row['runs']['imagination']}})
 for row in read('evidence/reviews/beforestep_r3/summary.json')['holdouts']:
  failures.append({'id':row['scene'],'label':row['scene'].replace('suite_r2_v4_','')+' · 留出','runs':{k:{'clip':row['scene']+'-'+k,'result':v['summary']['result'],'evidence':'data/recordings/'+row['scene']+'-'+k+'.json'} for k,v in row['runs'].items() if k in ('imagination','imagination_strict')}})
 d={'schema':'beforestep-real-footage-showcase/v1','clips':clips,'levels':levels,'routes':routes,'failures':failures,'candidates':read('site/home-assets/data/site.json')['candidates'],'demo':'media/demo-v3.mp4','new_experiments':0,'new_generation_tasks':0,'scope':'Camera footage of saved full-joint physical runs; no diagrams substituted for recordings.'}
 save(ROOT/'site/data/footage.json',d);print('INDEX',len(clips),'clips',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--base',action='store_true');a=ap.parse_args()
 if a.base:base()
 manifest()
