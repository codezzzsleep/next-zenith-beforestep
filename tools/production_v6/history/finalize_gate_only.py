"""Finalize existing terminal evidence; never start physics or cloud jobs."""
import json,subprocess,datetime
from pathlib import Path
from common import ROOT,OUT,save,sha,status

NAME='suite_r2_v4_F3_002_gate';base=ROOT/'outputs/crossing/route'/NAME
results=[json.loads((base/v/'result.json').read_text()) for v in ['A','B','C','D']]
evidence=ROOT/'evidence/crossing/route';output=evidence/f'summary-{NAME}.json'
deadline=datetime.datetime(2026,11,14,16,45,tzinfo=datetime.timezone.utc)
terminal_time=datetime.datetime.fromtimestamp(max((base/r['vehicle']/'result.json').stat().st_mtime for r in results),datetime.timezone.utc)
if output.exists():
 summary=json.loads(output.read_text());assert summary['all_terminal'] and summary['rows']==results,'Existing summary must agree exactly with raw outcomes'
else:
 save(output,{'scene':NAME,'all_terminal':True,'rows':results,'authority':'docs/reviews/SPEC_BEFORESTEP_ADDENDUM4.md','scope':'前四场之后追加的决定性单场演示，不是统计证据','completed_at_utc':terminal_time.isoformat(),'deadline_utc':deadline.isoformat(),'all_terminal_before_deadline':terminal_time<=deadline})
plan=evidence/'additional-scenes.json';data=json.loads(plan.read_text());row=next(r for r in data['scenes'] if r['scene']==NAME);row.update(status='终态',result=str(output.relative_to(ROOT)));save(plan,data)
labels={'arrived':'到达','stopped':'停下','stuck':'卡住','collision':'碰撞','not_run':'未发生'}
def reason(r):
 v=r['reason']
 if isinstance(v,dict) and v.get('reason')=='frozen_contact_watch_stopped_on_wheel_contact_to_high_rock':return '高石轮触触发原监视器，机身触石0'
 return {'imagined_blocked':'想象中的路线被挡','no_path':'无可行路',None:'—'}.get(v,str(v)) if not isinstance(v,dict) else json.dumps(v,ensure_ascii=False)
lines=['# F3_002_gate 四车正式结果','', '| 车 | 高石段 | 门槛段 | 总结果 | 执行仿真秒 | 眼数 | 停因 |','|---|---|---|---|---:|---:|---|']
for r in results:lines.append('| '+' | '.join(str(x) for x in [r['vehicle'],labels.get(r['first_segment_result'],r['first_segment_result']),labels.get(r['second_segment_result'],r['second_segment_result']),labels.get(r['total_result'],r['total_result']),f'{r["sim_seconds"]:.2f}',r['looks'],reason(r)])+' |')
d=results[3];version='A' if d['total_result']=='arrived' else 'B'
story_line='最新第五幕按NOTE_FOR_CODEX_ACT5：真值连接预检查与正式停车分开标注；预检查不算正式D或Lux成绩。' if (ROOT.parent/'NOTE_FOR_CODEX_ACT5.md').exists() else f'故事第五幕选版本{version}。'
from collections import Counter
budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text());new_tasks=[r for r in budget['tasks'] if r['scene'].startswith('route/'+NAME+'/') and r.get('task_id')];new_counts=Counter(r['status'] for r in new_tasks)
client={}
for p in (ROOT/'outputs/generation/tasks').glob('*.json'):
 r=json.loads(p.read_text())
 if r.get('task_id'):client[r['task_id']]=r['status']
counts=Counter(client.values());baseline=json.loads((ROOT/'evidence/crossing/route/lux-usage.json').read_text())
lines+=['','D第一段高石：'+('在全部准入假设中完成预演后绕行，到达整备点。' if d['first_segment_result']=='arrived' else '未到达整备点，原停因：'+reason(d)+'。'), 'D第二段门槛：'+('按原可见几何与冻结v72逐轮跨越，结果'+labels.get(d['second_segment_result'],d['second_segment_result'])+'。' if d['second_segment'] else '未发生，未使用腿，不能宣称跨越成功。'),'',story_line,'本场是在前四个同路场景出结果之后追加的，目的是检验决定性场景；单场演示，不是统计证据。','',f'本场{len(new_tasks)}个新生成任务：{new_counts["ok"]}份GLB、{new_counts["failed"]}份服务端失败；累计{len(client)}个真实创建任务、{counts["ok"]}份GLB、{counts["failed"]}份服务端失败。历史{baseline["generated_task_creates"]}/{baseline["status_counts"]["ok"]}/{baseline["status_counts"]["failed"]}仍是补充4之前的基线。',f'四车实际终态时间（UTC）：{terminal_time.isoformat()}；00:45北京截止：'+('按时全部终态。' if terminal_time<=deadline else 'D在截止时未完成，已如实记录；保持原在跑任务至真实终态，没有强制结束。'),'','原停因、完整数值和路径：'+str(output.relative_to(ROOT))+'；各车原result.json保全。']
(OUT/'gate-result.md').write_text('\n'.join(lines)+'\n');status('A 四车终态本地归档',OUT/'gate-result.md','结果照实保留，故事版本'+version+'；未发布远端')
subprocess.run(['git','add','--',str(output.relative_to(ROOT)),str(plan.relative_to(ROOT))],cwd=ROOT,check=True)
if subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).strip():
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert set(staged)<={str(output.relative_to(ROOT)),str(plan.relative_to(ROOT))},'Unrelated staged files must not enter this commit'
 subprocess.run(['git','commit','-m','Record F3_002 appended gate outcomes without changing prior scenes'],cwd=ROOT,check=True)
save(OUT/'gate-job.json',{'status':'four_terminal_local_result_retained','scene':NAME,'live_jobs':[],'all_terminal_before_deadline':terminal_time<=deadline,'source':str(output),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
subprocess.run([__import__('sys').executable,str(OUT/'materials.py')],cwd=ROOT,check=True)
