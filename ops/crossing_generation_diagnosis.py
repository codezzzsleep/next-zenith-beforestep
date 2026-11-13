"""Separate input, cached registration and generated-shape failures without creates."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
import trimesh
from beforestep.geometry import camera as CAM, imagination as IM, metrics as MET, admission as ADM, registration as REG
from experimental.crossing.runtime import sha, write
from ops.crossing_probe import event

FOLDER = ROOT / 'outputs/crossing/development/scene-dev-v5/seed-11002'
OBSERVATION = FOLDER / 'observation'
DIAGNOSIS = ROOT / 'outputs/crossing/diagnosis/input-registration-v1'


def principal_extents(points):
    centred = points - points.mean(axis=0)
    _, axes = np.linalg.eigh(np.cov(centred.T))
    return np.sort(np.ptp(centred @ axes, axis=0)).tolist()


def audit():
    path = DIAGNOSIS / 'audit.json'
    if path.exists():
        return json.loads(path.read_text())
    state = json.loads((OBSERVATION / 'state.json').read_text())
    obs = IM.load_observation(OBSERVATION)
    world = np.load(OBSERVATION / 'visible_points_world.npy')
    points = obs['points']
    frame = state['local_frame']
    c, s = np.cos(frame['yaw0']), np.sin(frame['yaw0'])
    rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    restored = points @ rotation.T + np.array([frame['x0'], frame['y0'], 0])
    u, v, z = CAM.project(points, obs['camera'])
    ui, vi = np.rint(u).astype(int), np.rint(v).astype(int)
    rgb = Image.open(OBSERVATION / 'rgb_gen.png')
    width, height = rgb.size
    mh, mw = obs['mask'].shape
    inputs = []
    for sample, item in state['crops'].items():
        box = item['crop_box']
        x0, y0, x1, y1 = [int(round(a)) for a in
                          [box[0] * mw / width, box[1] * mh / height,
                           box[2] * mw / width, box[3] * mh / height]]
        retained = int(obs['mask'][y0:y1, x0:x1].sum())
        inputs.append({'sample': sample, 'class': item['class'], 'sha256': item['sha256'],
                       'crop_box': box, 'observed_target_pixels_retained': retained,
                       'observed_target_pixels_total': int(obs['mask'].sum()),
                       'retained_fraction_low_resolution_mask': retained / int(obs['mask'].sum()),
                       'path_bytes_match_state': sha(ROOT / item['path']) == item['sha256']})
    decision = json.loads((FOLDER / 'decision/target_decision.json').read_text())
    candidates = []
    for candidate in decision['candidates']:
        mesh = trimesh.load(candidate['glb'], force='mesh', process=False)
        sampled = trimesh.sample.sample_surface(mesh, 10000, seed=0)[0]
        eigen = principal_extents(sampled)
        matrix = np.asarray(candidate['M'])
        singular = np.linalg.svd(matrix[:3, :3], compute_uv=False)
        mesh.apply_transform(matrix)
        candidates.append({'id': candidate['id'], 'principal_extents_native': eigen,
                           'principal_long_short_ratio': eigen[-1] / eigen[0],
                           'placed_bounds_local_m': mesh.bounds.tolist(),
                           'visible_top_m': state['visible']['H_vis'],
                           'matrix_singular_values': singular.tolist(),
                           'matrix_uniform_scale_error': float(np.ptp(singular)),
                           'frozen_metrics': {k: candidate[k] for k in
                                              ['contour_iou', 'scale_ratio', 'hidden_frac', 'shell_contact', 'free_intrusion_frac']}})
    ys, xs = np.nonzero(obs['mask'])
    result = {'schema': 'beforestep-crossing-input-audit/v1', 'new_lux_tasks': 0,
              'diagnostic_only': True, 'world_local_max_error_m': float(np.max(np.abs(restored - world))),
              'reprojection_max_error_px': float(max(np.max(np.abs(u - ui)), np.max(np.abs(v - vi)))),
              'reprojection_depth_max_error_m': float(np.max(np.abs(z - obs['depth'][vi, ui]))),
              'all_reprojected_points_on_observation_mask': bool(obs['mask'][vi, ui].all()),
              'mask_bbox_px': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
              'target_pixels_on_image_border': int(obs['mask'][:, 0].sum() + obs['mask'][:, -1].sum()
                                                 + obs['mask'][0].sum() + obs['mask'][-1].sum()),
              'input_classes_have_unique_images': len({r['sha256'] for r in inputs}),
              'inputs': inputs, 'observed_principal_extents_m': principal_extents(points),
              'candidates': candidates,
              'limitations': ['Crop retention is measured against the stored low-resolution observed target mask.',
                              'Principal extents are a shape diagnostic, not a proof that all placements are impossible.']}
    write(path, result)
    write(ROOT / 'evidence/crossing/diagnosis-input-audit-v1.json', result)
    return result


def cached_candidate(candidate):
    out = DIAGNOSIS / 'cached-poses' / (candidate['id'] + '.json')
    if out.exists():
        return json.loads(out.read_text())
    V, g, _, _ = IM.build_volume(OBSERVATION)
    mesh = trimesh.load(candidate['glb'], force='mesh', process=False)
    aligned = json.loads((FOLDER / 'decision/reg' / candidate['id'] / 'align.json').read_text())
    rows = []
    for pose in aligned['all']:
        metrics = MET.admission_metrics(mesh, np.asarray(pose['M']), V, g, {'mask_iou': pose['diagnostics']['mask_iou']})
        metrics['scale_ratio'] = ADM.scale_ratio_ground(metrics['P'], V, g)
        metrics.pop('P')
        rows.append({'rank': pose['rank'], 'selected_originally': pose['rank'] == aligned['best']['rank'],
                     'quality': pose['quality'], 'metrics': metrics, 'admitted_diagnostic': ADM.admitted(metrics)})
    result = {'id': candidate['id'], 'poses': rows, 'any_cached_pose_admitted': any(r['admitted_diagnostic'] for r in rows),
              'diagnostic_only': True, 'new_lux_tasks': 0}
    write(out, result)
    return result


def truth_registration():
    target = DIAGNOSIS / 'truth-registration.json'
    if target.exists():
        return json.loads(target.read_text())
    # Known-answer diagnostic: truth is deliberately supplied only here.
    truth = FOLDER / 'threshold/truth.glb'
    obs = IM.load_observation(OBSERVATION)
    registration = REG.register(truth, OBSERVATION, IM.PROTO, DIAGNOSIS / 'truth-registration', top_k=6,
                                observation_loader=IM.load_observation, coarse_searcher=IM.coarse_search,
                                evaluator=IM.evaluate_matrix, scorer=IM.observation_score)
    V, g, _, _ = IM.build_volume(OBSERVATION)
    mesh = trimesh.load(truth, force='mesh', process=False)
    metrics = MET.admission_metrics(mesh, np.asarray(registration['M']), V, g, registration['diagnostics'])
    metrics['scale_ratio'] = ADM.scale_ratio_ground(metrics['P'], V, g)
    metrics.pop('P')
    result = {'diagnostic_only': True, 'not_a_lux_result': True, 'new_lux_tasks': 0,
              'metrics': metrics, 'admitted_diagnostic': ADM.admitted(metrics),
              'production_registration_diagnostics': registration['diagnostics'],
              'exact_truth_diagnostic_reference': 'evidence/crossing/development-truth-admission-v5.json'}
    write(target, result)
    write(ROOT / 'evidence/crossing/diagnosis-truth-registration-v1.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['audit', 'cached', 'truth'], required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    DIAGNOSIS.mkdir(parents=True, exist_ok=True)
    source = DIAGNOSIS / 'source'
    source.mkdir(exist_ok=True)
    for file in [Path(__file__)]:
        saved = source / file.name
        if saved.exists():
            assert saved.read_bytes() == file.read_bytes()
        else:
            shutil.copyfile(file, saved)
    identity = 'diagnosis-input-registration-v1-' + args.stage
    event(identity, status='running', pid=os.getpid(), new_lux_tasks=0,
          source_sha256=sha(Path(__file__)), output=str(DIAGNOSIS.relative_to(ROOT)))
    if args.stage == 'audit':
        result = audit()
        print(json.dumps({k: result[k] for k in ['world_local_max_error_m', 'reprojection_max_error_px',
                                                'input_classes_have_unique_images', 'target_pixels_on_image_border']}))
    elif args.stage == 'truth':
        result = truth_registration()
        print(json.dumps(result))
    else:
        candidates = json.loads((FOLDER / 'decision/target_decision.json').read_text())['candidates']
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(cached_candidate, candidates))
        result = {'diagnostic_only': True, 'new_lux_tasks': 0, 'candidates': rows}
        write(ROOT / 'evidence/crossing/diagnosis-cached-poses-v1.json', result)
        print(json.dumps({'candidates': len(rows), 'any_cached_pose_admitted': sum(r['any_cached_pose_admitted'] for r in rows)}))
    event(identity, status='complete', new_lux_tasks=0)
