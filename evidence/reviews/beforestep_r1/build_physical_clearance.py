"""Post-run signed distances for the frozen simulation's collision geometry."""
from pathlib import Path
import hashlib
import json
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from beforestep import scene as S
from beforestep.navigation import map as N


def evaluate(run, environment, meta):
    m, d = environment.model, environment.data
    z = np.load(run/'traj.npz'); q, times = z['qpos'], z['t']
    assert q.shape[1] == m.nq
    robot = sorted(g for g in N.robot_geoms(environment) if m.geom_contype[g] or m.geom_conaffinity[g])
    results = {}
    for key, rock in meta['rocks'].items():
        body = mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,rock['body'])
        obstacles = [g for g in range(m.ngeom) if m.geom_bodyid[g] == body and
                     (m.geom_contype[g] or m.geom_conaffinity[g])]
        pairs = np.array([(a,b) for a in robot for b in obstacles if
            (m.geom_contype[a] & m.geom_conaffinity[b]) or
            (m.geom_contype[b] & m.geom_conaffinity[a])], dtype=int)
        assert len(pairs)
        best, witness = 10., None
        radii = m.geom_rbound[pairs[:,0]] + m.geom_rbound[pairs[:,1]]
        for index, pose in enumerate(q):
            d.qpos[:] = pose; d.qvel[:] = 0.; d.time = times[index]
            mujoco.mj_forward(m,d)
            lower = np.linalg.norm(d.geom_xpos[pairs[:,0]]-d.geom_xpos[pairs[:,1]],axis=1)-radii
            for pi in np.flatnonzero(lower <= best):
                a, b = pairs[pi]
                closest = np.zeros(6)
                distance = float(mujoco.mj_geomDistance(m,d,int(a),int(b),10.,closest))
                if distance < best:
                    best = distance
                    witness = {'trajectory_index':index,'time_s':float(times[index]),
                        'robot_geom':int(a),'obstacle_geom':int(b),
                        'nearest_points_xyz_m':closest.reshape(2,3).tolist()}
        results[key] = {'minimum_signed_collision_geometry_distance_m':best,
                        'witness':witness,'tested_geom_pairs':len(pairs)}
        print(json.dumps({'run':str(run.relative_to(ROOT)),'rock':key,'minimum_m':best}),flush=True)
    report = {'schema':'beforestep-r1-physical-clearance/v1',
        'scope':'Post-run reconstruction at every saved qpos, original MuJoCo collision geoms and masks; no simulation advance or planning input.',
        'run_id':json.loads((run/'run_identity.json').read_text())['run_id'],
        'trajectory_sha256':hashlib.sha256((run/'traj.npz').read_bytes()).hexdigest(),
        'distance_function':'mujoco.mj_geomDistance; signed, negative means geometric penetration',
        'sample_count':len(q),'scene':json.loads((run/'scene.json').read_text()),
        'physical_contact_record':json.loads((run/'summary.json').read_text())['collision'],
        'rocks':results}
    (run/'physical_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    base = Path(__file__).resolve().parent
    S.configure('stress_v8')
    spec, _, meta = S.scene_spec(ROOT/'outputs/reviews/r1/clearance_diagnostic_world')
    environment = S.make_env(spec)
    run = base/'lux/original_b'
    evaluate(run,environment,meta)


if __name__ == '__main__':
    main()
