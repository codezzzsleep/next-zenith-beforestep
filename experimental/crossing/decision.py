"""Development decision rule: geometry envelope, every-world rehearsal, execution."""
import copy
import json
from pathlib import Path

import numpy as np
import trimesh

from .execution import execute, geometry_for
from .runtime import ROOT, sha, write


SETTINGS = {'geometry_margin_m': .003, 'maximum_height_m': .15,
            'maximum_depth_m': .15, 'positions': 5}


def decide(scene, observation, destination):
    destination = Path(destination)
    if (destination / 'result.json').exists():
        return json.loads((destination / 'result.json').read_text())
    observation = Path(observation)
    admission = json.loads((observation.parent / 'decision/target_decision.json').read_text())
    candidates = [c for c in admission['candidates'] if c['admitted']]
    result = {'schema': 'beforestep-crossing-development-decision/v1', 'seed': scene['seed'],
              'revision': scene['revision'], 'method': 'D', 'settings': SETTINGS,
              'admitted_ids': [c['id'] for c in candidates], 'positions': [], 'rehearsals': [],
              'excluded_from_formal_statistics': True,
              'action_sha256': sha(ROOT / 'experimental/crossing/action.py'),
              'admission_sha256': sha(observation.parent / 'decision/target_decision.json')}
    meshes = [(c, trimesh.load(observation.parent / 'decision' / f'world_{c["id"]}.obj',
                               force='mesh', process=False)) for c in candidates]
    limit = scene['gap_m'] / 2 - .25
    for lateral in np.linspace(-limit, limit, SETTINGS['positions']):
        rows = []
        for candidate, mesh in meshes:
            geometry = geometry_for(mesh, float(lateral))
            rows.append({'id': candidate['id'], 'geometry': geometry})
        covered = bool(rows) and all(all(v is not None for v in row['geometry'][key])
                                     and row['geometry']['body_high'] is not None
                                     for row in rows for key in ['near', 'far', 'high'])
        item = {'lateral_m': float(lateral), 'candidates': rows, 'all_tracks_covered': covered,
                'within_capability': False}
        if covered:
            margin = SETTINGS['geometry_margin_m']
            near = min(v for row in rows for v in row['geometry']['near']) - margin
            far = max(v for row in rows for v in row['geometry']['far']) + margin
            high = max(max(row['geometry']['high'] + [row['geometry']['body_high']])
                       for row in rows) + margin
            clearance = min(SETTINGS['maximum_height_m'] - high,
                            SETTINGS['maximum_depth_m'] - (far - near))
            item.update(envelope={'near': [near] * 2, 'far': [far] * 2,
                                  'high': [high] * 2, 'lateral': float(lateral)},
                        clearance_m=clearance, within_capability=clearance >= 0)
        result['positions'].append(item)
    eligible = [p for p in result['positions'] if p['within_capability']]
    result.update(decision='stop', status='stopped', reason='no_admitted_geometry' if not candidates
                  else 'no_position_within_all_admitted_worlds')
    if eligible:
        chosen = max(eligible, key=lambda p: (p['clearance_m'], -abs(p['lateral_m'])))
        result['chosen'] = chosen
        # Only T changes. Gate stones and flat ground remain the declared known context.
        for candidate, mesh in meshes:
            folder = destination / 'rehearsal' / candidate['id']
            posed = folder / 'threshold'
            posed.mkdir(parents=True, exist_ok=True)
            mesh.export(posed / 'truth.obj')
            write(posed / 'manifest.json', {'coordinate_frame': 'world', 'parts': ['truth.obj'],
                                          'parts_sha256': {'truth.obj': sha(posed / 'truth.obj')},
                                          'collision': 'MuJoCo mesh convex hull'})
            objects = copy.deepcopy(scene['spec']['objects'])
            objects[0] = {'posed_dir': str(posed)}
            rehearsal = execute(scene, observation, chosen['envelope'], folder, 'D-rehearsal', objects)
            result['rehearsals'].append(rehearsal)
        if all(r['status'] == 'clean_pass' for r in result['rehearsals']):
            result.update(decision='cross', reason='every_admitted_world_rehearsed_cleanly')
            result['execution'] = execute(scene, observation, chosen['envelope'], destination / 'execution', 'D')
            result['status'] = result['execution']['status']
        else:
            result['reason'] = 'at_least_one_rehearsal_not_clean'
    write(destination / 'result.json', result)
    return result
