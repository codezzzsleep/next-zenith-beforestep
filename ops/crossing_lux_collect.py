"""Collect five existing tasks after the documented provider rejection; never submit."""
import argparse,json,sys,os,time,concurrent.futures,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import OUT,write,sha
from experimental.crossing.budget import CrossingBudget
from experimental.crossing.scene import generate,track_geometry
from beforestep.generation import records as records
from beforestep.geometry import imagination as IM
from ops.crossing_probe import event
import trimesh


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,required=True);parser.add_argument('--revision',default='scene-dev-v3');args=parser.parse_args()
    scene=generate(args.seed,args.revision);folder=Path(scene['truth_mesh']).parents[1];obs=folder/'observation'
    assert (ROOT/'evidence/crossing/development-blindness.json').exists()
    blind=json.loads((ROOT/'evidence/crossing/development-blindness.json').read_text())
    assert len(blind['scenes'])==4 and all(s['revision']==args.revision for s in blind['scenes'])
    name=f'lux-collect-only-{args.revision}-{args.seed}'
    source=folder/'lux-collect-source';source.mkdir(exist_ok=True)
    for p in [Path(__file__),ROOT/'experimental/crossing/budget.py',ROOT/'experimental/crossing/scene.py']:
        target=source/p.name
        if target.exists():assert target.read_bytes()==p.read_bytes()
        else:shutil.copyfile(p,target)
    event(name,status='waiting_validity',pid=os.getpid(),output=str(folder.relative_to(ROOT)),new_lux_tasks=0)
    # Screen is zero-paid; do not generate an already wheel-passable threshold.
    deadline=time.monotonic()+1800
    while True:
        cases=list((folder/'validity').glob('*/result.json'))
        if len(cases)==6:break
        if time.monotonic()>deadline:raise RuntimeError('Validity is incomplete; no paid task created')
        time.sleep(5)
    trials=[json.loads(p.read_text()) for p in cases]
    if any(r['status'] in ('clean_pass','wheel_contact_pass') for r in trials):
        event(name,status='invalid_seed_no_generation',reason='wheel-only check passed')
        print('Seed is invalid; retained wheel checks; zero paid tasks',flush=True);return
    st=json.loads((obs/'state.json').read_text())
    request_path=obs/'lux_request.json'
    if request_path.exists():request=json.loads(request_path.read_text())
    else:
        items=records.items_first(st)
        for item in items:item['id']=f'crossing_{args.revision}_{args.seed}_{item["id"]}'
        request=records.write_request(obs,'img',items)
    budget=CrossingBudget();jobs=[]
    ledger=json.loads(budget.path.read_text())
    assert ledger.get('stop',{}).get('new_creation_stopped')
    rejected=[]
    for item in request['items']:
        reservation=next(r for r in ledger['tasks'] if r['sample']==item['id'])
        record=json.loads((ROOT/reservation['client_ledger']).read_text())
        if record.get('task_id'):jobs.append(record)
        else:
            assert record['status']=='not_submitted'
            rejected.append({**record,'status':'failed','submission_status':'not_submitted','not_a_created_task':True})
    event(name,status='collecting_known_only',task_ids=[r['task_id'] for r in jobs],stop='evidence/crossing/generation-stop.json')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs=list(pool.map(budget.poll,jobs))
    write(obs/'lux_result.json',{'schema':'beforestep-lux-result/v1','tasks':jobs+rejected})
    glbs=records.read_result(obs);assert glbs is not None
    event(name,status='admitting',task_ids=[r['task_id'] for r in jobs])
    out=folder/'decision';saved=out/'target_decision.json'
    if saved.exists():
        decision=json.loads(saved.read_text());assert decision['cache_identity']==IM.decision_identity(obs,glbs)
    else:decision=IM.decide_target(obs,glbs,out)
    geometry=[]
    for candidate in decision['candidates']:
        obj=IM.candidate_world_mesh(candidate['glb'],candidate['M'],st['local_frame'],out/f'world_{candidate["id"]}.obj')
        mesh=trimesh.load(obj,force='mesh',process=False);g=track_geometry(mesh)
        task=next(r for r in jobs if r['id']==candidate['id'])
        geometry.append({'id':candidate['id'],'task_id':task['task_id'],'admitted':candidate['admitted'],
            'metrics':{k:v for k,v in candidate.items() if k not in ['glb','M']},'world_mesh':str(obj.relative_to(ROOT)),
            'geometry':g,'far_error_m':[g['far'][i]-scene['truth_geometry']['far'][i] if g['far'][i] is not None else None for i in range(2)],
            'height_error_m':[g['high'][i]-scene['truth_geometry']['high'][i] if g['high'][i] is not None else None for i in range(2)]})
    report={'schema':'beforestep-crossing-lux-development/v1','seed':args.seed,'revision':args.revision,
        'generated':len(jobs),'glb_successes':len(glbs),'admitted':len(decision['admitted_ids']),
        'task_ids':[r['task_id'] for r in jobs],'candidates':geometry,'truth_geometry':scene['truth_geometry'],
        'observation':str(obs.relative_to(ROOT)),'request':str(request_path.relative_to(ROOT)),
        'budget_usage':json.loads(budget.path.read_text())['created'],'excluded_from_test_statistics':True,'create_rejections':len(rejected),'stopped_under':'SPEC §12.4'}
    write(folder/'lux-development.json',report);write(ROOT/'evidence/crossing/development-lux-first.json',report)
    result=ROOT/'docs/reviews/RESULT_WHEELLEG_CROSSING.md'
    with result.open('a') as f:
        f.write(f'\n## §6 首个真实Lux链路完成\n\n开发种子{args.seed}，{args.revision}：生成{len(jobs)}份、成功GLB{len(glbs)}份、原阈值准入{len(decision["admitted_ids"])}份。各任务号、每份双轮迹远缘/最高点误差见[原始表](../../evidence/crossing/development-lux-first.json)。这是开发数据，不入正式统计；未降低准入阈值。\n')
    event(name,status='stopped_provider_rejection_known_tasks_complete',results=report)
    with Path('/root/3d/MEMORY.md').open('a') as f:
        f.write(f'\n§6首个真实Lux链路已终态：{name}，生成{len(jobs)}、GLB{len(glbs)}、准入{len(decision["admitted_ids"])}；evidence/crossing/development-lux-first.json，budget.created={report["budget_usage"]}。原件和身份保留，禁止重建任务。下一步发布现有终态与未完成项；按§12.4仍停止新增请求，不调冻阈值。\n')
    print(json.dumps({k:report[k] for k in ['seed','generated','glb_successes','admitted','task_ids','budget_usage']}),flush=True)
if __name__=='__main__':main()
