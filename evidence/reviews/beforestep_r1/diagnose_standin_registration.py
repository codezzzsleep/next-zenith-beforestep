"""Read-only post-run comparison of one known-shape stand-in and its placement."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull
from matplotlib.path import Path as Polygon
import trimesh

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep import evaluation as E


def footprint(vertices):
    xy = vertices[:, :2]
    polygon = xy[ConvexHull(xy).vertices]
    return Polygon(polygon).contains_points(np.c_[N.GX.ravel(), N.GY.ravel()]).reshape(N.GX.shape)


def main():
    base = Path(__file__).resolve().parent
    run = base / 'standins/single_batch'
    S.configure('stress_v8')
    target = run / 'looks/look2/T2'
    state = json.loads((target / 'state.json').read_text())
    candidate = json.loads((target / 'decide/target_decision.json').read_text())['candidates'][0]
    mesh_path = base / 'standins/shared_geometry/B.glb'
    mesh = trimesh.load(mesh_path, force='mesh', process=False)
    vertices = np.asarray(mesh.vertices)
    frame = state['local_frame']
    c, s = np.cos(frame['yaw0']), np.sin(frame['yaw0'])
    frame_matrix = np.array([[c,-s,0,frame['x0']], [s,c,0,frame['y0']],
                             [0,0,1,0], [0,0,0,1.]])
    actual = frame_matrix @ np.asarray(candidate['M'])
    rock = S.ROCKS['B']
    yaw = np.radians(rock['yaw']); c, s = np.cos(yaw), np.sin(yaw)
    expected = np.array([[c,-s,0,rock['x']], [s,c,0,rock['y']],
                         [0,0,1,0], [0,0,0,1.]])
    placed = vertices @ actual[:3,:3].T + actual[:3,3]
    known = vertices @ expected[:3,:3].T + expected[:3,3]
    scale = float(np.cbrt(np.linalg.det(actual[:3,:3])))
    rotation = actual[:3,:3] / scale
    angle = np.degrees(np.arccos(np.clip((np.trace(rotation @ expected[:3,:3].T)-1)/2,-1,1)))
    true = E.truth_footprints(run)
    registered_mesh = footprint(placed)
    saved = np.load(target / 'decide/footprint_A1.npy')
    observed = np.load(run / 'decision/look2_state.npy')
    start = np.load(run / 'traj.npz')['qpos'][-1,:2]
    comparisons = {}
    for name, b in [('true_B', true['B']), ('registered_mesh_hull_B', registered_mesh),
                    ('registered_voxel_footprint_B', saved)]:
        occupancy = N.occupancy(observed, 'imagination',
                               ndimage.binary_dilation(true['A'] | b, iterations=1))
        path = N.plan(occupancy, start, S.GOAL)
        comparisons[name] = {'B_cells':int(b.sum()), 'path':path,
                             'min_y_m':float(N.GY[b].min()), 'max_y_m':float(N.GY[b].max())}
    differences = np.linalg.norm(placed-known, axis=1)
    report = {
        'schema':'beforestep-r1-standin-placement-diagnostic/v1',
        'scope':'Post-run only; no registration, thresholds, scene or production decisions changed.',
        'not_real_lux':True,
        'run_id':json.loads((run/'run_identity.json').read_text())['run_id'],
        'mesh_sha256':hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        'matrix_world_registered':actual.tolist(), 'matrix_world_known_standin':expected.tolist(),
        'uniform_scale':scale, 'rotation_error_deg':float(angle),
        'world_xy_translation_error_m':float(np.linalg.norm(actual[:2,3]-expected[:2,3])),
        'world_translation_delta_m':(actual[:3,3]-expected[:3,3]).tolist(),
        'registered_yaw_deg':float(np.degrees(np.arctan2(actual[1,0],actual[0,0]))),
        'known_yaw_deg':rock['yaw'],
        'corresponding_vertex_displacement_m':{'median':float(np.median(differences)),
                                              'max':float(differences.max())},
        'registered_bounds_xyz_m':[placed.min(0).tolist(),placed.max(0).tolist()],
        'known_bounds_xyz_m':[known.min(0).tolist(),known.max(0).tolist()],
        'saved_voxel_vs_registered_hull_difference_cells':int((saved ^ registered_mesh).sum()),
        'diagnostic_plans_using_same_observed_map_true_A_and_frozen_5cm_rule':comparisons}
    destination = base / 'standin_placement_diagnostic.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('uniform_scale','rotation_error_deg',
           'world_xy_translation_error_m','registered_yaw_deg','known_yaw_deg',
           'saved_voxel_vs_registered_hull_difference_cells')}, indent=2))
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    main()
