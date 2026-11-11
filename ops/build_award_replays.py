"""Publish separate v3 trajectories without modifying original level payloads."""
import hashlib
import json
from pathlib import Path

import numpy as np
from beforestep.navigation.controller import yaw_of

ROOT = Path(__file__).resolve().parents[1]


def main():
    ledger = json.loads((ROOT / 'outputs/r3/v3/frozen/processes.json').read_text())
    assert ledger['completed']
    runs = {}
    for scene, job in ledger['jobs'].items():
        folder = (ROOT / job['chain']).parent / 'imagination_strict'
        summary = json.loads((folder / 'summary.json').read_text())
        identity = json.loads((folder / 'run_identity.json').read_text())
        with np.load(folder / 'traj.npz') as trace:
            times, qpos = trace['t'], trace['qpos']
            indices = np.unique(np.r_[np.arange(0, len(times), max(1, len(times) // 900)), len(times) - 1])
            trajectory = [[float(times[i]), float(qpos[i, 0]), float(qpos[i, 1]),
                           float(yaw_of(qpos[i]))] for i in indices]
        runs[scene] = {**summary, 'run_id': identity['run_id'], 'trajectory': trajectory,
                       'source': str(folder.relative_to(ROOT)),
                       'trajectory_sha256': hashlib.sha256((folder / 'traj.npz').read_bytes()).hexdigest(),
                       'evidence': f'evidence/reviews/beforestep_r3/scenes/{scene}/manifest.json',
                       'scope': 'Post-result revision, final v3, same known scene; not out-of-sample evidence.'}
    path = ROOT / 'site/data/award-revisions.json'
    path.write_text(json.dumps({'schema': 'beforestep-award-replays/v1', 'runs': runs},
                               ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'revision_replays': len(runs), 'original_levels_payload_changed': False}))


if __name__ == '__main__':
    main()
