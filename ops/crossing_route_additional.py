"""Predeclare up to three existing successful scenes, then run after first D."""
import argparse,concurrent.futures,fcntl,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import build,select,ROUTE,EVIDENCE
from ops.crossing_route_checks import run_one,aggregate

PLAN=EVIDENCE/'additional-scenes.json'
LIVE=ROOT.parent/'.memory/live'
CUTOFF=datetime(2026,11,14,12,tzinfo=timezone.utc)  # Beijing 20:00

def commit_scene(scene):
    with (LIVE/'route-publication/publication.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        paths=[str(PLAN.relative_to(ROOT)),f'evidence/crossing/route/scene-{scene["name"]}.json']
        if (EVIDENCE/f'precheck-{scene["name"]}.json').exists():paths.append(f'evidence/crossing/route/precheck-{scene["name"]}.json')
        # OBJ/collision provenance and the exact scene payload are publicly retained.
        files=[p for p in (ROUTE/scene['name']/'scene-attempts'/scene['attempt']).rglob('*') if p.is_file()]
        archive=EVIDENCE/'additional-scene-definitions'/scene['name']/scene['attempt'];archive.mkdir(parents=True,exist_ok=True)
        import shutil
        base=ROUTE/scene['name']/'scene-attempts'/scene['attempt']
        for source in files:
            target=archive/source.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        paths.append(str(archive.relative_to(ROOT)))
        subprocess.run(['git','add',*paths],cwd=ROOT,check=True)
        if subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).strip():
            subprocess.run(['git','commit','-m',f'Predeclare appended gate in {scene["base_scene"]} before its runs'],cwd=ROOT,check=True)
        subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
        local=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        assert local==remote
        return local

def prepare():
    if PLAN.exists():return json.loads(PLAN.read_text())
    old=json.loads((ROOT/'evidence/suite/summary.json').read_text())
    candidates=[]
    for row in old['scenes']:
        original=row['runs'].get('imagination',{})
        if original.get('summary',{}).get('result')!='arrived' or row['scene']=='stress_v8':continue
        run=ROOT/original['run'];admissions=[]
        for path in run.glob('looks/look*/T*/decide/target_decision.json'):
            data=json.loads(path.read_text());admissions.extend(c for c in data['candidates'] if c['admitted'])
        if admissions:candidates.append({'base_scene':row['scene'],'original_run':original['run'],'original_result':'arrived','original_admitted':len(admissions),'source_summary':'evidence/suite/summary.json'})
    # R3 holdout arrivals are already R2 scene configurations; include their source.
    r3=json.loads((ROOT/'evidence/reviews/beforestep_r3/summary.json').read_text())
    existing={x['base_scene'] for x in candidates}
    for row in r3['holdouts']:
        original=row['runs'].get('imagination',{})
        if row['scene'] in existing or original.get('summary',{}).get('result')!='arrived':continue
        paths=list((ROOT/'outputs/r3/v3/holdouts'/row['scene']).rglob('target_decision.json'))
        count=sum(sum(c['admitted'] for c in json.loads(p.read_text())['candidates']) for p in paths)
        if count:candidates.append({'base_scene':row['scene'],'original_result':'arrived','original_admitted':count,'source_summary':'evidence/reviews/beforestep_r3/summary.json'})
    candidates.sort(key=lambda row:row['base_scene'])
    plan={'schema':'beforestep-route-additional-scenes/v1','authority':'docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM3.md §1',
        'candidate_order':candidates,'scenes':[],'start_cutoff_utc':CUTOFF.isoformat(),'maximum_scenes':3,'first_D_result_not_selection_criterion':True}
    for candidate in candidates[:3]:
        scene=build(9.,22001,candidate['base_scene']);select(scene)
        plan['scenes'].append({**candidate,'scene':scene['name'],'near_x_m':9.,'threshold_seed':22001,'scene_definition':f'evidence/crossing/route/scene-{scene["name"]}.json','status':'未开始','placement_attempts':[]})
    write(PLAN,plan)
    for row in plan['scenes']:row['predeclared_commit']=commit_scene(json.loads((EVIDENCE/f'scene-{row["scene"]}.json').read_text()))
    write(PLAN,plan)
    with (ROOT.parent/'MEMORY.md').open('a') as stream:stream.write('\n追加场景名单/初始门位置已运行前提交：'+', '.join(x['scene']+' x9.0/22001' for x in plan['scenes'])+'；源准入和原方法到达证据见evidence/crossing/route/additional-scenes.json，D终态即启动，开工北京11/14 20:00截止。\n')
    return plan

def execute(plan):
    assert (ROUTE/'stress_v8_gate/D/result.json').exists(),'Wait for first D terminal'
    progress=ROOT/'outputs/crossing/route/progress.json';state=json.loads(progress.read_text())
    state['steps']['extra_scenes'].update(status='运行中',pid=os.getpid(),output=str(PLAN.relative_to(ROOT)));write(progress,state)
    for row in plan['scenes']:
        if row['status']=='终态':continue
        if row['status']=='未开始' and datetime.now(timezone.utc)>=CUTOFF:
            row.update(status='终态',result='未开工：已过截止');write(PLAN,plan);continue
        row.update(status='运行中',started_at=datetime.now(timezone.utc).isoformat(),pid=os.getpid());write(PLAN,plan)
        passed=False
        for near in [9.,9.25,9.5]:
            for seed in [22001,22003,22004,22005]:
                scene=build(near,seed,row['base_scene']);select(scene)
                row.update(near_x_m=near,threshold_seed=seed);write(PLAN,plan);commit_scene(scene)
                run_one(scene,'contour');report=aggregate(scene)
                if not report['checks']['contour'].get('passed'):continue
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    jobs=[pool.submit(run_one,scene,'wheel',stance,position) for stance in ['fixed','high'] for position in ['center','left','right']]
                    for future in concurrent.futures.as_completed(jobs):future.result()
                report=aggregate(scene)
                if any(not report['checks'][f'wheel-{s}-{p}'].get('passed') for s in ['fixed','high'] for p in ['center','left','right']):continue
                run_one(scene,'leg');run_one(scene,'detour');report=aggregate(scene)
                row['placement_attempts'].append({'near_x_m':near,'seed':seed,'precheck':str((EVIDENCE/f'precheck-{scene["name"]}.json').relative_to(ROOT)),'all_four_passed':report['all_four_passed']});write(PLAN,plan)
                if report['all_four_passed']:passed=True;break
                # A detour obstruction is addressed by moving the gate back,
                # rather than changing the original high rocks or method.
                if not report['checks']['detour'].get('passed'):break
            if passed:break
        if not passed:
            row.update(status='终态',result='四项预检查未全通过，未跑正式车');write(PLAN,plan);continue
        row['prechecks_commit']=commit_scene(scene);write(PLAN,plan)
        for vehicle in ['C','B','A','D']:
            command=[sys.executable,'ops/crossing_route_run.py','--scene',scene['name'],'--vehicle',vehicle]
            if vehicle=='A':
                probe=ROUTE/scene['name']/'input-probe/segment1'
                identity=EVIDENCE/f'input-reuse-{scene["name"]}.json'
                if not identity.exists():
                    probe_command=[sys.executable,'ops/crossing_route_run.py','--scene',scene['name'],'--vehicle','A','--probe']
                    if row.get('original_run'):probe_command+=['--comparison-source',row['original_run']]
                    subprocess.run(probe_command,cwd=ROOT,check=True)
                command+=['--reuse',str(probe.relative_to(ROOT))]
            elif vehicle=='D':command+=['--reuse',str((ROUTE/scene['name']/'A/segment1').relative_to(ROOT))]
            subprocess.run(command,cwd=ROOT,check=True)
        results=[json.loads((ROUTE/scene['name']/v/'result.json').read_text()) for v in ['A','B','C','D']]
        output=EVIDENCE/f'summary-{scene["name"]}.json';write(output,{'scene':scene['name'],'all_terminal':True,'rows':results})
        row.update(status='终态',result=str(output.relative_to(ROOT)));write(PLAN,plan)
        for script in ['crossing_route_summary.py','crossing_route_text.py']:
            subprocess.run([sys.executable,'ops/'+script],cwd=ROOT,check=True)
        subprocess.run([sys.executable,'ops/crossing_route_report_assets.py','--usage-only'],cwd=ROOT,check=True)
        subprocess.run([sys.executable,'ops/crossing_route_report.py'],cwd=ROOT,check=True)
        subprocess.run([sys.executable,'ops/crossing_route_publish.py','--stage',scene['name']+'-terminal','--message','Publish additional route outcomes from saved evidence'],cwd=ROOT,check=True)
    state=json.loads(progress.read_text());state['steps']['extra_scenes'].update(status='终态',result=str(PLAN.relative_to(ROOT)));write(progress,state)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan-only',action='store_true');args=parser.parse_args()
    LIVE.mkdir(parents=True,exist_ok=True)
    with (LIVE/'additional-scenes.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        plan=prepare()
        if not args.plan_only:execute(plan)
