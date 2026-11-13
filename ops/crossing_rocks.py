"""Compare the three abilities on three retained source-rock fixtures."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import *
from experimental.crossing.action import crossing
from experimental.crossing.assets import ROCKS, rock_fixture
from ops.crossing_audit import audit, physical_audit
from ops.crossing_probe import event


def run(rock, method, attempt):
    folder = OUT / 'calibration' / attempt / (rock + '-' + method)
    if (folder / 'result.json').exists():
        return json.loads((folder / 'result.json').read_text())
    obj, manifest = rock_fixture(rock)
    lo, hi = np.array(manifest['bounds_m'])
    geometry = {'near': [float(lo[0])] * 2, 'far': [float(hi[0])] * 2,
                'high': [float(hi[2])] * 2, 'lateral': 0.}
    e = env_for([obj])
    rec = Record(e)
    rec.frame('start')
    started = time.monotonic()
    if method == 'gait':
        ok, stages = crossing(rec, geometry)
    else:
        stages = []
        pose = stance_array(STANCE if method == 'fixed' else STANCE_HIGH)
        ok = transition(rec, pose, 2., 'raise' if method == 'high' else 'settle')
        if ok:
            ok = drive(rec, pose, float(hi[0]) + .35, timeout=240.)
    status = ('clean_pass' if ok and rec.summary()['steps_with_wheel_stone'] == 0 else
              'wheel_contact_pass' if ok else
              'body_collision' if rec.failure and rec.failure['kind'] == 'body_collision' else
              'unstable' if rec.failure else 'stuck')
    rec.save(folder)
    result = {'attempt': attempt, 'rock': rock, 'method': method, 'status': status,
              'sim_seconds': e.t, 'wall_seconds': time.monotonic() - started,
              'truth_geometry': geometry, 'truth_geometry_definition':
                  'Conservative whole-fixture bounds applied to both wheel tracks; physical scene uses the source rock mesh, not the bounds box.',
              'fixture': manifest, 'scene': e.spec, 'object_bounds': e.obj_bounds,
              'contact': rec.summary(), 'stages': stages, 'last_phase': rec.phase[-1],
              'final_base': e.data.qpos[:7].tolist(),
              'final_wheel_centres': wheel_positions(e).tolist(),
              'trajectory_sha256': sha(folder / 'trajectory.npz'),
              'contacts_sha256': sha(folder / 'contacts.npz'),
              'source_sha256': {p.name: sha(p) for p in (folder.parent / 'source').glob('*.py')},
              'new_lux_tasks': 0, 'common_total_time_limit_s': 240.}
    write(folder / 'result.json', result)
    if method == 'gait':
        write(folder / 'support-audit.json', audit(folder))
        write(folder / 'support-physical-audit.json', physical_audit(folder))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--rock', choices=ROCKS)
    parser.add_argument('--method', choices=['fixed', 'high', 'gait'])
    args = parser.parse_args()
    if args.rock:
        result = run(args.rock, args.method, args.attempt)
        print(json.dumps({k: result[k] for k in ['rock', 'method', 'status', 'sim_seconds']}), flush=True)
        return
    source = OUT / 'calibration' / args.attempt / 'source'
    source.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'experimental/crossing' / name for name in ['action.py', 'runtime.py', 'assets.py']]
    sources += [Path(__file__)]
    identity = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for p in sources:
        target = source / p.name
        if target.exists():
            assert target.read_bytes() == p.read_bytes()
        else:
            shutil.copy2(p, target)
    event(args.attempt, status='running', pid=__import__('os').getpid(),
          output=str(source.parent.relative_to(ROOT)), source_sha256=identity, trials=9, workers=1)
    rows = []
    for rock in ROCKS:
        for method in ['fixed', 'high', 'gait']:
            folder = source.parent / (rock + '-' + method)
            folder.mkdir(parents=True, exist_ok=True)
            if not (folder / 'result.json').exists():
                command = [sys.executable, str(Path(__file__)), '--attempt', args.attempt,
                           '--rock', rock, '--method', method]
                with (folder / 'run.log').open('a') as log:
                    process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    write(folder / 'process.json', {'pid': process.pid, 'command': command})
                    code = process.wait()
                if code:
                    write(folder / f'failure-{time.time_ns()}.json', {'exit_code': code, 'command': command})
                    event(args.attempt, status='failed', failed_case=rock + '-' + method)
                    raise RuntimeError('Rock trial failed; retain log and resume unfinished identity')
            result = json.loads((folder / 'result.json').read_text())
            rows.append({k: result[k] for k in ['rock', 'method', 'status', 'sim_seconds']})
            event(args.attempt, results=rows)
            print(json.dumps(rows[-1]), flush=True)
    assert all(sha(ROOT / p) == value for p, value in identity.items())
    write(source.parent / 'summary.json', {'trials': 9, 'results': rows})
    event(args.attempt, status='complete', results=rows)


if __name__ == '__main__':
    main()
