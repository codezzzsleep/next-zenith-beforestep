import sys,json,collections,shutil,datetime
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[2]),str(Path(__file__).resolve().parents[2]/'src')]
from common import *
def read(path):return json.loads((ROOT/path).read_text())
def fact(value,path,pointer,expected=None):
 return {'value':value,'source':path,'source_sha256':sha(ROOT/path),'json_pointer':pointer,'status':'mismatch' if expected is not None and value!=expected else 'verified',**({'story_expected':expected} if expected is not None else {})}
suitepath='evidence/suite/summary.json';suite=read(suitepath);r3path='evidence/reviews/beforestep_r3/summary.json';r3=read(r3path)
facts={'schema':'beforestep-final-v6-facts/v1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_policy':'All numeric facts are read or calculated from evidence; expected narrative values never replace observations','r1':{},'decisive_eight':{},'back_error':{},'original_collisions':{},'post_result_v3':{},'legs':{},'lux':{},'same_route':{}}
for p,expected in [('optimistic',80.87),('conservative',142.2),('imagination',112.84)]:
 run=suite['scenes'][0]['runs'][p]['run'];src=run+'/summary.json';s=read(src)
 facts['r1'][p]={k:fact(s[k],src,'/'+k,expected if k=='sim_time_s' else None) for k in ['result','sim_time_s','execution_elapsed_s','looks']}
decisive=[s for s in suite['scenes'] if s['classification']=='decisive'];facts['decisive_eight']['count']=fact(len(decisive),suitepath,'/scenes filtered classification=decisive',8)
expected={'optimistic':{'arrived':0,'collision':8},'conservative':{'arrived':0,'safe_stop':8},'imagination':{'arrived':3,'safe_stop':3,'collision':2},'see_dark':{'arrived':5},'truth':{'arrived':8}}
for policy in ['optimistic','conservative','imagination','see_dark','truth']:
 count=collections.Counter(s['runs'][policy]['summary']['result'] for s in decisive)
 results={k:count[k] for k in ['arrived','collision','stuck','stopped_short']};results['safe_stop']=count['stuck']+count['stopped_short']
 facts['decisive_eight'][policy]={'counts':{k:fact(v,suitepath,f'/scenes[classification=decisive]/runs/{policy}/summary/result',expected.get(policy,{}).get(k)) for k,v in results.items()},'scenes':[{'scene':s['scene'],'run':s['runs'][policy]['run'],'summary':s['runs'][policy]['summary'],'source':suitepath} for s in decisive]}
p='evidence/reviews/beforestep_r3/back-error/stats.json';s=read(p)
facts['back_error']={k:fact(s[k],p,'/'+k,e) for k,e in [('candidate_count',64),('shorter_than_five_cm',23),('threshold_m',-.05)]}
collisions=[]
for scene in suite['scenes']:
 r=scene['runs']['imagination']
 if r['summary']['result']=='collision':collisions.append({'scene':scene['scene'],'summary':r['summary'],'source':r['run']+'/summary.json'})
for scene in r3['holdouts']:
 r=scene['runs'].get('imagination',{})
 if r.get('summary',{}).get('result')=='collision':collisions.append({'scene':scene['scene'],'summary':r['summary'],'source':r['run']+'/summary.json'})
facts['original_collisions']={'count':fact(len(collisions),r3path,'/holdouts/runs/imagination + evidence/suite/summary.json',4),'rows':collisions}
for k,e in [('completed',17),('arrived',3),('safe_stop',14),('collisions',0)]:facts['post_result_v3'][k]=fact(r3['all_run_stats'][k],r3path,'/all_run_stats/'+k,e)
facts['post_result_v3']['scope']='赛后修订：已知12场+留出5场；不能当成独立样本外证据'
p='evidence/crossing/calibration/gate.json';g=read(p)
for k,e in [('wheel_trials_at_band_heights',90),('wheel_passes_at_band_heights',0),('band_gait_trials',24),('band_gait_clean_trials',24)]:facts['legs'][k]=fact(g[k],p,'/'+k,e)
p='evidence/crossing/route/lux-usage.json';u=read(p)
for k,value,e in [('created',u['generated_task_creates'],467),('glb',u['status_counts']['ok'],438),('server_failed',u['status_counts']['failed'],29)]:facts['lux'][k]=fact(value,p,'/generated_task_creates' if k=='created' else '/status_counts/'+('ok' if k=='glb' else 'failed'),e)
facts['lux']['baseline_before_addendum4']=True
client={}
for f in (ROOT/'outputs/generation/tasks').glob('*.json'):
 d=json.loads(f.read_text())
 if d.get('task_id'):client[d['task_id']]={'status':d['status'],'source':str(f.relative_to(ROOT)),'source_sha256':sha(f)}
facts['lux']['live_ledger_counts']={'created':len(client),'statuses':dict(collections.Counter(x['status'] for x in client.values())),'task_ids':client,'scope':'Current client ledger. New §1 tasks change cumulative counts; baseline467/438/29 remains historical.'}
budget_path='outputs/generation/crossing-budget.json';budget=read(budget_path)
new_tasks=[r for r in budget['tasks'] if r['scene'].startswith('route/suite_r2_v4_F3_002_gate/') and r.get('task_id')]
facts['lux']['new_f3_002']={'created':fact(len(new_tasks),budget_path,'/tasks filtered route/suite_r2_v4_F3_002_gate with accepted task_id'),'statuses':{k:fact(v,budget_path,'/tasks filtered F3_002/status') for k,v in collections.Counter(r['status'] for r in new_tasks).items()},'task_ids':[r['task_id'] for r in new_tasks],'scope':'Accepted tasks for this appended single scene; D reuses matching A uploads.'}
names=['stress_v8_gate','suite_r2_v4_F1_003_gate','suite_r2_v4_F2_001_gate','suite_r2_v4_F2_007_gate','suite_r2_v4_F3_002_gate']
for name in names:
 rows=[]
 for v in ['A','B','C','D']:
  p=f'outputs/crossing/route/{name}/{v}/result.json'
  if (ROOT/p).exists():
   r=read(p);rows.append({'vehicle':v,**{k:fact(r[k],p,'/'+k) for k in ['first_segment_result','second_segment_result','total_result','sim_seconds','looks','reason','legs_used']}})
  else:rows.append({'vehicle':v,'status':'pending','source':p})
 facts['same_route'][name]={'rows':rows,'complete':all('total_result' in r for r in rows),'scope':'单场演示，不是统计证据；F3_002是在前四场之后追加'}
facts['same_route']['D_arrived_completed_scenes']={'value':sum(facts['same_route'][name]['rows'][3].get('total_result',{}).get('value')=='arrived' for name in names),'source_paths':[f'outputs/crossing/route/{name}/D/result.json' for name in names if (ROOT/f'outputs/crossing/route/{name}/D/result.json').exists()],'calculation':'Count D total_result=arrived, retain pending scene separately'}
facts['same_route']['completed_scenes']={'value':sum(facts['same_route'][name]['complete'] for name in names),'source_paths':[f'outputs/crossing/route/{name}/{v}/result.json' for name in names for v in ['A','B','C','D'] if (ROOT/f'outputs/crossing/route/{name}/{v}/result.json').exists()],'calculation':'All four vehicles have terminal result files'}
facts['back_error']['r1_reveal_examples']=[{k:fact(r[k],'evidence/reviews/beforestep_r3/back-error/stats.json',f'/rows/{i}/{k}') for k in ['task_id','back_error_m']} for i,r in enumerate(read('evidence/reviews/beforestep_r3/back-error/stats.json')['rows']) if r['scene']=='stress_v8' and r['target']=='T2']
cap_path='evidence/crossing/calibration/capability-v72.json';cap=read(cap_path);facts['legs']['true_rocks']=fact(len(cap['clean_support_compliant_rocks']),cap_path,'/clean_support_compliant_rocks length',3)
def mismatches(o):
 if isinstance(o,dict):return ([o] if o.get('status')=='mismatch' else [])+sum((mismatches(v) for v in o.values()),[])
 if isinstance(o,list):return sum((mismatches(v) for v in o),[])
 return []
facts['mismatches']=mismatches(facts);save(OUT/'facts.json',facts)
status('D facts数字核对',OUT/'facts.json',f'已核现有证据；mismatch={len(facts["mismatches"])}；F3_002未终态项标pending')
files=[('r1-three-trajectories','site/media/r1-routes.png'),('r1-self-check','site/media/r1-self-check.png'),('back-error-distribution','evidence/reviews/beforestep_r3/back-error/figure.png'),('six-version-assets','site/media/award/asset-iterations.png'),('sill-inputs-rounds-1-2','evidence/crossing/route/report-assets/low-inputs-1.png'),('sill-inputs-rounds-3-4','evidence/crossing/route/report-assets/low-inputs-2.png'),('sill-inputs-rounds-5-6','evidence/crossing/route/report-assets/low-inputs-3.png'),('high-two-looks','evidence/crossing/route/report-assets/high-two-looks.png'),('r1-first-eye','site/media/r1-camera.jpg')]
pending=[]
for name in names:
 for vehicle in ['A','B','C','D']:
  source=f'outputs/crossing/route/{name}/{vehicle}/segment1/map_final.png'
  if (ROOT/source).exists() and (ROOT/f'outputs/crossing/route/{name}/{vehicle}/result.json').exists():
   files.append((f'{name}-{vehicle}-original-map',source))
  else:pending.append(f'{name}/{vehicle}: 原第一段俯视地图待正式终态')
directory=OUT/'figures';directory.mkdir(exist_ok=True);rows=json.loads((directory/'index.json').read_text()).get('rows',[]) if (directory/'index.json').exists() else []
for label,src in files:
 source=ROOT/src;dest=directory/(label+source.suffix);shutil.copyfile(source,dest);assert sha(source)==sha(dest)
 row={'id':label,'source':src,'path':str(dest),'sha256':sha(dest),'copied_original_bytes':True}
 if label.endswith('-original-map'):row['scope']='原第一段俯视地图与轨迹；不是完整两段叠合轨迹，未重画'
 rows=[r for r in rows if r['id']!=label];rows.append(row)
save(directory/'index.json',{'status':'original_figures_complete' if not pending else 'terminal_figures_pending','rows':rows,'pending':pending,'route_map_scope':'All same-route maps are original first-segment figures. Second-segment motion remains in the saved trajectories and videos.'})
status('D 原图复制',directory/'index.json',f'通过：{len(rows)}张逐SHA一致；待终态原图{len(pending)}张；同路图明确第一段范围')
print('facts mismatches',len(facts['mismatches']),'figures',len(rows),flush=True)
