"""Export actual scan footprints and admitted candidate footprints for C2.

The editable scene is a lightweight geometric view. Saved first-eye maps are
also provided separately for the quantitative planner consistency check.
"""
import json
from pathlib import Path

import numpy as np
import trimesh

from beforestep import scene as S
from beforestep.navigation import map as N

ROOT = S.ROOT


def main():
    levels = json.loads((ROOT / 'site/data/levels.json').read_text())
    library = {}
    for asset in sorted((ROOT / 'assets/rocks').iterdir()):
        path = asset / 'h1/body_vis.obj'
        if not path.is_file():
            continue
        # Use the same principal-axis alignment and ground normalization as the
        # real scene exporter, rather than the raw scan's arbitrary frame.
        previous_precision = S.ASSET_CACHE_PRECISION
        try:
            S.ASSET_CACHE_PRECISION = 'exact'
            canonical, _ = S.rock_asset_uniform(asset.name, 1.0)
        finally:
            S.ASSET_CACHE_PRECISION = previous_precision
        mesh = trimesh.load(canonical, force='mesh', process=False)
        from scipy.spatial import ConvexHull
        points = mesh.vertices[:, :2]
        hull = points[ConvexHull(points).vertices]
        library[asset.name] = {'id': asset.name, 'footprint': hull.tolist(),
                              'height': float(mesh.bounds[1, 2] - mesh.bounds[0, 2]),
                              'candidates': []}
    presets = []
    for level in levels['levels']:
        definition = S.configure(level['id'])
        for candidate in level['candidates']:
            if not candidate['admitted'] or not candidate['footprint']:
                continue
            # Only use single-rock observations as reusable rock templates.
            actual = ROOT / level['runs']['imagination']['source']
            target = ROOT / candidate['source_decision']
            cells = np.load(target.parent.parent / 'cells.npy')
            from beforestep.evaluation import truth_footprints
            masks = truth_footprints(actual)
            overlapping = [k for k, m in masks.items() if (m & cells).any()]
            if len(overlapping) != 1:
                continue
            rock = definition['rocks'][overlapping[0]]
            row = library[rock['rock']]
            if row['candidates'] and row['candidates'][0]['scene'] != level['id']:
                continue
            row['candidates'].append({'source': candidate['source_decision'],
                'scene': level['id'], 'task_id': candidate['task_id'],
                'sample': candidate['sample'], 'height': rock['height'],
                'pose': [rock['x'], rock['y'], rock['yaw']],
                'footprint': candidate['footprint'], 'resolution': N.RES})
        presets.append({'id': level['id'], 'definition': definition,
                        'observation': level['observation'],
                        'candidates': [c for c in level['candidates'] if c['admitted']]})
    output = {'schema': 'beforestep-sandbox-data/v1',
        'development_anchor_only': levels['anchor_only_development'],
        'scope': 'Lightweight geometry and planning; no physics or live Lux3D.',
        'grid': {'origin': [N.X0, N.Y0], 'shape': [N.NX, N.NY], 'resolution': N.RES},
        'robot': S.ROBOT, 'drive_radius': N.R_DRIVE, 'turn_radius': N.R_TURN,
        'library': list(library.values()), 'presets': presets}
    (ROOT / 'site/data/sandbox.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'rocks': len(library), 'presets': len(presets),
                      'rocks_with_admitted_templates': sum(bool(r['candidates']) for r in library.values())}))


if __name__ == '__main__':
    main()
