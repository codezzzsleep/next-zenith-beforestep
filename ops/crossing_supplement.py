"""Measure the wheel-only comparison at the supplemental 15 cm depth."""
import json
import os
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops.crossing_calibrate import run_fixed
from ops.crossing_probe import event
from experimental.crossing.runtime import OUT, sha, write


def main():
    attempt = 'wheel-d15-common240-v1'
    folder = OUT / 'calibration' / attempt
    source = folder / 'source'
    source.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), ROOT / 'ops/crossing_calibrate.py', ROOT / 'experimental/crossing/runtime.py']
    identity = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for path in paths:
        target = source / path.name
        if target.exists():
            assert target.read_bytes() == path.read_bytes()
        else:
            shutil.copy2(path, target)
    event(attempt, status='running', pid=os.getpid(), output=str(folder.relative_to(ROOT)),
          source_sha256=identity, trials=18, common_total_time_limit_s=240., workers=1)
    rows = []
    for h in [.10, .12, .15]:
        for method in ['fixed', 'high']:
            for angle in [0, -5, 5]:
                target = folder / f'{method}-h{h:.3f}-d0.150-a{angle:+.1f}'
                result = run_fixed(h, .15, angle, method, target, seconds=240.)
                rows.append(result)
                event(attempt, completed=len(rows))
                print(json.dumps({k: result[k] for k in ['method', 'h_m', 'angle_deg', 'status', 'sim_seconds']}), flush=True)
    assert all(sha(ROOT / p) == value for p, value in identity.items())
    write(folder / 'summary.json', {'trials': len(rows), 'results': rows, 'common_total_time_limit_s': 240.})
    event(attempt, status='complete', completed=len(rows))


if __name__ == '__main__':
    main()
