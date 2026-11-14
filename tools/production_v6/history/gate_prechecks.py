import sys,os,json,subprocess,concurrent.futures,shutil,datetime
sys.path[:0]=['/root/3d/next-zenith-beforestep','/root/3d/next-zenith-beforestep/src']
from common import *
from experimental.crossing.route.world import build,select,ROUTE,EVIDENCE
from ops.crossing_route_additional import run_one,aggregate
BASE='suite_r2_v4_F3_002';NAME=BASE+'_gate';PLAN=EVIDENCE/'additional-scenes.json'
def commit(paths,message):
 subprocess.run(['git','add','--',*[str(p.relative_to(ROOT)) for p in paths]],cwd=ROOT,check=True)
 subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True)
 return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def archive(scene):
 source=ROUTE/NAME/'scene-attempts'/scene['attempt'];dest=EVIDENCE/'additional-scene-definitions'/NAME/scene['attempt']
 if not dest.exists():shutil.copytree(source,dest)
 return dest
plan=json.loads(PLAN.read_text());original_rows=json.loads(json.dumps(plan['scenes']))
row=next((r for r in plan['scenes'] if r['scene']==NAME),None)
if row is None:
 row={'base_scene':BASE,'scene':NAME,'original_run':f'outputs/suite/real/{BASE}/imagination','original_result':'arrived','original_admitted':5,'source_summary':'evidence/suite/summary.json','near_x_m':9.,'threshold_seed':22001,'scene_definition':f'evidence/crossing/route/scene-{NAME}.json','status':'未开始','placement_attempts':[],
 'selection_rule':{'criteria':['决定性场景','R2原想象车到达','尚未做过同路实验'],'selected':BASE,'disclosure':'本场是在前四个同路场景出结果之后追加的，目的是检验决定性场景；单场演示，不是统计证据','prior_four_scenes_retained':True,'D_result_not_selection_criterion':True},'authority':'docs/reviews/SPEC_BEFORESTEP_ADDENDUM4.md §1','start_cutoff_utc':'2026-11-14T18:00:00+00:00','candidate_near_x_m':[9.,9.25,9.5]}
 plan['scenes'].append(row);plan['selection_rule_addendum4']=row['selection_rule'];save(PLAN,plan)
 scene=build(9.,22001,BASE);select(scene);arc=archive(scene)
 head=commit([PLAN,EVIDENCE/f'scene-{NAME}.json',arc,ROOT/'docs/reviews/SPEC_BEFORESTEP_ADDENDUM4.md',ROOT/'docs/reviews/STORY_V3.md',ROOT/'docs/story-v3.md'],'Predeclare F3_002 gate under addendum 4 and preserve story v3')
 row['predeclared_commit']=head;save(PLAN,plan);status('A §1.1 场景预声明',PLAN,f'通过：本地提交 {head}；未push；x9.0/22001')
save(OUT/'gate-job.json',{'status':'prechecks_running','pid':os.getpid(),'scene':NAME,'live_jobs':['zero-paid prechecks']})
passed=False
for near in [9.,9.25,9.5]:
 if any(r['near_x_m']==near and r['all_four_passed'] for r in row['placement_attempts']):passed=True;break
 scene=build(near,22001,BASE);select(scene);row.update(near_x_m=near,status='运行中');save(PLAN,plan)
 arc=archive(scene)
 # A moved gate is retained in a scoped local commit before checking it.
 if near!=9.:commit([PLAN,EVIDENCE/f'scene-{NAME}.json',arc],f'Retain zero-paid placement attempt at x{near:.2f} before checks')
 run_one(scene,'contour');aggregate(scene)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(run_one,scene,'wheel',stance,position) for stance in ['fixed','high'] for position in ['center','left','right']]
  for future in concurrent.futures.as_completed(futures):future.result();aggregate(scene)
 run_one(scene,'leg');run_one(scene,'detour');report=aggregate(scene)
 snapshot=EVIDENCE/'precheck-history'/NAME/f'{scene["attempt"]}.json';save(snapshot,report)
 row['placement_attempts'].append({'near_x_m':near,'seed':22001,'precheck':str(snapshot.relative_to(ROOT)),'all_four_passed':report['all_four_passed']});save(PLAN,plan)
 status('A 预检查 '+scene['attempt'],snapshot,'通过' if report['all_four_passed'] else '未通过：'+str([k for k,v in report['checks'].items() if not v.get('passed')]))
 if report['all_four_passed']:passed=True;break
if passed:
 row['prechecks_commit']=commit([PLAN,EVIDENCE/f'scene-{NAME}.json',EVIDENCE/f'precheck-{NAME}.json',EVIDENCE/'precheck-history'/NAME],'Retain F3_002 zero-paid gate checks before formal vehicles')
 save(PLAN,plan);save(OUT/'gate-job.json',{'status':'prechecks_passed','scene':NAME,'selected_attempt':scene['attempt'],'live_jobs':[],'next':'Read cloud remaining credits, then C/B/A/D via unchanged runner'})
else:
 row.update(status='终态',result='预检查两次整体后移后仍未全通过，未开正式车');save(PLAN,plan)
 save(OUT/'gate-job.json',{'status':'stopped_by_spec7','scene':NAME,'live_jobs':[],'reason':row['result']})
 (OUT/'gate-result.md').write_text('# F3_002_gate 结果\n\n四车均未开跑：x9.0、9.25、9.5预检查未全通过，按补充4 §7停止本场。没有生成任务，没有为D修改场景。D第一段高石与第二段门槛均未发生。故事选择版本B，现有五场中已运行四场D到达2场，本追加场未通过预检查。\n')
 status('A 指定停因',OUT/'gate-result.md','未开正式车；预检查结果完整保留')
assert all(a==b for a,b in zip(original_rows,plan['scenes'][:len(original_rows)])),'Existing rows changed'
print(json.dumps({'passed':passed,'scene':NAME},ensure_ascii=False),flush=True)
