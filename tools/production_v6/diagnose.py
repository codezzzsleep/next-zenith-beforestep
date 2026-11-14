from pathlib import Path
import sys,json
sys.path[:0]=[str(Path(__file__).resolve().parents[2]),str(Path(__file__).resolve().parents[2]/'src')]
from common import *
import numpy as np
from scipy import ndimage
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.evaluation import truth_footprints
from experimental.crossing.route.world import register
def read(p):return json.loads(p.read_text())
def examine(run,base):
 S.configure(base);truth=truth_footprints(run);looks=[]
 for look in sorted((run/'looks').glob('look*')):
  targets=[]
  for target in sorted(look.glob('T*')):
   dec=target/'decide/target_decision.json'
   if not dec.exists():continue
   state=read(target/'state.json');cells=np.load(target/'cells.npy');rocks=[key for key,mask in truth.items() if (mask&cells).any()]
   actual=np.logical_or.reduce([truth[r] for r in rocks]);yaw=state['local_frame']['yaw0'];direction=np.array([np.cos(yaw),np.sin(yaw)])
   projection=N.GX*direction[0]+N.GY*direction[1];true_end=float(projection[actual].max())
   tasks={r['id']:r for p in [target/'lux_result.json',target/'retry/lux_result.json'] if p.exists() for r in read(p)['tasks']}
   rows=[]
   for c in read(dec)['candidates']:
    if not c['admitted']:continue
    fp=dec.parent/f'footprint_{c["id"]}.npy';occ=np.load(fp);pred=float(projection[occ].max())
    # Supplemental contact-band comparison; primary error remains r3's definition.
    band=abs(N.GY-(-.365))<=.10;tb=actual&band;pb=occ&band
    rows.append({'candidate':c['id'],'task_id':tasks[c['id']]['task_id'],'back_error_m':pred-true_end,'predicted_farthest_m':pred,'truth_farthest_m':true_end,'associated_true_rocks':rocks,'contact_band_y_m':[-.465,-.265],'contact_band_back_error_m':float(N.GX[pb].max()-N.GX[tb].max()) if pb.any() and tb.any() else None,'contact_band_candidate_present':bool(pb.any()),'footprint':str(fp.relative_to(ROOT)),'sha256':sha(fp)})
   req=target/'lux_request.json';items=read(req)['items'];inputs=[{'sample':item['id'],'sha256':[sha(ROOT/p) for p in (item.get('paths') or [item['path']])]} for item in items]
   targets.append({'target':target.name,'state':str((target/'state.json').relative_to(ROOT)),'generated':len(tasks),'returned_glb':sum(r['status']=='ok' for r in tasks.values()),'admitted':len(rows),'rows':rows,'inputs':inputs,'decision':str(dec.relative_to(ROOT))})
  if targets:looks.append({'look':look.name,'targets':targets,'generated':sum(t['generated'] for t in targets),'admitted':sum(t['admitted'] for t in targets)})
 return {'run':str(run.relative_to(ROOT)),'summary':read(run/'summary.json'),'looks':looks}
out={}
for base in ['suite_r2_v4_F2_007','stress_v8']:
 paths={'A':ROOT/f'outputs/crossing/route/{base}_gate/A/segment1','D':ROOT/f'outputs/crossing/route/{base}_gate/D/segment1','original':ROOT/'evidence/reviews/beforestep_r1/lux/original_b' if base=='stress_v8' else ROOT/f'outputs/suite/real/{base}/imagination'}
 out[base]={k:examine(run,base) for k,run in paths.items()}
 for vehicle in ['A','D']:
  current=out[base][vehicle]['looks'][0];former=out[base]['original']['looks'][0];old={t['target']:t for t in former['targets']}
  out[base][vehicle]['first_inputs_equal_original']={t['target']:t['inputs']==old.get(t['target'],{}).get('inputs') for t in current['targets']}
# Exact saved occupancy is used for a read-only planner ablation, never simulation.
scene=read(ROOT/'evidence/crossing/route/scene-stress_v8_gate.json');register(scene);S.configure(scene['name'])
run=ROOT/'outputs/crossing/route/stress_v8_gate/A/segment1';events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
tests=[]
for look_num in [1,2]:
 state=np.load(run/f'decision/look{look_num}_state.npy');latest={}
 for l in range(1,look_num+1):
  for td in sorted((run/f'looks/look{l}').glob('T*')):
   p=td/'decide/footprint_union.npy'
   if not p.exists():continue
   sd=read(td/'state.json');ref=sd.get('ref',sd.get('target_ref',td.name));latest[ref]=(td,np.load(p))
 admitted_union=np.logical_or.reduce([fp for td,fp in latest.values()]);im=admitted_union.copy();fallback=np.zeros_like(im)
 for td,fp in latest.values():
  dec=read(td/'decide/target_decision.json')
  if not any(c['admitted'] for c in dec['candidates']):
   near=ndimage.binary_dilation(np.load(td/'cells.npy'),iterations=int(1.5/N.RES));fallback|=near&np.isin(state,(N.DARK,N.HIDDEN,N.UNSEEN))
 im|=fallback;start=next(e['measured_pose'][:2] for e in events if e['kind']=='look' and e['k']==look_num)
 variants={'production_with_zero_admitted_fallback':im,'admitted_candidates_only':admitted_union,'without_imagination_or_fallback':np.zeros_like(im),'true_high_rock_occupancy':np.logical_or.reduce(list(truth_footprints(run).values()))}
 tests.append({'look':look_num,'saved_state':str((run/f'decision/look{look_num}_state.npy').relative_to(ROOT)),'start':start,'goal':S.GOAL,'candidate_union_cells':int(admitted_union.sum()),'zero_admitted_fallback_cells':int(fallback.sum()),'target_unions':[str(td.relative_to(ROOT)) for td,fp in latest.values()],'planner_paths':{k:N.plan(N.occupancy(state,'imagination',fp),start,S.GOAL) is not None for k,fp in variants.items()},'margin_planner_paths':{k:N.plan(N.occupancy(state,'imagination',ndimage.binary_dilation(fp,iterations=1)),start,S.GOAL) is not None for k,fp in variants.items()}})
out['stress_v8']['read_only_planner_tests']=tests
save(OUT/'diagnosis-data.json',out)
lines=['# 同路失败只读诊断','', '口径：与 ops/r3_back_error.py 相同，5cm XY 占地，沿该眼记录的车体朝向计算候选最远缘减关联真石联合最远缘。附加接触带结果单列；不把两种口径混用。未跑物理、未调用生成、未改规则。','']
for base,data in out.items():
 lines+=['## '+base,'']
 for vehicle in ['A','D','original']:
  d=data[vehicle];lines.append(f'- {vehicle}：{d["summary"]["result"]}，{d["summary"]["looks"]} 眼；来源 `{d["run"]}/summary.json`。')
  for look in d['looks']:
   lines.append(f'  - {look["look"]}：生成 {look["generated"]}，准入 {look["admitted"]}。')
   for t in look['targets']:
    lines.append(f'    - {t["target"]}：{t["generated"]} 份 / {t["admitted"]} 准入，证据 `{t["decision"]}`。')
    for r in t['rows']:lines.append(f'      - {r["candidate"]} 任务 {r["task_id"]}：背缘误差 {r["back_error_m"]:+.6f} m；接触带存在={r["contact_band_candidate_present"]}、带内误差={r["contact_band_back_error_m"]}；`{r["footprint"]}`。')
  if vehicle!='original':lines.append(f'  - 第一眼上传图与原运行逐字节比较：{d["first_inputs_equal_original"]}；各输入 SHA 见 `diagnosis-data.json`。')
 if base=='stress_v8':
  for t in tests:lines.append(f'- {t["look"]}眼保存状态只读规划：{t["planner_paths"]}；候选联合占 {t["candidate_union_cells"]} 格；`{t["saved_state"]}`。')
lines+=['','## 结论与动作','', 'F2_007 的 A/D 第一眼各12份、3准入：前石2份、后石1份；后石候选A1背面短约0.75m，接触点y=-0.365附近候选缺失。原R2首眼后石0准入，因此再看一眼，第二眼2份准入后到达。原监视器在高石轮触时停车，A/D未发生第二段。','', 'stress_v8 首眼后石0准入，第二眼含重试12份仍0准入。冻结pipeline.py会把零准入目标周围1.5m的未知区按保守占地处理；只用已准入前石联合仍有路，加零准入后石fallback才无路。保存状态只读规划已复现两眼原停车条件。因此原因是后石没有准入候选触发保守封锁，不是已准入候选过大堵死窄道。','', '上传图字节不同本身不证明门遮挡了高石；没有能够支持移动门的因果证据。因此不调整方法参数，不为结果选门位置。F3_002 从 x9.0/22001 开始，只允许预检查不通过时按原规则整体后移。','', '数字修正：原F2_007实际2眼、sim_time_s=128.4，不能沿用未核实的1眼印象。所有逐字节上传对比与原始路径见diagnosis-data.json。']
(OUT/'diagnosis.md').write_text('\n'.join(lines)+'\n');status('A §1.0 只读诊断',OUT/'diagnosis.md','通过：数字与SHA留证，零生成、零物理、规则未改')
print(json.dumps({base:{k:{'looks':len(v['looks']),'first_admitted':v['looks'][0]['admitted']} for k,v in data.items() if k in ['A','D','original']} for base,data in out.items()},ensure_ascii=False))
