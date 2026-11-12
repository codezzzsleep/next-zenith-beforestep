"""Join every real web model to original decisions and task-matched interventions."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/web-assets/gallery'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def snapshot(source):
 source=Path(source);target=OUT/'sources'/(hashlib.sha256(str(source.relative_to(ROOT)).encode()).hexdigest()+'.json')
 if source.exists():
  raw=source.read_bytes()
  if target.exists():assert target.read_bytes()==raw
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 return target

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 models=read(ROOT/'evidence/web-assets/models.json')['models'];contexts=read(ROOT/'evidence/web-assets/registrations.json')['contexts'];by=defaultdict(list)
 for c in contexts:by[c['task_id']].append(c)
 # Historical models predate R1/R2. Preserve their original decisions as separate sources.
 historical=OUT/'historical.json'
 if not historical.exists():
  extra=[];paths=[ROOT/'experiments/polar_retry_001/admission.json']
  for tree in ['outputs/effective','outputs/decision-effect','outputs/learning-validation']:
   paths+=list((ROOT/tree).glob('**/T*/decide/target_decision.json'))
  needed={m['task_id'] for m in models if m['task_id'] not in by}
  for path in sorted(paths):
   d=read(path)
   for c in d.get('candidates',[]):
    task=int(Path(c['glb']).parent.name)
    if task not in needed:continue
    source=snapshot(path);source_rel=str(source.relative_to(ROOT))
    scene=('polar_retry_001' if 'polar_retry' in str(path) else 'blind_tail_001' if 'blind_tail' in str(path) else 'stress_v8_history')
    extra.append({'task_id':task,'sample':c['id'],'scene':scene,'target':('T2' if 'polar_retry' in str(path) else 'T1'),'look':('look2' if 'polar_retry' in str(path) else 'look1'),'run':str(path.parent),'run_id':'historical','admitted':c['admitted'],'metrics':c,'thresholds':d.get('thresholds'),'source_decision':source_rel,'source_decision_sha256':sha(source),'original_source':str(path.relative_to(ROOT)),'reason':'原历史生产自检，保留原数值与结论；不属于R1/R2/R3冻结组。'})
  write(historical,extra)
 for c in read(historical):by[c['task_id']].append(c)
 assert all(m['task_id'] in by for m in models),'Do not invent missing measurements'
 # Task catalog includes failures, unlike the model catalog.
 catalog=OUT/'tasks.json'
 if not catalog.exists():
  tasks={}
  for path in (ROOT/'outputs/generation/tasks').glob('*.json'):
   d=read(path)
   if d.get('task_id') is not None:tasks[d['task_id']]={k:d.get(k) for k in ['task_id','id','status','glb_sha256','input_sha256']}
  write(catalog,sorted(tasks.values(),key=lambda x:x['task_id']))
 cf_source=OUT/'counterfactuals.json'
 if not cf_source.exists():
  joins=[];r2=read(ROOT/'evidence/suite/summary.json');r3=read(ROOT/'evidence/reviews/beforestep_r3/summary.json')
  ledgers=[(s['counterfactuals'],'R2','evidence/suite/summary.json') for s in r2['scenes'] if s.get('counterfactuals')]
  for item in r3['new_rejected_counterfactuals']:
   ledger=snapshot(ROOT/item['ledger']);ledgers.append((read(ledger),'R3',str(ledger.relative_to(ROOT))))
  for d,scope,source in ledgers:
   for c in d.get('candidates',[]):
    key=f"look{c['look']}_{c['target']}_{c['candidate']}";run=d['runs'].get(key,{})
    if not run.get('executed') or not run.get('summary'):continue
    task=c.get('task_id') or int(Path(c['glb']).parent.name)
    assert run.get('prefix_verification',{}).get('passed')
    joins.append({'task_id':task,'scope':scope,'scene':d['scene'],'policy':d.get('policy','imagination'),'look':c['look'],'target':c['target'],'sample':c['candidate'],'result':run['summary']['result'],'collision':run['collision'],'run':run['run'],'source':source,'source_sha256':sha(ROOT/source),'verified_intervention':True})
  write(cf_source,joins)
 # The three anchor interventions are stored separately from the suite ledger.
 joins=read(cf_source)
 anchor=read(ROOT/'site/data/demo.json')
 for sample in ['A1','B1','C2']:
  model=next(c for c in anchor['candidates'] if c['target']=='T2' and c['sample_id']==sample)
  run=anchor['runs']['trust_'+sample]
  if not any(x['task_id']==model['task_id'] and x['scope']=='R1' for x in joins):
   joins.append({'task_id':model['task_id'],'scope':'R1','scene':'stress_v8','policy':'imagination','look':1,'target':'T2','sample':sample,'result':run['result'],'collision':run['collision'] is not None,'run':run['evidence'],'source':'site/data/demo.json','source_sha256':sha(ROOT/'site/data/demo.json'),'verified_intervention':True})
 write(cf_source,joins)
 cf=defaultdict(list)
 for row in read(cf_source):cf[row['task_id']].append(row)
 rows=[]
 for m in models:
  ctx=sorted(by[m['task_id']],key=lambda c:('historical'==c.get('run_id'),'/r3/' in c['run'],c['scene'],c['look']))
  assert len({c['admitted'] for c in ctx})==1
  c=ctx[0];id_=m['task_id'];rows.append({'task_id':id_,'sample':m['sample'],'scene':c['scene'],'target':c['target'],'look':c['look'],'admitted':c['admitted'],'model':m['path'],'poster':f'evidence/web-assets/gallery/posters/{id_}.jpg','input':m['web_inputs'][0],'source_sha256':m['source_sha256'],'web_sha256':m['sha256'],'bytes':m['bytes'],'contexts':ctx,'counterfactuals':cf[id_],'would_collide':any(r['collision'] for r in cf[id_]),'counterfactual_status':('collision' if any(r['collision'] for r in cf[id_]) else 'verified_no_collision' if cf[id_] else 'unverified')})
 tasks=read(catalog);stats={'real_tasks':len(tasks),'returned_models':len(rows),'admitted':sum(r['admitted'] for r in rows),'rejected':sum(not r['admitted'] for r in rows),'rejected_would_collide':sum(not r['admitted'] and r['would_collide'] for r in rows),'counterfactual_interventions':sum(len(r['counterfactuals']) for r in rows),'counterfactual_collision_interventions':sum(sum(x['collision'] for x in r['counterfactuals']) for r in rows),'decision_contexts':sum(len(r['contexts']) for r in rows)}
 write(OUT/'facts.json',{'schema':'beforestep-gallery-facts/v1','scope':'Entire 306-model web catalog, including historical experiments; admissions are unique task IDs. Intervention counts are separate.','stats':stats,'original_scope_facts':'evidence/web-assets/facts.json','sources':[{ 'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ROOT/'evidence/web-assets/models.json',ROOT/'evidence/web-assets/registrations.json',catalog,historical,cf_source]]})
 write(ROOT/'site/data/gallery.json',{'schema':'beforestep-gallery/v1','stats':stats,'models':rows,'facts':'evidence/web-assets/gallery/facts.json'})
 print(json.dumps(stats))
if __name__=='__main__':main()
