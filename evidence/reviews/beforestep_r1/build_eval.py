"""Post-run R1 geometry audit. Truth is used only here, never by a planner."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from beforestep import scene as S
from beforestep.navigation import controller as F


def polygon_distances(points, polygon):
    from matplotlib.path import Path as Polygon
    points = np.asarray(points)
    starts = polygon
    edges = np.roll(polygon, -1, axis=0) - polygon
    length2 = np.sum(edges * edges, axis=1)
    result = []
    for first in range(0, len(points), 256):
        block = points[first:first+256]
        relative = block[:, None, :] - starts[None, :, :]
        t = np.clip(np.sum(relative * edges[None, :, :], axis=2) / length2, 0, 1)
        nearest = starts[None, :, :] + t[..., None] * edges[None, :, :]
        distance = np.linalg.norm(block[:, None, :] - nearest, axis=2).min(axis=1)
        distance[Polygon(polygon).contains_points(block)] = 0
        result.append(distance)
    return np.concatenate(result)


def envelope_gap(center, yaw, polygon):
    c, s = np.cos(yaw), np.sin(yaw)
    rotation = np.array([[c, -s], [s, c]])
    half_len, half_width = S.ROBOT['half_len'], S.ROBOT['half_wid']
    rectangle = np.array([[-half_len,-half_width],[half_len,-half_width],
                          [half_len,half_width],[-half_len,half_width]]) @ rotation.T + center
    edges = np.concatenate([np.roll(rectangle,-1,axis=0)-rectangle,
                            np.roll(polygon,-1,axis=0)-polygon])
    axes = np.stack([-edges[:,1],edges[:,0]],axis=1)
    a, b = rectangle @ axes.T, polygon @ axes.T
    separated = (a.max(axis=0) < b.min(axis=0)) | (b.max(axis=0) < a.min(axis=0))
    if not separated.any(): return 0.
    return float(min(polygon_distances(rectangle,polygon).min(),
                     polygon_distances(polygon,rectangle).min()))


def dense_route(start, path, pitch=.005):
    points = [np.asarray(start)]
    for end in path:
        a, b = points[-1], np.asarray(end)
        count = max(2, int(np.ceil(np.linalg.norm(b-a)/pitch))+1)
        points.extend(a + np.linspace(0,1,count)[1:,None]*(b-a))
    return np.asarray(points)


def truth_polygons(definition):
    from scipy.spatial import ConvexHull
    polygons = {}
    for key, rock in definition['rocks'].items():
        obj, _ = S.rock_asset_uniform(rock['rock'], rock['height'])
        vertices = np.array([[float(v) for v in line.split()[1:3]]
                             for line in Path(obj).read_text().splitlines() if line.startswith('v ')])
        yaw=np.radians(rock['yaw']); c,s=np.cos(yaw),np.sin(yaw)
        vertices=vertices @ np.array([[c,-s],[s,c]]).T + [rock['x'],rock['y']]
        polygons[key]=vertices[ConvexHull(vertices).vertices]
    return polygons


def evaluate(run):
    summary=json.loads((run/'summary.json').read_text())
    definition=json.loads((run/'scene.json').read_text())
    polygons=truth_polygons(definition)
    events=[json.loads(line) for line in (run/'events.jsonl').read_text().splitlines() if line]
    data=np.load(run/'traj.npz'); q=data['qpos']; xy=q[:,:2]
    actual={}
    radius=np.hypot(S.ROBOT['half_len'],S.ROBOT['half_wid'])
    for key, polygon in polygons.items():
        distances=polygon_distances(xy,polygon); best_center=float(distances.min())
        subset=np.flatnonzero(distances <= best_center + 2*radius)
        gap=min(envelope_gap(xy[i],F.yaw_of(q[i]),polygon) for i in subset)
        actual[key]={'min_center_distance_m':best_center,
                     'min_center_minus_half_width_m':best_center-S.ROBOT['half_wid'],
                     'min_xy_rectangle_envelope_gap_m':gap}
    first_look=next(e for e in events if e['kind']=='look')
    first_plan=next((e for e in events if e['kind']=='plan' and e.get('path')),None)
    planned={}
    if first_plan:
        look=next(e for e in events if e['kind']=='look' and e['k']==first_plan['look'])
        start=look.get('measured_pose',look['pose'])[:2]
        route=dense_route(start,first_plan['path'])
        for key,polygon in polygons.items():
            distance=float(polygon_distances(route,polygon).min())
            planned[key]={'min_center_distance_m':distance,
                          'center_minus_half_width_m':distance-S.ROBOT['half_wid'],
                          'planned_envelope_intrusion_proxy_m':max(0,S.ROBOT['half_wid']-distance)}
    report={'schema':'beforestep-r1-post-run-eval/v1',
        'scope':'Post-run frozen scan geometry; 5 mm route sampling; rectangle is an XY envelope, not a 3D contact test.',
        'not_real_lux':(run/'standin_provenance.json').exists(),
        'run_id':json.loads((run/'run_identity.json').read_text())['run_id'],
        'summary_sha256':hashlib.sha256((run/'summary.json').read_bytes()).hexdigest(),
        'scene':definition,'robot_envelope':S.ROBOT,'result':summary['result'],
        'actual_clearance_by_rock':actual,'first_departure_plan':first_plan,
        'first_departure_plan_by_rock':planned,
        'optimistic_intrusion_at_least_10cm':
            summary['policy']=='optimistic' and planned.get('B',{}).get('planned_envelope_intrusion_proxy_m',0)>=.1,
        'physical_collision':summary['collision'],
        'execution_rehearsals':[e for e in events if e['kind']=='rehearsal' and e.get('role','execution')=='execution']}
    (run/'eval.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return {'run':str(run.relative_to(ROOT)),'result':summary['result'],
            'planned_B_intrusion_m':planned.get('B',{}).get('planned_envelope_intrusion_proxy_m'),
            'actual_min_xy_envelope_gap_m':min(a['min_xy_rectangle_envelope_gap_m'] for a in actual.values())}


if __name__=='__main__':
    base=Path(__file__).resolve().parent
    runs=[p.parent for p in base.glob('section20/*/summary.json')]
    runs += [p.parent for p in base.glob('section20_final/*/summary.json')]
    runs += [p.parent for p in base.glob('standins/*/summary.json')]
    print(json.dumps([evaluate(run) for run in sorted(runs)],indent=2))
