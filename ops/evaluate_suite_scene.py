"""Post-run only: actual 3D/XY clearance and original optimistic plan intrusion."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from beforestep import scene as S
from evidence.reviews.beforestep_r1 import build_eval as XY
from evidence.reviews.beforestep_r1 import build_physical_clearance as PHYSICAL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--real-run', required=True)
    parser.add_argument('--optimistic-run', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    output = (ROOT / args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    actual = (ROOT / args.real_run).resolve()
    optimistic = (ROOT / args.optimistic_run).resolve()
    S.configure(args.scene)
    actual_xy = XY.evaluate(actual)
    optimistic_xy = XY.evaluate(optimistic)
    spec, _, meta = S.scene_spec(output / 'world')
    environment = S.make_env(spec)
    distance = PHYSICAL.evaluate(actual, environment, meta)
    review = json.loads((actual / 'eval.json').read_text())
    plan = json.loads((optimistic / 'eval.json').read_text())
    result = {'schema': 'beforestep-suite-post-run-review/v1', 'scene': args.scene,
              'scope': 'Post-run truth only; no hidden geometry was supplied to production planning',
              'actual_run_id': review['run_id'], 'optimistic_run_id': plan['run_id'],
              'minimum_3d_clearance_m': min(r['minimum_signed_collision_geometry_distance_m'] for r in distance['rocks'].values()),
              'actual_3d_by_rock': distance['rocks'], 'actual_xy_by_rock': review['actual_clearance_by_rock'],
              'minimum_xy_envelope_clearance_m': min(r['min_xy_rectangle_envelope_gap_m'] for r in review['actual_clearance_by_rock'].values()),
              'optimistic_plan_intrusion_by_rock': plan['first_departure_plan_by_rock'],
              'optimistic_max_intrusion_m': max((r['planned_envelope_intrusion_proxy_m'] for r in plan['first_departure_plan_by_rock'].values()), default=0),
              'diagnostic_results': [actual_xy, optimistic_xy]}
    (output / 'review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
