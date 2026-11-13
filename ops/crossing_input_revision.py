"""Correct crossing input context crop; retain the original camera and pixels."""
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from beforestep.observation import images as INPUTS
from experimental.crossing.runtime import OUT, write, sha
from experimental.crossing.scene import DEVELOPMENT_SEEDS
from ops.crossing_observe import observe

REVISION = 'scene-dev-v6'


def scene_revision(seed):
    original = OUT / 'development/scene-dev-v5' / f'seed-{seed}'
    folder = OUT / 'development' / REVISION / f'seed-{seed}'
    if (folder / 'scene.json').exists():
        return folder
    scene = copy.deepcopy(json.loads((original / 'scene.json').read_text()))
    folder.mkdir(parents=True, exist_ok=True)
    for name in ['threshold', 'gate-1', 'gate-2']:
        shutil.copytree(original / name, folder / name, dirs_exist_ok=True)
    theta = np.deg2rad(65)
    camera = np.array([3.0 - 1.4 * np.cos(theta), 1.4 * np.sin(theta)])
    scene.update(revision=REVISION, observation_yaw_deg=-65,
                 observation_stop=(camera - .42 * np.array([np.cos(theta), -np.sin(theta)])).tolist(),
                 camera_nominal_distance_m=float(1.4 * np.cos(theta)), camera_to_target_center_xy_m=1.4,
                 truth_mesh=str(folder / 'threshold/truth.obj'))
    scene['spec'].update(name=f'crossing-{REVISION}-{seed}', start=scene['observation_stop'],
                         objects=[{'posed_dir': str(folder / name)} for name in ['threshold', 'gate-1', 'gate-2']])
    scene['input_revision'] = {'source_scene': str(original / 'scene.json'), 'context_pad_frac': .25,
                               'physical_geometry_changed': False, 'new_lux_tasks': 0}
    write(folder / 'scene.json', scene)
    return folder


def derive_existing_preview(folder):
    target = folder / 'observation'
    if (target / 'blindness.json').exists():
        return json.loads((target / 'blindness.json').read_text())
    original = OUT / 'development/input-preview-a65-d1.4/seed-11002/observation'
    shutil.copytree(original, target, dirs_exist_ok=True)
    state = json.loads((target / 'state.json').read_text())
    a = state['crops']['A1']['crop_box']
    # Tight box was uncapped and has 10% padding. Make context 25% with the same centre.
    side = int(round((a[2] - a[0]) / 1.2 * 1.5))
    centre = [(a[0] + a[2]) / 2, (a[1] + a[3]) / 2]
    image = np.asarray(Image.open(original / 'rgb_gen.png'))
    x0 = int(round(centre[0] - side / 2))
    y0 = int(round(centre[1] - side / 2))
    assert 0<=x0 and 0<=y0 and x0+side<=image.shape[1] and y0+side<=image.shape[0]
    box = [x0, y0, x0 + side, y0 + side]
    context = INPUTS._crop_image(image, box, 1536)
    for name, item in state['crops'].items():
        path = target / 'gen/variants' / (name + '.png')
        if name.startswith('C'):
            Image.fromarray(context).save(path)
            item.update(crop_box=box, uploaded_object_height_px=round(state['crop_native_px'] * 1536 / side, 1))
        item.update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    state['input_controls'] = {'context_pad_frac': .25, 'derived_from_real_preview': str(original),
                               'original_tight_pad_frac': .10, 'context_derived_from_uncapped_tight_box': True}
    write(target / 'state.json', state)
    report = json.loads((target / 'blindness.json').read_text())
    report.update(revision=REVISION, upload_ok=all(c['uploaded_object_height_px']>=512 for c in state['crops'].values()))
    write(target / 'blindness.json', report)
    variants = json.loads((target / 'gen/variants/variants.json').read_text())
    variants.update(variants=state['crops'], upload_ok=report['upload_ok'], context_pad_frac=.25)
    write(target / 'gen/variants/variants.json', variants)
    write(target / 'derivation.json', {'source_observation': str(original), 'original_rgb_sha256': sha(original / 'rgb.png'),
                                      'same_rgb': sha(target / 'rgb.png')==sha(original / 'rgb.png'),
                                      'same_depth': sha(target / 'depth.npy')==sha(original / 'depth.npy'),
                                      'same_physical_state': sha(target / 'physical-state.npz')==sha(original / 'physical-state.npz'),
                                      'only_context_crop_changed': True, 'new_lux_tasks': 0})
    return report


if __name__ == '__main__':
    rows = []
    for seed in [11002] + [s for s in DEVELOPMENT_SEEDS if s != 11002]:
        folder = scene_revision(seed)
        report = derive_existing_preview(folder) if seed == 11002 else observe(seed, REVISION, context_pad=.25)
        state = json.loads((folder / 'observation/state.json').read_text())
        rows.append(report)
        print(json.dumps({'seed': seed, 'native_ok': report['native_ok'], 'upload_ok': report['upload_ok'],
                          'unique_inputs': len({c['sha256'] for c in state['crops'].values()})}), flush=True)
    write(ROOT / 'evidence/crossing/development-blindness-scene-dev-v6.json', {'scenes': rows, 'new_lux_tasks': 0})
