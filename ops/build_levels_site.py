"""Build playable levels from actual saved runs and registered candidate meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.navigation.controller import yaw_of
from beforestep.geometry.imagination import candidate_world_mesh
from evidence.reviews.beforestep_r1.build_eval import truth_polygons

DATA = ROOT / 'site/data/levels'
UP = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def trajectory(path, start, count=900):
    with np.load(path) as data:
        indices = np.flatnonzero(data['t'] >= start - 1e-6)
        selected = np.unique(np.r_[indices[::max(1, len(indices) // count)], indices[-1]])
        return [[float(data['t'][i]), float(data['qpos'][i, 0]), float(data['qpos'][i, 1]),
                 float(yaw_of(data['qpos'][i]))] for i in selected]


def model(mesh, path, anchor=None, yaw=None):
    mesh = mesh.copy()
    if yaw is not None:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1]))
    if anchor is not None:
        mesh.apply_translation(-np.array(anchor))
    mesh.apply_transform(UP)
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh,
        vertex_colors=np.tile([155, 169, 162, 255], (len(mesh.vertices), 1)))
    mesh.export(path)
    return str(path.relative_to(ROOT / 'site'))


def build(row):
    scene_id = row['scene']
    definition = S.configure(scene_id)
    actual = ROOT / row['runs']['imagination']['run']
    events = [json.loads(line) for line in (actual / 'events.jsonl').read_text().splitlines()]
    first = next(e for e in events if e['kind'] == 'look' and e['k'] == 1)
    image = DATA / 'images' / (scene_id + '_first.jpg')
    source_image = actual / 'looks/look1_rgb.png'
    picture = Image.open(source_image).convert('RGB'); picture.thumbnail((1200, 900)); picture.save(image, quality=93)
    state = np.load(actual / 'decision/look1_state.npy')
    record = {'id': scene_id, 'goal': definition['goal'], 'robot': S.ROBOT,
              'observation': {'image': str(image.relative_to(ROOT / 'site')), 'source_sha256': sha(source_image),
                 'time': first['t'], 'pose': first['measured_pose'],
                 'map': {'origin': [N.X0, N.Y0], 'resolution': N.RES, 'shape': list(state.shape),
                         'values': state.ravel().tolist()}, 'nogo': N.prior_nogo().ravel().astype(int).tolist()},
              'runs': {}, 'truth': {'rocks': []}, 'candidates': [],
              'reveal_description': f"{row['family']} · {'决定性场景' if row['classification']=='decisive' else '普通场景'}。三种选择的结果来自同一个真实仿真场景。",
              'evidence': row.get('evidence', 'evidence/reviews/beforestep_r1/lux/original_b/run_identity.json')}
    for key in ('optimistic', 'conservative', 'imagination'):
        path = ROOT / row['runs'][key]['run']
        summary = read(path / 'summary.json')
        identity = read(path / 'run_identity.json')
        assert summary['scene_id'] == scene_id and summary['controller'] == 'rules'
        assert identity['arguments']['pose_model'] is None
        record['runs'][key] = {**summary, 'run_id': identity['run_id'], 'source': str(path.relative_to(ROOT)),
                              'trajectory_sha256': sha(path / 'traj.npz'),
                              'trajectory': trajectory(path / 'traj.npz', first['t'])}
    polygons = truth_polygons(definition)
    true_masks = {}
    from matplotlib.path import Path as Polygon
    true_models = {}
    for key, rock in definition['rocks'].items():
        polygon = polygons[key]
        true_masks[key] = Polygon(polygon).contains_points(np.c_[N.GX.ravel(), N.GY.ravel()]).reshape(N.GX.shape)
        record['truth']['rocks'].append({'id': key, 'polygon': polygon.tolist()})
        scan, _ = S.rock_asset_uniform(rock['rock'], rock['height'])
        true_models[key] = model(trimesh.load(scan, force='mesh', process=False),
                                 DATA / 'meshes' / (scene_id + '_truth_' + key + '.glb'), yaw=rock['yaw'])
    scratch = ROOT / 'outputs/site/levels'
    scratch.mkdir(parents=True, exist_ok=True)
    for decision in sorted(actual.glob('looks/look*/T*/decide/target_decision.json')):
        target = decision.parent.parent
        target_state = read(target / 'state.json')
        cells = np.load(target / 'cells.npy')
        key = max(true_masks, key=lambda k: int((true_masks[k] & cells).sum()))
        rock = definition['rocks'][key]
        look = int(target_state['look'].removeprefix('look'))
        for candidate in read(decision)['candidates']:
            cid = f'{scene_id}_L{look}_{target.name}_{candidate["id"]}'
            footprint = decision.parent / ('footprint_' + candidate['id'] + '.npy')
            occupied = np.load(footprint) if footprint.exists() else np.zeros(N.GX.shape, bool)
            ix, iy = np.nonzero(occupied)
            uri = None
            if candidate.get('M') is not None and candidate.get('glb'):
                world = candidate_world_mesh(candidate['glb'], candidate['M'], target_state['local_frame'], scratch / (cid + '.obj'))
                uri = model(trimesh.load(world, force='mesh', process=False), DATA / 'meshes' / (cid + '.glb'),
                            anchor=[rock['x'], rock['y'], 0.])
            record['candidates'].append({'id': cid, 'look': '首眼' if look == 1 else '第二眼',
                'target': target.name, 'sample': candidate['id'], 'admitted': candidate['admitted'],
                'task_id': candidate.get('task_id'), 'model': uri, 'truth_model': true_models[key],
                'original_glb_sha256': sha(ROOT / candidate['glb']) if candidate.get('glb') else None,
                'model_sha256': sha(ROOT / 'site' / uri) if uri else None,
                'footprint': np.c_[N.XS[ix], N.YS[iy]].tolist(), 'source_decision': str(decision.relative_to(ROOT))})
    # Task ID lives in the raw result contract rather than the admission row.
    for result in actual.glob('looks/look*/T*/**/lux_result.json'):
        target = result.parent.parent if result.parent.name == 'retry' else result.parent
        state = read(target / 'state.json'); look = int(state['look'].removeprefix('look'))
        for task in read(result).get('tasks', []):
            for candidate in record['candidates']:
                if candidate['id'] == f"{scene_id}_L{look}_{target.name}_{task['id']}":
                    candidate['task_id'] = task['task_id']
    review = actual / 'physical_clearance.json'
    xy = actual / 'eval.json'
    if review.exists() and xy.exists():
        distance = min(r['minimum_signed_collision_geometry_distance_m'] for r in read(review)['rocks'].values())
        gap = min(r['min_xy_rectangle_envelope_gap_m'] for r in read(xy)['actual_clearance_by_rock'].values())
        record['clearance_note'] = f'赛后复盘：三维最小间隙 {distance*1000:.3f} mm；二维包络间隙 {gap*1000:.3f} mm。'
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', default='evidence/suite/summary.json')
    parser.add_argument('--anchor-only', action='store_true', help='Develop the UI using the real R1 anchor only')
    args = parser.parse_args()
    for folder in ('images', 'meshes'):
        (DATA / folder).mkdir(parents=True, exist_ok=True)
    if args.anchor_only:
        base = 'evidence/reviews/beforestep_r1'
        rows = [{'scene': 'stress_v8', 'family': 'F0', 'classification': 'decisive',
                 'runs': {'imagination': {'run': base + '/lux/original_b'},
                          'optimistic': {'run': base + '/section25_final_base/optimistic'},
                          'conservative': {'run': base + '/section25_final_base/conservative'}}}]
    else:
        rows = read(ROOT / args.summary)['scenes']
    data = {'schema': 'beforestep-playable-levels/v1', 'anchor_only_development': args.anchor_only,
            'scope': 'Recorded real experiment data; choice changes which saved physical trajectory is replayed.',
            'levels': [build(row) for row in rows]}
    (ROOT / 'site/data/levels.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'levels': len(data['levels']), 'anchor_only': args.anchor_only}))


if __name__ == '__main__':
    main()
