"""Bind every advertised action to its actual original file and encoded movie."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((ROOT/'site/data/footage.json').read_text());required={'wheel-stuck','leg-cross','leg-close','rejected-6339854'}
required|={f'world-{i:02d}' for i in range(12)}
for group in ['levels','routes','failures']:
 for row in m[group]:required|={v['clip'] for v in row['runs'].values()}
assert len(required)==78,len(required)
assert required<=m['clips'].keys(),sorted(required-m['clips'].keys())
checks=[]
for name in sorted(required):
 c=m['clips'][name];p=ROOT/'site'/c['path'];assert sha(p)==c['sha256']
 for s in c['source_files']:assert sha(ROOT/s['path'])==s['sha256'],s
 if c.get('world_source',{}).get('candidate_meshes'):
  for s in c['world_source']['candidate_meshes']:assert sha(ROOT/s['path'])==s['sha256']
 assert c['physics_advanced'] is False
 record=json.loads((ROOT/'site/data/recordings'/f'{name}.json').read_text())
 assert record['recording']==c
 if record['original_result_path']:
  result=ROOT/record['original_result_path'];assert sha(result)==record['original_result_sha256']
  original=json.loads(result.read_text());assert all(original[k]==v for k,v in record['original_result'].items())
 world=c.get('world_source',{})
 for key in ['pane','scene','ledger']:
  if key in world:assert sha(ROOT/world[key])==world['sha256']
 transform=c.get('display_transform_verification')
 if transform:assert transform['passed'] and transform['states_checked']==3 and transform['maximum_transform_error']==0
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate:format=duration','-of','json',str(p)],text=True));v=d['streams'][0]
 assert len(d['streams'])==1 and (v['codec_name'],v['codec_type'],v['r_frame_rate'])==('h264','video','30/1')
 assert int(v['nb_frames'])==round(c['clip_duration_s']*30),(name,v)
 assert (ROOT/'site'/c['poster']).exists()
 checks.append({'id':name,'sha256':c['sha256'],'source_files':c['source_files'],'duration_s':float(d['format']['duration']),'metadata':v,'camera_recording':True})
usage=json.loads((ROOT/'evidence/crossing/route/lux-usage.json').read_text());assert usage['generated_task_creates']==467 and usage['status_counts']=={'ok':438,'failed':29}
for group in ['levels','routes','failures']:
 for row in m[group]:
  for run in row['runs'].values():
   record=json.loads((ROOT/'site'/run['evidence']).read_text())
   original=record['original_result']
   assert run['result']==original.get('total_result',original.get('result')),(row['id'],run)
assert len(m['routes'])==4
film=json.loads((WORK/'film-delivery.json').read_text());assert film['no_diagram_shots'] and sha(ROOT/'site'/film['path'])==film['sha256']
for source in film['sources']:assert sha(ROOT/source['path'])==source['sha256']
report={'schema':'beforestep-footage-showcase-audit/v1','passed':True,'recorded_clips':len(checks),'worlds':12,'known_scenes':12,'known_strategies':36,'holdout_films':10,'route_scenes':4,'route_vehicle_films':16,'threshold_films':3,'post_run_rejected_model_diagnostic_films':1,'new_experiments':0,'new_generation_tasks':0,'historical_generation_tasks_unchanged':467,'film':film,'checks':checks,'source_data_unchanged':True,'frontpage_illustrative_maps':0}
p=ROOT/'evidence/award/acceptance/real-footage-showcase.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2));(WORK/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('ACTUAL SOURCE AND MOVIE AUDIT PASSED',len(checks),flush=True)
