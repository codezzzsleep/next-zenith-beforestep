"""Run observed-only B or Lux D on an already screened development scene."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import OUT, sha, write
from experimental.crossing.scene import generate
from experimental.crossing.execution import execute, observed_geometry
from experimental.crossing.decision import decide
from ops.crossing_probe import event


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--revision', default='scene-dev-v5')
    parser.add_argument('--method', choices=['B', 'D'], required=True)
    args = parser.parse_args()
    scene = generate(args.seed, args.revision)
    folder = Path(scene['truth_mesh']).parents[1]
    checks = [json.loads(p.read_text()) for p in (folder / 'validity').glob('*/result.json')]
    assert len(checks) == 6 and not any(r['status'] in ('clean_pass', 'wheel_contact_pass') for r in checks), 'Invalid scene'
    destination = folder / ('method-' + args.method + '-v1')
    source = destination / 'source'
    source.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__)] + [ROOT / 'experimental/crossing' / n for n in
                              ['action.py', 'runtime.py', 'scene.py', 'execution.py', 'decision.py']]
    for path in paths:
        saved = source / path.name
        if saved.exists():
            assert saved.read_bytes() == path.read_bytes()
        else:
            shutil.copyfile(path, saved)
    identity = f'method-{args.method}-{args.revision}-{args.seed}'
    event(identity, status='running', pid=os.getpid(), output=str(destination.relative_to(ROOT)))
    if args.method == 'B':
        result = execute(scene, folder / 'observation', observed_geometry(folder / 'observation'), destination, 'B')
    else:
        result = decide(scene, folder / 'observation', destination)
    event(identity, status='complete', result=str((destination / 'result.json').relative_to(ROOT)),
          outcome=result['status'])
    print(json.dumps({k: result[k] for k in ['seed', 'method', 'status']}, ensure_ascii=False), flush=True)
