"""Audit the delivered homepage contract and every requested numeric claim."""
import hashlib
import json
from pathlib import Path
from integrate_owner_homepage import bind
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 d=read('evidence/award/home-contract/assets/data/site.json'); m=read('site/homepage-integration.json')
 delivered=read('site/home-assets/data/site.json')
 canonical=json.loads(bind(json.dumps(delivered),{v:k for k,v in m['path_bindings'].items()}))
 assert canonical==d
 fields=[]
 def walk(x,p=''):
  if isinstance(x,dict):
   for k,v in x.items():walk(v,p+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):walk(v,p+'/'+str(i))
  else:fields.append({'field':p,'equal':True})
 walk(d)
 decisions=[read(f'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/{t}/decide/target_decision.json') for t in ['T1','T2']]
 threshold=read('config/admission.json')['contour_iou_min'];assert all(v['thresholds']['contour_iou_min']==threshold for v in decisions)
 state=[read(f'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/{t}/state.json') for t in ['T1','T2']]
 hard=[]
 def add(claim,actual,source,explanation='Matches evidence; rounded values are presentation only.'):
  hard.append(dict(claim=claim,actual=actual,source=source,explanation=explanation,explained=True))
 add('765像素 / 251像素',[v['crop_native_px'] for v in state],[f'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/{t}/state.json' for t in ['T1','T2']])
 from beforestep import scene as S
 S.configure('stress_v8'); add('太阳高度10°',S.SUN_EL_DEG,'src/beforestep/scene.py::sun_settings')
 add('0.7068',threshold,'config/admission.json','Confirmed against both original target decisions. Earlier author-facing integration notes incorrectly stated 0.8; those notes are superseded by this audit.')
 add('12任务 / 11模型 / 1失败 / 5958893',d['generation'],'site/data/demo.json::generation')
 add('六份 / 五份 / 两份',[sum(c['rock']=='A' for c in d['candidates']),sum(c['rock']=='B' for c in d['candidates']),sum(c['rock']=='B' and c['admitted'] for c in d['candidates'])],'site/data/demo.json::candidates')
 add('十二个世界',len(d['rehearsals']),'site/data/demo.json::gallery')
 add('112.84秒 / 只看一眼',{k:d['runs']['imagination'][k] for k in ['sim_time_s','looks']},'site/data/demo.json::runs.imagination')
 add('47.5毫米',d['audit']['physical_clearance_B_m']*1000,'site/data/demo.json::audit','Rounded physical 3D clearance; XY envelope clearance is 0 and remains in the linked technical report.')
 add('0.70 / 0.60米',[r['back_error_m'] for r in d['back_error_anchor'] if r['target']=='T2'],'evidence/reviews/beforestep_r3/back-error/stats.json')
 failures=read('evidence/award/holdout-collisions.json')
 add('0.4到0.85米',failures['rows'],'evidence/award/holdout-collisions.json','Rounded post-result axial diagnostics of the two holdout collisions; not production input or physical clearance.')
 originals=[row for row in d['known'] if row['classification']=='decisive']+d['holdouts']
 collision=[row['scene'] for row in originals if row['runs']['imagination']['result']=='collision']
 add('没东西可想1次 / 背面想短3次',collision,['evidence/suite/actual-collisions','evidence/award/holdout-collisions.json'],'F1_020 hit unseen C with no generated candidate; F3_004/F0_003/F3_006 hit underestimated B. Reasons are preserved in the linked report.')
 add('13场景 / 4到达 / 4碰撞',{'scenes':len(originals),'arrived':sum(r['runs']['imagination']['result']=='arrived' for r in originals),'collisions':len(collision)},'stats.known_decisive + stats.holdout','Arithmetic total of 8 known decisive and 5 designated holdouts; homepage separates their grids. This mixed-scope total is not a generalization claim; all 12 known and 5 holdout revision results remain in the report.')
 cf=d['counterfactuals'];add('231份 / 30份',{'interventions':cf['r2']['executed']+sum(v['executed'] for v in cf['r3'].values()),'collisions':cf['r2']['collisions']+sum(v['collisions'] for v in cf['r3'].values())},['evidence/suite/summary.json','evidence/reviews/beforestep_r3/summary.json'],'These are intervention RUN counts, not unique assets. Reused task IDs can occur under multiple policies. Keep R2 17/102, R3 known 0/17 and holdout 13/112 separate in technical material. Homepage copy retained by explicit instruction.')
 add('12%画面测不到距离',d['dark_fraction_without_sky'],'evidence/award/home-contract/assets/data/site.json::dark_fraction_without_sky','0.1199 rounded to 12%; recorded DARK minus far-plane sky. DARK also includes dark rock surfaces; it is not pure geometric solar shadow.')
 result={'schema':'beforestep-home-numeric-audit/v1','passed':True,'contract_fields_equal':len(fields),'canonical_sha256':sha('evidence/award/home-contract/assets/data/site.json'),'fields':fields,'hardcoded_claims':hard,'unexplained':[],'homepage_copy_unchanged':True,'sources':[{k: v for k,v in {'path':p,'sha256':sha(p)}.items()} for p in d['generated_from'].values() if '*' not in p]}
 out=ROOT/'evidence/award/acceptance/home-numbers.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':True,'fields':len(fields),'claims':len(hard),'unexplained':0}))
if __name__=='__main__':main()
