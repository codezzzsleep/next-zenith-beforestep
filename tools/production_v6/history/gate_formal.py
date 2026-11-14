"""Continue C/B/A/D via the unchanged runner; budget note authorizes paid phases."""
import sys,os,json,subprocess,datetime
sys.path[:0]=['/root/3d/next-zenith-beforestep','/root/3d/next-zenith-beforestep/src']
from common import *
NAME='suite_r2_v4_F3_002_gate';BASE=ROOT/'outputs/crossing/route'/NAME;EVIDENCE=ROOT/'evidence/crossing/route';PLAN=EVIDENCE/'additional-scenes.json'
def run(phase):
 if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,11,14,16,45,tzinfo=datetime.timezone.utc):raise RuntimeError('§1截止已到，不开新的车')
 initial=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())['created']
 if phase=='paid':
  note=ROOT.parent/'NOTE_FOR_CODEX_BUDGET.md'
  assert note.exists(),'Budget authorization note must exist'
  from experimental.crossing.budget import CrossingBudget
  with CrossingBudget().locked() as data:
   data.setdefault('authorization_history',[]).append({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authority':str(note),'authority_sha256':sha(note),'scope':'F3_002 A/D; user explicitly removes cloud balance prerequisite and allows higher local cap if needed','max_inflight':4})
  status('A/D 用户额度新授权',note,'云余额前置作废；最多4在途、任务落账与同SHA复用照旧；截止00:45北京')
 vehicles=['C','B'] if phase=='free' else ['A','D']
 if phase=='paid':assert all((BASE/v/'result.json').exists() for v in ['C','B'])
 state={'status':phase+'_formal_running','scene':NAME,'pid':os.getpid(),'live_jobs':[]};save(OUT/'gate-job.json',state)
 for vehicle in vehicles:
  if (BASE/vehicle/'result.json').exists():continue
  command=[sys.executable,'ops/crossing_route_run.py','--scene',NAME,'--vehicle',vehicle]
  if vehicle=='A':
   identity=EVIDENCE/f'input-reuse-{NAME}.json';probe=BASE/'input-probe/segment1'
   if not identity.exists():subprocess.run([sys.executable,'ops/crossing_route_run.py','--scene',NAME,'--vehicle','A','--probe','--comparison-source','outputs/suite/real/suite_r2_v4_F3_002/imagination'],cwd=ROOT,check=True)
   command+=['--reuse',str(probe.relative_to(ROOT))]
  elif vehicle=='D':command+=['--reuse',str((BASE/'A/segment1').relative_to(ROOT))]
  state.update(current_vehicle=vehicle,live_jobs=[{'vehicle':vehicle,'source':str((BASE/vehicle).relative_to(ROOT))}]);save(OUT/'gate-job.json',state)
  subprocess.run(command,cwd=ROOT,check=True)
  result=json.loads((BASE/vehicle/'result.json').read_text());status('A 正式车 '+vehicle,BASE/vehicle/'result.json',f'终态：{result["total_result"]}；{result["sim_seconds"]}仿真秒；{result["looks"]}眼；理由={result["reason"]}')
 if phase=='free':
  assert json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())['created']==initial,'C/B must create zero Lux tasks'
  state.update(status='C_B_terminal_A_D_waiting_cloud_balance',live_jobs=[]);state.pop('pid',None);save(OUT/'gate-job.json',state)
 else:
  results=[json.loads((BASE/v/'result.json').read_text()) for v in ['A','B','C','D']];output=EVIDENCE/f'summary-{NAME}.json';save(output,{'scene':NAME,'all_terminal':True,'rows':results,'authority':'docs/reviews/SPEC_BEFORESTEP_ADDENDUM4.md','scope':'前四场之后追加的决定性单场演示，不是统计证据'})
  plan=json.loads(PLAN.read_text());row=next(r for r in plan['scenes'] if r['scene']==NAME);row.update(status='终态',result=str(output.relative_to(ROOT)));save(PLAN,plan)
  lines=['# F3_002_gate 四车正式结果','', '| 车 | 第一段 | 第二段 | 总结果 | 仿真秒（执行elapsed） | 眼数 | 原停因 |','|---|---|---|---|---:|---:|---|']
  for r in results:lines.append('| '+' | '.join(str(r[k]) for k in ['vehicle','first_segment_result','second_segment_result','total_result','sim_seconds','looks','reason'])+' |')
  d=results[3];lines+=['','D第一段高石：'+('Lux3D准入假设完整预演后绕行到整备点。' if d['first_segment_result']=='arrived' else '未通过第一段；原停因：'+str(d['reason'])+'，不宣称绕过高石。'),'D第二段门槛：'+('实际RGB-D可见几何、冻结v72逐轮抬腿，'+str(d['second_segment_result'])+'。' if d['second_segment'] else '未发生，没有使用腿。'),'','本场是在前四个同路场景出结果之后追加的，目的是检验决定性场景；单场演示，不是统计证据。','故事第五幕：版本'+('A' if d['total_result']=='arrived' else 'B')+'。','',f'证据：{output.relative_to(ROOT)}；各车原件 {BASE.relative_to(ROOT)}。']
  (OUT/'gate-result.md').write_text('\n'.join(lines)+'\n');status('A §1.1 四车结果',OUT/'gate-result.md','终态结果已本地归档；不论D成败均保留；未发布远端')
  subprocess.run(['git','add','--',str(output.relative_to(ROOT)),str(PLAN.relative_to(ROOT))],cwd=ROOT,check=True);subprocess.run(['git','commit','-m','Record F3_002 appended gate outcomes without changing prior scenes'],cwd=ROOT,check=True)
  state.update(status='four_terminal_local_result_retained',live_jobs=[]);state.pop('pid',None);save(OUT/'gate-job.json',state)
 subprocess.run([sys.executable,str(OUT/'materials.py')],cwd=ROOT,check=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['free','paid'],required=True);run(p.parse_args().phase)
