"""Zero-paid new camera poses on an unchanged retained physical development fixture."""
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from experimental.crossing.runtime import OUT, write, sha
from ops.crossing_observe import observe


if __name__ == '__main__':
    seed = 11002
    original = OUT / 'development/scene-dev-v5' / f'seed-{seed}'
    base = json.loads((original / 'scene.json').read_text())
    rows = []
    for angle, distance in [(45, 1.4), (65, 1.4), (65, 1.8)]:
        revision = f'input-preview-a{angle}-d{distance:g}'
        folder = OUT / 'development' / revision / f'seed-{seed}'
        if not (folder / 'scene.json').exists():
            scene = copy.deepcopy(base)
            folder.mkdir(parents=True, exist_ok=True)
            for name in ['threshold', 'gate-1', 'gate-2']:
                shutil.copytree(original / name, folder / name, dirs_exist_ok=True)
            scene['revision'] = revision
            scene['observation_yaw_deg'] = -angle
            theta = np.deg2rad(angle)
            camera = np.array([3.0 - distance * np.cos(theta), distance * np.sin(theta)])
            scene['observation_stop'] = (camera - .42 * np.array([np.cos(theta), -np.sin(theta)])).tolist()
            scene['camera_nominal_distance_m'] = distance * np.cos(theta)
            scene['camera_to_target_center_xy_m'] = distance
            scene['truth_mesh'] = str(folder / 'threshold/truth.obj')
            scene['spec']['name'] = f'crossing-{revision}-{seed}'
            scene['spec']['start'] = scene['observation_stop']
            scene['spec']['objects'] = [{'posed_dir': str(folder / name)} for name in ['threshold', 'gate-1', 'gate-2']]
            scene['input_preview'] = {'source_scene': str(original / 'scene.json'), 'new_lux_tasks': 0,
                                      'physical_mesh_sha256': {name: sha(folder / name / 'truth.obj')
                                                               for name in ['threshold', 'gate-1', 'gate-2']},
                                      'purpose': 'View and crop changes only; unchanged fixture geometry.'}
            write(folder / 'scene.json', scene)
        report = observe(seed, revision)
        state = json.loads((folder / 'observation/state.json').read_text())
        row = {'revision': revision, 'seed': seed, 'angle_deg': angle, 'camera_distance_xy_m': distance,
               'native_ok': report['native_ok'], 'upload_ok': report['upload_ok'],
               'native_height_px': report['crop_native_height_px'],
               'distinct_inputs': len({c['sha256'] for c in state['crops'].values()}),
               'classes': {name: {'crop_box': c['crop_box'], 'uploaded_object_height_px': c['uploaded_object_height_px'],
                                  'sha256': c['sha256']} for name, c in state['crops'].items()},
               'blindness': report['tracks'], 'new_lux_tasks': 0}
        rows.append(row)
        print(json.dumps({k: row[k] for k in ['revision', 'native_ok', 'upload_ok', 'native_height_px', 'distinct_inputs']}), flush=True)
    write(ROOT / 'evidence/crossing/diagnosis-input-previews-v1.json', {'new_lux_tasks': 0, 'scenes': rows})
