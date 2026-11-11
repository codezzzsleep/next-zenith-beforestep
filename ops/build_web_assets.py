"""Deliver real models, measurements and trajectories to the homepage author."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np
from PIL import Image
import trimesh

from beforestep import scene as S
from beforestep.navigation import map as N, controller as F
from beforestep.generation import client as C
from web_glb import make_web, LIMIT

ROOT = C.ROOT
OUT = ROOT / 'evidence/web-assets'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    live = Path('/root/3d/.memory/live/web-assets.json')
    job = {'status': 'running', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
           'output': str(OUT), 'paid_tasks': 0, 'log': 'outputs/qa/r3/final/web-assets.log'}
    C.atomic_json(live, job)
    original = ROOT / 'evidence/reviews/beforestep_r1/lux/original_b'
    anchor_tasks = [task for target in ['T1', 'T2']
                    for task in read(original / 'looks/look1' / target / 'lux_result.json')['tasks']]
    anchor_ids = {task['task_id'] for task in anchor_tasks}
    records = {}
    for path in sorted(C.LEDGER.glob('tasks/*.json')):
        row = read(path)
        if row.get('status') != 'ok' or not row.get('glb'):
            continue
        source = (ROOT / row['glb']).resolve()
        if source.is_relative_to(ROOT) and source.is_file():
            records[row['task_id']] = {key: row.get(key) for key in
                ['task_id', 'id', 'identity', 'glb', 'glb_sha256', 'inputs', 'input_sha256', 'api_field', 'n_images']}
    for row in anchor_tasks:
        if row['status'] == 'ok':
            assert row['task_id'] in records
    ordered = sorted(records, key=lambda task: (task not in anchor_ids, task))
    registry, failures = {}, []

    def model(task_id):
        row = records[task_id]
        source = ROOT / row['glb']
        assert sha(source) == row['glb_sha256']
        target = OUT / 'models' / (str(task_id)+'.glb')
        sidecar = target.with_suffix('.json')
        if sidecar.exists() and target.exists():
            existing = read(sidecar)
            if existing['source_sha256'] == row['glb_sha256'] and sha(target) == existing['sha256']:
                assert target.stat().st_size <= LIMIT
                return existing
        info = make_web(source, target)
        info.update(task_id=task_id, sample=row['id'], source=str(source.relative_to(ROOT)),
                    path=str(target.relative_to(ROOT)), inputs=row['inputs'], input_sha256=row['input_sha256'])
        C.atomic_json(sidecar, info)
        return info

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(model, task): task for task in ordered}
        for future in as_completed(futures):
            task = futures[future]
            try:
                registry[task] = future.result()
            except Exception as error:
                failures.append({'task_id': task, 'reason': str(error), 'source': records[task]['glb']})
            if (len(registry)+len(failures)) % 12 == 0:
                job.update(models_ready=len(registry), failures=failures)
                C.atomic_json(live, job)
                print(json.dumps({'web_models': len(registry), 'failures': len(failures)}), flush=True)
    assert all(task['task_id'] in registry for task in anchor_tasks if task['status'] == 'ok'), failures

    items = {}

    def register(path, role, source=None, task_id=None):
        relative = str(path.relative_to(ROOT))
        if relative not in items:
            items[relative] = {'path': relative, 'sha256': sha(path), 'bytes': path.stat().st_size,
                               'roles': [], 'sources': []}
        item = items[relative]
        if role not in item['roles']:
            item['roles'].append(role)
        if source:
            proof = {'path': str(source.relative_to(ROOT)), 'sha256': sha(source)}
            if task_id is not None:
                proof['task_id'] = task_id
            if proof not in item['sources']:
                item['sources'].append(proof)
        return relative

    def publish(source, role, task_id=None):
        source = Path(source)
        digest = sha(source)
        target = OUT / 'objects' / (digest + source.suffix.lower())
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        assert sha(target) == digest
        return register(target, role, source, task_id)

    missing_inputs = []
    for task, info in registry.items():
        register(ROOT / info['path'], 'real_generated_web_glb', ROOT / info['source'], task)
        input_files = []
        for source, digest in zip(info['inputs'] or [], info['input_sha256'] or []):
            path = (ROOT / source).resolve()
            if not path.is_file():
                missing_inputs.append({'task_id': task, 'source': source, 'sha256': digest})
                continue
            assert path.is_relative_to(ROOT) and sha(path) == digest
            input_files.append(publish(path, 'actual_uploaded_input', task))
        info['web_inputs'] = input_files

    # Registration is a context of an observation, not a global property of a
    # task reused from identical pixels in another run.
    contexts = []
    primary = read(ROOT / 'evidence/suite/summary.json')
    revised = read(ROOT / 'evidence/reviews/beforestep_r3/summary.json')
    runs = {row['runs']['imagination']['run'] for row in primary['scenes']}
    runs |= {record['run'] for row in revised['frozen']+revised['holdouts']
             for policy, record in row['runs'].items() if policy in ('imagination','imagination_strict') and record.get('summary')}
    UP = trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0])
    for relative in sorted(runs):
        run = ROOT / relative
        identity = read(run / 'run_identity.json')
        for decision_path in sorted(run.glob('looks/look*/T*/decide/target_decision.json')):
            target = decision_path.parent.parent
            state = read(target / 'state.json')
            task_rows = read(target / 'lux_result.json')['tasks']
            retry = target / 'retry/lux_result.json'
            if retry.exists():
                task_rows += read(retry)['tasks']
            by_sample = {r['id']: r for r in task_rows}
            decision = read(decision_path)
            frame = state['local_frame']; c, s = np.cos(frame['yaw0']), np.sin(frame['yaw0'])
            world = np.array([[c,-s,0,frame['x0']],[s,c,0,frame['y0']],[0,0,1,0],[0,0,0,1.]])
            for candidate in decision['candidates']:
                task = by_sample[candidate['id']]['task_id']
                if task not in registry:
                    continue
                M = np.asarray(candidate.get('M')) if candidate.get('M') is not None else None
                threshold = decision.get('thresholds', {}).get('contour_iou_min')
                reason = '通过当前可见观测的冻结自检；不保证背面正确。' if candidate['admitted'] else (
                    '轮廓与实际观测不符。' if threshold is not None and candidate.get('contour_iou', 1) < threshold
                    else '未满足冻结自检；各项原始数值见 metrics。')
                available = M is not None and M.shape == (4,4) and np.isfinite(M).all()
                contexts.append({'task_id': task, 'sample': candidate['id'], 'scene': identity['scene']['id'],
                    'run_id': identity['run_id'], 'run': relative, 'look': state['look'], 'target': target.name,
                    'admitted': candidate['admitted'], 'reason': reason, 'metrics': candidate,
                    'thresholds': decision.get('thresholds'), 'source_decision': str(decision_path.relative_to(ROOT)),
                    'source_decision_sha256': sha(decision_path), 'local_frame': frame, 'registration_available': bool(available),
                    'local_from_generated': M.tolist() if available else None,
                    'world_from_generated': (world@M).tolist() if available else None,
                    'viewer_y_up_from_generated': (UP@world@M).tolist() if available else None})

    S.configure('stress_v8')
    truth = []
    for name, rock in S.ROCKS.items():
        obj, texture = S.rock_asset_uniform(rock['rock'], rock['height'])
        obj = Path(obj)
        mesh = trimesh.load(obj, force='mesh', process=False)
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rock['yaw']), [0,0,1]))
        mesh.apply_translation([rock['x'],rock['y'],0])
        mesh.apply_transform(UP)
        intermediate = ROOT / 'outputs/qa/r3/final/web-truth-sources' / (name+'-original-world.glb')
        intermediate.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(intermediate)
        target = OUT / 'truth' / (name+'.glb')
        info = make_web(intermediate, target)
        register(target, 'true_scan_world_y_up_web_glb', obj)
        truth.append({'rock': name, 'path': str(target.relative_to(ROOT)), 'sha256': sha(target),
                      'bytes': target.stat().st_size, 'source_obj': str(obj.relative_to(ROOT)),
                      'source_obj_sha256': sha(obj), 'coordinate_frame': 'world; Z-up converted to glTF Y-up',
                      'source_scene': 'config/scenes/stress_v8.json', 'web_representation': info['representation']})

    anchor_runs = {'imagination': original, **{policy: ROOT / 'evidence/reviews/beforestep_r1/section25_final_base' / policy
                                             for policy in ['conservative','see_dark','optimistic']}}
    anchor = {'schema': 'beforestep-homepage-anchor/v1', 'scene': 'stress_v8',
              'generated': [], 'truth': truth, 'observations': [], 'runs': {}, 'rehearsals': [],
              'registration_contexts': [r for r in contexts if r['run'] == str(original.relative_to(ROOT))],
              'scope': 'Actual recorded simulation and real Lux3D tasks. Web copies are visual assets; raw models and frozen engineering results are unchanged.'}
    for task in anchor_tasks:
        row = {'task_id': task['task_id'], 'sample': task['id'], 'provider_status': task['status']}
        if task['status'] == 'ok':
            row.update(registry[task['task_id']])
        else:
            row['reason'] = '供应商生成失败，没有GLB；不算自检拒绝。'
        anchor['generated'].append(row)
    for policy, run in anchor_runs.items():
        identity = read(run / 'run_identity.json')
        summary = read(run / 'summary.json')
        with np.load(run / 'traj.npz') as z:
            t, q = z['t'], z['qpos']
            trajectory = [[float(t[i]),float(q[i,0]),float(q[i,1]),float(F.yaw_of(q[i]))] for i in range(len(t))]
        file = OUT / 'trajectories' / (policy+'.json'); C.atomic_json(file, {'run_id': identity['run_id'], 'summary': summary,
            't_xy_yaw': trajectory, 't':t.tolist(), 'qpos':q.tolist(), 'source_npz_sha256':sha(run/'traj.npz')})
        register(file, 'full_sample_trajectory_json', run / 'traj.npz')
        anchor['runs'][policy] = {'summary': summary, 'run_id': identity['run_id'],
                                  'trajectory_json': str(file.relative_to(ROOT)),
                                  'trajectory_npz': publish(run / 'traj.npz', 'original_five_arrays_npz')}
        for rgb in sorted((run / 'looks').glob('look*_rgb.png')):
            look = rgb.name.removesuffix('_rgb.png')
            depth, dark = run / 'looks' / (look+'_depth.npy'), run / 'looks' / (look+'_dark.npy')
            row = {'policy': policy, 'look': look, 'run_id': identity['run_id'],
                   'rgb': publish(rgb, 'actual_rgb'), 'depth': publish(depth, 'recorded_depth_m'),
                   'dark': publish(dark, 'recorded_dark_mask')}
            dark_values = np.load(dark).astype(bool)
            image = OUT / 'observations' / f'{policy}-{look}-dark.png'
            image.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(dark_values.astype(np.uint8)*255).save(image)
            row['dark_png'] = register(image, 'actual_dark_mask_png', dark)
            depth_values = np.load(depth)
            usable = np.isfinite(depth_values) & ~dark_values & (depth_values < np.nanmax(depth_values))
            encoded = np.where(usable, np.clip(depth_values*1000, 0, 65535), 0).astype(np.uint16)
            image = OUT / 'observations' / f'{policy}-{look}-depth-mm.png'
            Image.fromarray(encoded).save(image)
            row['depth_mm_png'] = register(image, 'recorded_depth_display_png', depth)
            row['depth_display_encoding'] = '16-bit millimetres, 0=recorded DARK or far-plane background; display clips at 65.535m. Original float32 depth and DARK bytes are preserved.'
            anchor['observations'].append(row)
        for state in sorted((run / 'decision').glob('look*_state.npy')):
            publish(state, 'original_observed_occupancy_classes')
    first = original / 'decision/look1_state.npy'
    state = np.load(first)
    union = np.zeros_like(state, dtype=bool)
    footprint_sources = []
    for target in ['T1','T2']:
        folder = original / 'looks/look1' / target / 'decide'
        decision = read(folder / 'target_decision.json')
        task_ids = {t['id']:t['task_id'] for t in read(folder.parent/'lux_result.json')['tasks']}
        for candidate in decision['candidates']:
            if candidate['admitted']:
                p = folder / ('footprint_'+candidate['id']+'.npy')
                union |= np.load(p)
                footprint_sources.append(publish(p, 'admitted_original_footprint', task_ids[candidate['id']]))
    from scipy import ndimage
    occupied = N.occupancy(state, 'imagination', ndimage.binary_dilation(union, iterations=1))
    path = OUT / 'observations/anchor-imagination-occupancy.npy'; np.save(path, occupied)
    register(path, 'recomputed_frozen_original_imagination_occupancy', first)
    anchor['occupancy'] = {'path': str(path.relative_to(ROOT)), 'state_source': str(first.relative_to(ROOT)),
        'admitted_footprints': footprint_sources, 'resolution_m': N.RES, 'origin_xy': [N.X0,N.Y0],
        'scope': 'Read-only recomputation with the passed R1 implementation and original footprints; no truth geometry is supplied.'}
    for pane in sorted((original / 'rehearsal/look1').glob('pane*/traj.npz')):
        with np.load(pane) as z:
            t, q = z['t'], z['qpos']
            data = [[float(t[i]),float(q[i,0]),float(q[i,1]),float(F.yaw_of(q[i]))] for i in range(len(t))]
        path = OUT / 'trajectories' / (pane.parent.name+'.json'); C.atomic_json(path,
            {'t_xy_yaw':data,'t':t.tolist(),'qpos':q.tolist(),'source':str(pane.relative_to(ROOT)),'source_npz_sha256':sha(pane)})
        register(path, 'full_sample_rehearsal_json', pane)
        anchor['rehearsals'].append({'pane': pane.parent.name, 'trajectory_json': str(path.relative_to(ROOT)),
                                     'trajectory_npz': publish(pane, 'original_rehearsal_npz')})
    assert len(anchor['rehearsals']) == 12
    assert not any(r['task_id'] in anchor_ids for r in missing_inputs)
    path = OUT / 'anchor.json'; C.atomic_json(path, anchor); register(path, 'complete_anchor_bundle')
    path = OUT / 'models.json'; C.atomic_json(path, {'models':list(registry.values()), 'not_prepared':failures,'missing_inputs':missing_inputs}); register(path, 'all_model_registry')
    path = OUT / 'registrations.json'; C.atomic_json(path, {'contexts':contexts}); register(path, 'observed_registration_matrices_and_all_selfcheck_values')
    path = OUT / 'facts.json'; facts = read(ROOT/'evidence/award/facts.json')
    facts.update(anchor_audit=read(ROOT/'site/data/demo.json')['audit'],
                 original_failure_facts=read(ROOT/'evidence/reviews/beforestep_r3/failure-facts.json'),
                 all_original_back_errors=read(ROOT/'evidence/reviews/beforestep_r3/back-error/stats.json'))
    C.atomic_json(path, facts); register(path, 'all_numbers_with_evidence_sources')
    C.atomic_json(OUT / 'index.json', {'schema':'beforestep-web-assets/v1','items':list(items.values()),
        'anchor':'evidence/web-assets/anchor.json','models':'evidence/web-assets/models.json',
        'registrations':'evidence/web-assets/registrations.json','facts':'evidence/web-assets/facts.json',
        'web_glb_max_bytes':LIMIT,'ready_models':len(registry),'anchor_successful_models':len([r for r in anchor_tasks if r['status']=='ok']),
        'no_paid_tasks':True,'coordinate_note':'Generated web GLBs retain original glTF frame. Apply viewer_y_up_from_generated for overlay with truth world-Y-up GLBs.'})
    job.update(status='complete', models_ready=len(registry), failures=failures, index=str((OUT/'index.json').relative_to(ROOT)))
    C.atomic_json(live, job)
    print(json.dumps({'complete':True,'web_models':len(registry),'anchor_generated':len(anchor['generated']),
                      'anchor_successful':11,'truth_models':len(truth),'four_runs':len(anchor['runs']),
                      'observations':len(anchor['observations']),'rehearsals':len(anchor['rehearsals']),
                      'indexed_files':len(items),'failures':len(failures)}),flush=True)


if __name__ == '__main__':
    main()
