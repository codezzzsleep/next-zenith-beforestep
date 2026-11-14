"""Check terminal handoff against raw results, uploaded bytes and task ledgers."""
import collections,json,subprocess,datetime
from pathlib import Path
from common import OUT,ROOT,save,sha,status

NAME='suite_r2_v4_F3_002_gate';base=ROOT/'outputs/crossing/route'/NAME
results={v:json.loads((base/v/'result.json').read_text()) for v in ['A','B','C','D']}
summary_path=ROOT/f'evidence/crossing/route/summary-{NAME}.json'
summary=json.loads(summary_path.read_text());assert summary['all_terminal']
assert summary['rows']==[results[v] for v in ['A','B','C','D']]
uploaded=[]
for a in sorted((base/'A/segment1/looks').glob('look*/T*/**/lux_request.json')):
 d=base/'D/segment1'/a.relative_to(base/'A/segment1')
 ar=json.loads(a.read_text());dr=json.loads(d.read_text());am={x['id']:x for x in ar['items']};dm={x['id']:x for x in dr['items']};assert am.keys()==dm.keys()
 for sample,item in am.items():
  ap=item.get('paths') or [item['path']];dp=dm[sample].get('paths') or [dm[sample]['path']]
  ah=[sha(ROOT/p) for p in ap];dh=[sha(ROOT/p) for p in dp];assert ah==dh
  parts=a.relative_to(base/'A/segment1/looks').parts
  uploaded.append({'look':parts[0],'target':parts[1],'batch':str(a.parent.relative_to(base/'A/segment1/looks')),'sample':sample,'sha256':ah,'A_request':str(a.relative_to(ROOT)),'D_request':str(d.relative_to(ROOT))})
assert sum(x['look']=='look1' for x in uploaded)==12
task_reuse=[]
for a in sorted((base/'A/segment1/looks').glob('look*/T*/**/lux_result.json')):
 d=base/'D/segment1'/a.relative_to(base/'A/segment1')
 at={x['id']:x for x in json.loads(a.read_text())['tasks']};dt={x['id']:x for x in json.loads(d.read_text())['tasks']}
 assert at.keys()==dt.keys()
 for sample,x in at.items():
  y=dt[sample];assert x['task_id']==y['task_id'] and x['status']==y['status']
  if x['status']=='ok':assert x['glb_sha256']==y['glb_sha256']==sha(ROOT/y['glb'])
  parts=a.relative_to(base/'A/segment1/looks').parts
  task_reuse.append({'look':parts[0],'target':parts[1],'batch':str(a.parent.relative_to(base/'A/segment1/looks')),'sample':sample,'task_id':x['task_id'],'status':x['status'],'same_A_D_task':True})
budget_path=ROOT/'outputs/generation/crossing-budget.json';budget=json.loads(budget_path.read_text());tasks=[x for x in budget['tasks'] if x['scene'].startswith('route/'+NAME+'/') and x.get('task_id')]
assert all(x['status'] in ('ok','failed') for x in tasks)
assert len({x['task_id'] for x in tasks})==len(tasks)
for x in tasks:
 c=json.loads((ROOT/x['client_ledger']).read_text());assert c['task_id']==x['task_id'] and c['status']==x['status']
facts=json.loads((OUT/'facts.json').read_text());assert not facts['mismatches'];assert facts['same_route'][NAME]['complete'];assert facts['same_route']['completed_scenes']['value']==5
for row in facts['same_route'][NAME]['rows']:
 v=row['vehicle']
 for key in ['first_segment_result','second_segment_result','total_result','sim_seconds','looks','reason','legs_used']:
  assert row[key]['value']==results[v][key]
figures=json.loads((OUT/'figures/index.json').read_text());assert not figures['pending']
for x in figures['rows']:assert sha(Path(x['path']))==x['sha256']==sha(ROOT/x['source'])
old=json.loads(subprocess.check_output(['git','show','3ba77405:evidence/crossing/route/additional-scenes.json'],cwd=ROOT));new=json.loads((ROOT/'evidence/crossing/route/additional-scenes.json').read_text());lookup={r['scene']:r for r in new['scenes']}
assert all(lookup[x['scene']]==x for x in old['scenes'] if x['scene']!=NAME)
record={'status':'passed','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'terminal_rows':{v:{k:r[k] for k in ['total_result','sim_seconds','looks']} for v,r in results.items()},'summary_sha256':sha(summary_path),'A_D_uploads':uploaded,'A_D_reused_tasks':task_reuse,'new_accepted_tasks':len(tasks),'new_task_statuses':dict(collections.Counter(x['status'] for x in tasks)),'budget_client_ledgers_agree':True,'facts_source_results_agree':True,'original_figures_byte_identical':len(figures['rows']),'prior_additional_rows_unchanged':True,'frozen_evidence_check':str(OUT/'frozen-resume-verification.json')}
save(OUT/'gate-delivery-verification.json',record);status('A/D 终态交付核验',OUT/'gate-delivery-verification.json',f'通过：原四行/事实数字/全部原图SHA/{len(uploaded)}份A-D上传字节与任务复用/账本终态一致；原场景行不变')
print(json.dumps({k:record[k] for k in ['status','terminal_rows','new_accepted_tasks','new_task_statuses','original_figures_byte_identical']},ensure_ascii=False))
