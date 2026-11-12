"""Build the homepage data file from audited project evidence (dev tool, not shipped).

Reads frozen evidence; writes the delivered canonical data contract and web images.
Asset URL binding is performed separately by integrate_owner_homepage.py.
Every number on the homepage comes from one of the SOURCES below.
"""
import json
import argparse
from pathlib import Path

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', default=str(REPO / 'evidence/award/home-contract'))
args = parser.parse_args()
HOME = Path(args.out).resolve()
R1 = REPO / 'evidence/reviews/beforestep_r1/lux/original_b'
SOURCES = {
    'anchor': 'site/data/demo.json',
    'scene': 'evidence/reviews/beforestep_r1/lux/original_b/scene.json',
    'suite_r2': 'evidence/suite/summary.json',
    'suite_r3': 'evidence/reviews/beforestep_r3/summary.json',
    'back_error': 'evidence/reviews/beforestep_r3/back-error/stats.json',
    'footprints': 'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/decide/footprint_*.npy',
}


def load(rel):
    return json.loads((REPO / rel).read_text())


def thin(points, keep=220):
    """Downsample a trajectory, always keeping the first and last sample."""
    if len(points) <= keep:
        return points
    idx = np.unique(np.linspace(0, len(points) - 1, keep).round().astype(int))
    return [points[i] for i in idx]


def xy(traj):
    return [[round(float(p[1]), 3), round(float(p[2]), 3)] for p in traj]


def outcome(summary):
    if not isinstance(summary, dict) or 'result' not in summary:
        return None
    result = summary['result']
    if summary.get('collision') and result != 'collision':
        result = 'collision'
    return {'result': result, 'looks': summary.get('looks'), 'sim_time_s': summary.get('sim_time_s')}


demo = load(SOURCES['anchor'])
scene = load(SOURCES['scene'])

runs = {}
for key in ('conservative', 'optimistic', 'see_dark', 'imagination'):
    run = demo['runs'][key]
    runs[key] = {
        'label': demo['labels'][key], 'result': run['result'], 'looks': run['looks'],
        'sim_time_s': run['sim_time_s'], 'collision': run.get('collision'),
        'traj': thin(xy(run['trajectory'])),
    }

rehearsals = [{'label': pane['label'], 'completed': pane['completed'], 'collided': pane['collided'],
               'traj': thin(xy(pane['trajectory']), 120)} for pane in demo['gallery']]

rock_of = {'T1': 'A', 'T2': 'B'}
candidates = []
for c in demo['candidates']:
    rock = rock_of[c['target']]
    candidates.append({
        'rock': rock, 'sample': c['sample_id'], 'task_id': c['task_id'], 'admitted': c['admitted'],
        'contour_iou': c['contour_iou'], 'scale_ratio': c['scale_ratio'],
        'reason': c.get('rejection_reason'), 'glb': f"assets/glb/{rock}-{c['sample_id']}.glb",
        'poster': f"assets/img/poster/{rock}-{c['sample_id']}.jpg",
    })
candidates.sort(key=lambda c: (c['rock'], c['sample']))

# Imagined footprints of the two admitted B candidates, as 5 cm cells in world XY.
footprints = {}
for sample in ('A2', 'C1'):
    grid = np.load(R1 / f'looks/look1/T2/decide/footprint_{sample}.npy')
    ii, jj = np.nonzero(grid)
    footprints[sample] = [[round(-0.975 + 0.05 * int(i), 3), round(-1.975 + 0.05 * int(j), 3)]
                          for i, j in zip(ii, jj)]

back = [{'candidate': r['candidate'], 'task_id': r['task_id'], 'target': r['target'],
         'predicted_farthest_m': r['predicted_farthest_m'], 'truth_farthest_m': r['truth_farthest_m'],
         'back_error_m': r['back_error_m'], 'forward_axis': r['forward_axis_world_xy']}
        for r in load(SOURCES['back_error'])['rows'] if r['scene'] == 'stress_v8']
back_all = load(SOURCES['back_error'])

r2 = load(SOURCES['suite_r2'])
r3 = load(SOURCES['suite_r3'])


def r3_runs(row):
    out = {}
    for policy, run in (row.get('runs') or {}).items():
        out[policy] = outcome(run.get('summary') if isinstance(run, dict) and 'summary' in run else run)
    return out


known = [{'scene': s['scene'], 'classification': s['classification'],
          'runs': {p: outcome(r.get('summary')) for p, r in (s.get('runs') or {}).items()}}
         for s in r2['scenes']]
strict_known = {row['scene']: r3_runs(row).get('imagination_strict') for row in r3['frozen']}
for row in known:
    row['runs']['imagination_strict'] = strict_known.get(row['scene'])
holdouts = [{'scene': row['scene'], 'status': row.get('status'), 'runs': r3_runs(row)} for row in r3['holdouts']]


def tally(rows, policy):
    count = {'arrived': 0, 'stuck': 0, 'collision': 0, 'stopped_short': 0}
    for row in rows:
        o = row['runs'].get(policy)
        if o:
            count[o['result']] = count.get(o['result'], 0) + 1
    return count


POLICIES = ('conservative', 'see_dark', 'optimistic', 'imagination', 'imagination_strict')
decisive = [r for r in known if r['classification'] == 'decisive']
stats = {
    'known_decisive': {p: tally(decisive, p) for p in POLICIES},
    'known_all': {p: tally(known, p) for p in POLICIES},
    'holdout': {p: tally(holdouts, p) for p in POLICIES},
}

data = {
    'generated_from': SOURCES,
    'scene': {'id': scene['id'], 'start': scene['start'], 'goal': demo['goal'],
              'rocks': demo['rocks'], 'rille_edge': demo['rille_edge'], 'wall_y': demo['wall_y'],
              'envelope': demo['robot_envelope'], 'truth': scene['rocks']},
    'runs': runs, 'rehearsals': rehearsals, 'candidates': candidates,
    'generation': demo['generation'], 'audit': demo['audit'],
    'footprints_B': footprints, 'back_error_anchor': back,
    'imagined_union': [[round(float(x), 3), round(float(y), 3)] for x, y in demo['imagined_footprint']],
    'back_error_all': {k: back_all[k] for k in ('candidate_count', 'shorter_than_five_cm', 'threshold_m')},
    'known': known, 'holdouts': holdouts, 'stats': stats,
    'counterfactuals': {'r2': r2['counterfactuals'], 'r3': r3['new_rejected_counterfactual_stats_by_scope']},
    'paid_tasks': r3['paid_tasks'],
}
# What the robot knew after its first look: one digit per 5 cm cell.
# 0 seen free ground, 1 seen rock, 2 sun shadow (no depth), 3 hidden behind something, 4 never in view.
state = np.load(R1 / 'looks/look1_state.npy')
data['look1_state'] = {'nx': int(state.shape[0]), 'ny': int(state.shape[1]), 'x0': -0.975, 'y0': -1.975,
                       'res': 0.05, 'cells': ''.join(str(int(v)) for v in state.flatten())}

# Pixels with no depth in the first view, leaving out the sky (pixels at the far plane).
dark = np.load(R1 / 'looks/look1_dark.npy')
depth = np.load(R1 / 'looks/look1_depth.npy')
ground_dark = dark & (depth < np.nanmax(depth) - 1e-6)
data['dark_fraction_without_sky'] = round(float(ground_dark.mean()), 4)
(HOME / 'assets/img').mkdir(parents=True, exist_ok=True)
Image.fromarray((ground_dark * 255).astype('uint8'), 'L').save(HOME / 'assets/img/first-view-dark.png', optimize=True)

out = HOME / 'assets/data/site.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))

# Images: real observations and real uploads, re-encoded for the web only (no edits).
img = HOME / 'assets/img'
img.mkdir(parents=True, exist_ok=True)
jobs = [
    (R1 / 'looks/look1/T1/rgb.png', img / 'first-view.jpg', 1600),
    (R1 / 'looks/look1/T1/gen/variants/A1_upload.jpg', img / 'upload-A.jpg', 1200),
    (R1 / 'looks/look1/T2/gen/variants/A1_upload.jpg', img / 'upload-B.jpg', 1200),
]
for src, dst, width in jobs:
    picture = Image.open(src)
    if picture.width > width:
        picture = picture.resize((width, round(picture.height * width / picture.width)), Image.LANCZOS)
    if dst.suffix == '.jpg':
        picture.convert('RGB').save(dst, quality=86, optimize=True, progressive=True)
    else:
        picture.save(dst, optimize=True)

print('site.json', out.stat().st_size // 1024, 'KB', '| dark without sky:', data['dark_fraction_without_sky'])
print('runs:', {k: (v['result'], v['looks'], v['sim_time_s'], len(v['traj'])) for k, v in runs.items()})
print('rehearsals:', len(rehearsals), 'all completed:', all(r['completed'] and not r['collided'] for r in rehearsals))
print('candidates:', [(c['rock'], c['sample'], c['admitted']) for c in candidates])
print('back error (anchor):', [(b['target'], b['candidate'], round(b['back_error_m'], 3)) for b in back])
for scope, table in stats.items():
    print(scope, {p: {k: v for k, v in t.items() if v} for p, t in table.items()})
print('cf r2:', {k: r2['counterfactuals'][k] for k in ('executed', 'collisions')}, '| r3:', data['counterfactuals']['r3'])
print('paid:', r3['paid_tasks'])
