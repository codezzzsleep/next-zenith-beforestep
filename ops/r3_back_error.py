"""Post-run forward-axis error for every original admitted R1/R2 candidate."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.evaluation import truth_footprints

ROOT = S.ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect():
    suite = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    rows = []
    for scene in suite['scenes']:
        S.configure(scene['scene'])
        run = ROOT / scene['runs']['imagination']['run']
        truth = truth_footprints(run)
        for path in sorted(run.glob('looks/look*/T*/decide/target_decision.json')):
            target = path.parent.parent
            state = json.loads((target / 'state.json').read_text())
            cells = np.load(target / 'cells.npy')
            rocks = [key for key, mask in truth.items() if (mask & cells).any()]
            assert rocks, str(target)
            actual = np.logical_or.reduce([truth[key] for key in rocks])
            yaw = state['local_frame']['yaw0']
            direction = np.array([np.cos(yaw), np.sin(yaw)])
            projection = N.GX * direction[0] + N.GY * direction[1]
            true_end = float(projection[actual].max())
            decision = json.loads(path.read_text())
            tasks = {}
            for result in (target / 'lux_result.json', target / 'retry/lux_result.json'):
                if result.exists():
                    tasks.update({item['id']: item for item in json.loads(result.read_text())['tasks']})
            for candidate in decision['candidates']:
                if not candidate['admitted']:
                    continue
                footprint = path.parent / ('footprint_' + candidate['id'] + '.npy')
                occupied = np.load(footprint)
                predicted_end = float(projection[occupied].max())
                rows.append({'scene': scene['scene'], 'anchor': bool(scene.get('anchor')),
                    'run_id': scene['runs']['imagination']['run_id'], 'look': state['look'],
                    'target': target.name, 'associated_true_rocks': rocks,
                    'candidate': candidate['id'], 'task_id': tasks[candidate['id']]['task_id'],
                    'forward_axis_world_xy': direction.tolist(),
                    'predicted_farthest_m': predicted_end, 'truth_farthest_m': true_end,
                    'back_error_m': predicted_end - true_end,
                    'shorter_than_five_cm': predicted_end - true_end < -.05,
                    'decision': str(path.relative_to(ROOT)), 'decision_sha256': sha(path),
                    'footprint': str(footprint.relative_to(ROOT)), 'footprint_sha256': sha(footprint)})
    return rows


def main():
    rows = collect()
    out = ROOT / 'evidence/reviews/beforestep_r3/back-error'
    out.mkdir(parents=True, exist_ok=True)
    report = {'schema': 'beforestep-r3-admitted-back-error/v1',
        'scope': 'Post-run 5cm XY footprint diagnostic; never provided to production planning',
        'definition': 'Candidate farthest minus associated truth-union farthest along the recorded robot forward axis at that observation',
        'candidate_count': len(rows), 'r1_count': sum(r['anchor'] for r in rows),
        'r2_count': sum(not r['anchor'] for r in rows),
        'shorter_than_five_cm': sum(r['shorter_than_five_cm'] for r in rows),
        'threshold_m': -.05, 'rows': rows}
    (out / 'stats.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    values = np.array([r['back_error_m'] * 100 for r in rows])
    fig, ax = plt.subplots(figsize=(9, 4.6), constrained_layout=True)
    ax.hist(values, bins=np.linspace(np.floor(values.min()/5)*5, np.ceil(values.max()/5)*5+5, 20),
            color='#3b9b8d', edgecolor='white', linewidth=.6)
    ax.axvline(-5, color='#b93f47', linewidth=2, label='Frozen 5 cm margin: -5 cm')
    ax.axvline(0, color='#36424a', linewidth=1, linestyle=':')
    ax.set(xlabel='Back error along recorded robot forward axis (cm)',
           ylabel='Admitted candidates', title='Visible-face admission does not verify the hidden back')
    ax.text(.98, .95, f"All {len(rows)} admitted candidates\n{report['shorter_than_five_cm']} shorter by more than 5 cm",
            transform=ax.transAxes, ha='right', va='top')
    ax.legend(loc='upper left'); ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(out / 'figure.png', dpi=190); fig.savefig(out / 'figure.svg')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
