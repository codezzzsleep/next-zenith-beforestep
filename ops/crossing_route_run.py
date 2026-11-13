"""One formal vehicle, with durable cloud waits and an unchanged first pipeline."""
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import numpy as np
import trimesh
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.generation import client as C,records as LX
from experimental.crossing.runtime import write,sha
from experimental.crossing.budget import CrossingBudget
from experimental.crossing.route.world import ROUTE,EVIDENCE,footprint
from experimental.crossing.route.execution import first_segment,leg_segment,wheel_trial,hashes,save_physical
from ops.crossing_private_checkpoint import checkpoint

def scene_for(name):return json.loads((EVIDENCE/f'scene-{name}.json').read_text())

def outcome(summary,physical,events):
    if summary['result']=='arrived':return 'arrived',None
    if summary.get('collision') or physical.get('failure',{} ) and physical['failure']['kind']=='body_collision':return 'collision',summary.get('collision') or physical['failure']
    if physical.get('max_tilt_deg',0)>60:return 'collision',{'reason':'tilt_gt_60','tilt_deg':physical['max_tilt_deg']}
    plans=[e for e in events if e['kind']=='plan']
    if plans and plans[-1]['path'] is None:return 'stopped',plans[-1].get('reason')
    return 'stuck',summary['result']

def child(scene,vehicle,reuse=None,probe=False):
    folder=ROUTE/scene['name']/('input-probe' if probe else vehicle)
    policies={'C':('conservative','lux',5),'B':('optimistic','lux',None),
              'A':('imagination','lux',2),'D':('imagination','lux',2)}
    policy,imagine,looks=policies[vehicle]
    e,first,out=first_segment(scene,folder,policy,imagine,reuse=reuse,max_looks=looks)
    if probe:raise RuntimeError('Input probe unexpectedly executed past its cloud request')
    physical=json.loads((out/'physical-summary.json').read_text())
    events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    stage1,reason=outcome(first,physical,events)
    total=stage1;second=None;handoff=None
    if stage1=='arrived':
        before=hashes(e);saved=e.save_state();model=hashlib.sha256(e._xml.encode()).hexdigest()
        stage2=folder/'segment2';stage2.mkdir(exist_ok=True)
        write(stage2/'handoff-before.json',{'hashes':before,'state':saved,'model_sha256':model})
        after=hashes(e)
        handoff={'qpos_before':before['qpos'],'qpos_after':after['qpos'],'qvel_before':before['qvel'],'qvel_after':after['qvel'],
            'equal':before==after,'same_live_mujoco_world':True,'model_sha256':model,'physical_time_s':e.data.time,
            'reset_between_segments':False,'source':str((out/'physical-state.json').relative_to(ROOT))}
        assert handoff['equal'];write(stage2/'handoff.json',handoff)
        index=int(e.spec['route_threshold_index']);rb=e.spec['route_rock_bodies']
        if vehicle!='A':
            second=leg_segment(e,scene,rb,index,stage2)
            total='arrived' if second['arrived'] else 'collision' if second['status'] in ('body_collision','unstable') else second['status']
            reason=None if second['arrived'] else second['contact'].get('failure') or second['last_phase']
        else:
            occ=N.prior_nogo().copy()
            for path in scene['mesh_paths']:occ |= footprint(trimesh.load(ROOT/path,force='mesh',process=False))
            path=N.plan(occ,scene['staging_xy'],scene['goal'])
            np.save(stage2/'truth-contour-occupancy.npy',occ)
            contour={'has_path':path is not None,'path':path,'planner':'unchanged 2-D production planner; true collision contours'}
            write(stage2/'contour.json',contour)
            trials=[]
            # Both diagnostic attempts use this same world, one after the other;
            # the second raises the legs at the measured end of the first.
            for stance in ('fixed','high'):
                trials.append(wheel_trial(e,scene,index,stage2/stance,stance,0.))
            arrived=any(t['arrived'] for t in trials)
            collision=next((t['contact']['failure'] for t in trials if t['status'] in ('body_collision','unstable')),None)
            second={'status':'arrived' if arrived else 'collision' if collision else 'stuck','arrived':arrived,
                'sim_seconds':sum(t['sim_seconds'] for t in trials),'contour':contour,'wheel_trials':trials,
                'second_trial_start':'Measured end state of first wheel-only attempt; no reset',
                'legs_used':False}
            write(stage2/'result.json',second);total=second['status'];reason=collision or ('wheel_only_both_stuck' if not arrived else None)
    result={'schema':'beforestep-crossing-route-vehicle/v1','scene':scene['name'],'vehicle':vehicle,'legs':vehicle!='A',
        'policy':policy,'imagine':imagine if policy=='imagination' else None,'first_segment':first,
        'first_segment_result':stage1,'second_segment':second,'second_segment_result':second['status'] if second else 'not_run',
        'total_result':total,'sim_seconds':first['execution_elapsed_s']+(second['sim_seconds'] if second else 0.),
        'looks':first['looks']+(1 if second and vehicle!='A' and (folder/'segment2/observation/raw.png').exists() else 0),
        'reason':reason,'legs_used':bool(vehicle!='A' and second and second.get('stages')),'handoff':handoff,
        'formal_runs':1,'high_rock_inputs_live':True,'threshold_lux_tasks':0,
        'source':str(folder.relative_to(ROOT))}
    write(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ('vehicle','first_segment_result','second_segment_result','total_result','sim_seconds','looks')},ensure_ascii=False),flush=True)

def compare_r1(probe):
    old=ROOT/'evidence/reviews/beforestep_r1/lux/original_b'
    rows=[]
    for current in sorted((probe/'segment1/looks/look1').glob('T*/lux_request.json')):
        target=current.parent.name;new=json.loads(current.read_text());original=json.loads((old/f'looks/look1/{target}/lux_request.json').read_text())
        old_items={r['id']:r for r in original['items']}
        for item in new['items']:
            former=old_items[item['id']]
            paths=item.get('paths') or [item['path']];old_paths=former.get('paths') or [former['path']]
            same=len(paths)==len(old_paths) and all(sha(ROOT/p)==sha(ROOT/q) for p,q in zip(paths,old_paths))
            rows.append({'target':target,'sample':item['id'],'equal_uploaded_bytes':same,
                'new_sha256':[sha(ROOT/p) for p in paths],'r1_sha256':[sha(ROOT/p) for p in old_paths]})
    report={'schema':'beforestep-crossing-route-r1-reuse/v1','comparisons':rows,'all_uploaded_inputs_equal':len(rows)==12 and all(r['equal_uploaded_bytes'] for r in rows),
        'r1_source':str(old.relative_to(ROOT)),'current_source':str(probe.relative_to(ROOT)),'new_lux_tasks':0}
    write(EVIDENCE/'input-reuse-stress_v8_gate.json',report)
    if report['all_uploaded_inputs_equal']:
        for current in sorted((probe/'segment1/looks/look1').glob('T*/lux_request.json')):
            original=json.loads((old/f'looks/look1/{current.parent.name}/lux_result.json').read_text())
            req=json.loads(current.read_text());items={r['id']:r for r in req['items']}
            for record in original['tasks']:
                record['reused_from']=str((old/f'looks/look1/{current.parent.name}/lux_result.json').relative_to(ROOT))
                paths=items[record['id']].get('paths') or [items[record['id']]['path']]
                record['inputs']=paths;record['input_sha256']=[sha(ROOT/p) for p in paths]
            write(current.parent/'lux_result.json',original)
    return report

def generate_request(path,scene):
    request=json.loads(path.read_text());budget=CrossingBudget();tasks=[]
    for item in request['items']:
        data=json.loads(budget.path.read_text())
        scoped=[r for r in data['tasks'] if r['scene'].startswith('route/'+scene['name']+'/')]
        name=f'crossing_route_{scene["name"]}_{path.parent.parent.name}_{path.parent.name}_{item["id"]}'
        paid={**item,'id':name}
        identity=C.request_identity(request,paid)
        known=next((r for r in data['tasks'] if r['identity']==identity),None)
        if known is None and len(scoped)>=24:raise RuntimeError('Scene reached its 24-task cap; do not create any further request')
        record=budget.submit(request,paid,scene=f'route/{scene["name"]}/{path.parent.parent.name}/{path.parent.name}',observation=str(path.parent.relative_to(ROOT)))
        with Path('/root/3d/MEMORY.md').open('a') as f:
            f.write(f'\nroute真实Lux已落账：{record.get("task_id")}，identity {record["identity"]}，scene {scene["name"]}，request {path.relative_to(ROOT)}；独立budget/client ledger权威，known/uncertain禁止重建。\n')
        checkpoint(f'route-task-{record.get("task_id")}-known')
        record=budget.poll(record,timeout=3600)
        if record['status'] not in ('ok','failed'):raise RuntimeError('Known cloud request is pending or uncertain; resume it, never submit it again')
        tasks.append({**record,'id':item['id'],'crossing_budget_sample':name})
    write(path.parent/'lux_result.json',{'schema':'beforestep-lux-result/v1','tasks':tasks})

def preserve_attempt(folder,number):
    source=folder/'segment1';dest=folder/'attempt-history'/f'{number:03d}';dest.mkdir(parents=True,exist_ok=True)
    for name in ['events.jsonl','run_identity.json','partial_traj.npz','traj.npz','physical-state.json','physical-state.npz','physical-summary.json']:
        p=source/name
        if p.exists() and not (dest/name).exists():shutil.copy2(p,dest/name)
    if (source/'full-record').exists() and not (dest/'full-record').exists():shutil.copytree(source/'full-record',dest/'full-record')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--scene',default='stress_v8_gate');ap.add_argument('--vehicle',choices=['C','B','A','D'],default='A')
    ap.add_argument('--child',action='store_true');ap.add_argument('--probe',action='store_true');ap.add_argument('--reuse');a=ap.parse_args()
    scene=scene_for(a.scene)
    check=json.loads((EVIDENCE/f'precheck-{a.scene}.json').read_text())
    assert check['all_four_passed'],'All four zero-paid prechecks must pass first'
    if a.child:
        child(scene,a.vehicle,a.reuse,a.probe);sys.exit(0)
    folder=ROUTE/a.scene/('input-probe' if a.probe else a.vehicle)
    if (folder/'result.json').exists():print('Formal terminal identity exists; skipped');sys.exit(0)
    folder.mkdir(parents=True,exist_ok=True)
    progress=ROOT/'outputs/crossing/route/progress.json';state=json.loads(progress.read_text())
    if not a.probe:
        state['steps'][a.vehicle].update(status='运行中',pid=os.getpid(),output=str(folder.relative_to(ROOT)));write(progress,state)
        selected=EVIDENCE/f'scene-{a.scene}.json';scene.update(formal_runs_started=True);write(selected,scene)
    for number in range(1,10):
        log=folder/f'attempt-{number:03d}.log'
        command=[sys.executable,str(Path(__file__)),'--scene',a.scene,'--vehicle',a.vehicle,'--child']
        if a.probe:command+=['--probe']
        if a.reuse:command+=['--reuse',a.reuse]
        with log.open('a') as stream:
            proc=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            write(folder/'live-job.json',{'pid':proc.pid,'command':command,'attempt':number,'log':str(log.relative_to(ROOT))})
            code=proc.wait()
        preserve_attempt(folder,number)
        if a.probe:
            assert code==10,'Probe must stop before creating any cloud tasks'
            report=compare_r1(folder);print(json.dumps(report,ensure_ascii=False));break
        if code==0 and (folder/'result.json').exists():
            state=json.loads(progress.read_text());state['steps'][a.vehicle].update(status='终态',result=str((folder/'result.json').relative_to(ROOT)));write(progress,state);break
        if code!=10:raise RuntimeError(f'Program interruption {code}; preserve {log}, repair before repeating')
        pending=json.loads((folder/'segment1/NEED_LUX3D.json').read_text())
        budget=CrossingBudget()
        with budget.locked() as data:
            if data.get('stop',{}).get('criterion')=='USER_REQUESTED_STOP':
                data.setdefault('stop_history',[]).append(data.pop('stop'))
            data['status']='addendum2_route_high_rocks_only'
        for req in pending['requests']:generate_request(ROOT/req,scene)
    else:raise RuntimeError('Unexpected number of pipeline cloud continuations')
