"""Close the existing threshold batch without submitting or executing a method."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
import numpy as np
import trimesh
from beforestep.generation import records as LX
from beforestep.geometry import imagination as IM
from experimental.crossing.budget import CrossingBudget
from experimental.crossing.runtime import write
from experimental.crossing.scene import track_geometry
from ops.crossing_lux import admit_sample, merge_admissions

if __name__ == '__main__':
    budget = CrossingBudget()
    data = json.loads(budget.path.read_text())
    assert data['threshold_generation_closed']
    assert all(r['status'] in ('ok', 'failed', 'not_submitted') for r in data['tasks'])
    folder = ROOT/'outputs/crossing/development/scene-dev-v9/seed-22005'
    scene = json.loads((folder/'scene.json').read_text())
    obs = folder/'observation'
    request = json.loads((obs/'lux_request.json').read_text())
    jobs = []
    for item in request['items']:
        row = next(r for r in data['tasks'] if r['sample'] == item['id'])
        record = json.loads((ROOT/row['client_ledger']).read_text())
        assert record['task_id'] == row['task_id'] and record['status'] in ('ok', 'failed')
        jobs.append(record)
        if record['status'] == 'ok':
            admit_sample(obs, record, folder)
    write(obs/'lux_result.json', {'schema': 'beforestep-lux-result/v1', 'tasks': jobs})
    glbs = LX.read_result(obs)
    out = folder/'decision'
    if (out/'target_decision.json').exists():
        decision = json.loads((out/'target_decision.json').read_text())
        assert decision['cache_identity'] == IM.decision_identity(obs, glbs)
    else:
        decision = merge_admissions(obs, glbs, folder, out)
    st = json.loads((obs/'state.json').read_text())
    candidates = []
    for c in decision['candidates']:
        obj = IM.candidate_world_mesh(c['glb'], c['M'], st['local_frame'], out/f'world_{c["id"]}.obj')
        geometry = track_geometry(trimesh.load(obj, force='mesh', process=False))
        task = next(r for r in jobs if r['id'] == c['id'])
        candidates.append({'id': c['id'], 'task_id': task['task_id'], 'admitted': c['admitted'],
            'metrics': {k:v for k,v in c.items() if k not in ('glb','M')}, 'world_mesh': str(obj.relative_to(ROOT)),
            'geometry': geometry,
            'far_error_m': [geometry['far'][i]-scene['truth_geometry']['far'][i] if geometry['far'][i] is not None else None for i in range(2)],
            'height_error_m': [geometry['high'][i]-scene['truth_geometry']['high'][i] if geometry['high'][i] is not None else None for i in range(2)]})
    report = {'schema':'beforestep-crossing-lux-development/v1', 'seed':22005, 'revision':'scene-dev-v9',
        'generated':len(jobs), 'glb_successes':len(glbs), 'admitted':len(decision['admitted_ids']),
        'task_ids':[r['task_id'] for r in jobs], 'candidates':candidates, 'truth_geometry':scene['truth_geometry'],
        'observation':str(obs.relative_to(ROOT)), 'request':str((obs/'lux_request.json').relative_to(ROOT)),
        'budget_usage':data['created'], 'excluded_from_test_statistics':True, 'collection_only_addendum2':True}
    write(folder/'lux-development.json', report)
    write(ROOT/'evidence/crossing/development-lux-scene-dev-v9-22005.json', report)
    closure = {'schema':'beforestep-crossing-threshold-closure/v1', 'created':data['created'],
        'glb_successes':sum(r['status']=='ok' for r in data['tasks']),
        'failed_tasks':sum(r['status']=='failed' for r in data['tasks']),
        'requests_not_submitted':sum(r['status']=='not_submitted' for r in data['tasks']),
        'pending_or_uncertain':[], 'new_tasks_in_closure':0, 'threshold_generation_closed':True,
        'cancelled':['remaining threshold development','threshold preregistration','twelve formal threshold tests'],
        'last_scene':report, 'budget':'outputs/generation/crossing-budget.json'}
    write(ROOT/'evidence/crossing/route/threshold-closure.json', closure)
    progress_path=ROOT/'outputs/crossing/route/progress.json'
    progress=json.loads(progress_path.read_text())
    progress['steps']['close_threshold_lux'].update(status='终态',result='closed',created=data['created'])
    write(progress_path,progress)
    with Path('/root/3d/MEMORY.md').open('a') as f:
        f.write(f'\n补充2门槛Lux收尾终态：总{data["created"]}，GLB全部收齐；22005六份准入{report["admitted"]}，只完成自检不执行旧D、不新增。证据evidence/crossing/route/threshold-closure.json；下一route四检查。\n')
    print(json.dumps({k:closure[k] for k in ('created','glb_successes','new_tasks_in_closure')},ensure_ascii=False),flush=True)
