"""Add missing owner-video postmortems in new sidecars, never old results."""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import sys

from beforestep import scene as S
ROOT = S.ROOT
sys.path.insert(0, str(ROOT))
from evidence.reviews.beforestep_r1 import build_eval as XY
from evidence.reviews.beforestep_r1 import build_physical_clearance as PHYSICAL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--need-xy', action='store_true')
    parser.add_argument('--need-physical', action='store_true')
    args = parser.parse_args()
    run = ROOT / args.run
    identity = json.loads((run / 'run_identity.json').read_text())
    summary = json.loads((run / 'summary.json').read_text())
    out = ROOT / 'outputs/video/r3/reviews' / identity['run_id']
    out.mkdir(parents=True, exist_ok=True)
    # A recovery worker and the completion supervisor may reach this saved run
    # together. Serialize sidecar creation and reuse completed files unchanged.
    with (out / '.review.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in ('scene.json', 'summary.json', 'run_identity.json', 'events.jsonl', 'traj.npz'):
            if not (out / name).exists():
                shutil.copy2(run / name, out / name)
        S.configure(summary['scene_id'])
        if args.need_xy and not (out / 'eval.json').exists():
            XY.evaluate(out)
        if args.need_physical and not (out / 'physical_clearance.json').exists():
            spec, _, meta = S.scene_spec(out / 'world')
            environment = S.make_env(spec)
            PHYSICAL.evaluate(out, environment, meta)
    print(json.dumps({'source_run': args.run, 'sidecar': str(out.relative_to(ROOT)), 'post_run_only': True}))


if __name__ == '__main__':
    main()
