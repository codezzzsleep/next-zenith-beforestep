"""Generate a seeded preregistered pool; never patch an individual scene.

All numeric ranges live in the committed parameter file. A changed range needs
a new revision and a complete regenerated pool, preserving the old revision.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def generate(parameters, family, seed):
    parameters = {**parameters, **parameters.get('family_overrides', {}).get(family, {})}
    rng = np.random.default_rng(np.random.SeedSequence(
        [parameters['rng_version'], int(family[1:]), seed]))

    def uniform(name):
        return round(float(rng.uniform(*parameters[name])), 6)

    def choose(name):
        return str(rng.choice(parameters[name]))

    def rock(asset, x, y, yaw, role=None):
        field = role + '_height_m' if role and role + '_height_m' in parameters else 'height_m'
        return {'rock': asset, 'height': uniform(field), 'x': x, 'y': y, 'yaw': yaw}

    low, high = parameters['family_rock_counts'][family]
    count = int(rng.integers(low, high + 1))
    broad = bool(rng.random() < parameters['broad_layout_probability'])
    front_x, front_y = uniform('front_x_m'), uniform('front_y_m')
    rocks = {'A': rock(choose('front_rocks'), front_x, front_y, uniform('front_yaw_deg'), 'front')}
    if count >= 2:
        rocks['B'] = rock(choose('broad_rocks' if broad else 'compact_rocks'),
                          round(front_x + uniform('back_delta_x_m'), 6),
                          uniform('back_y_m'), uniform('back_yaw_deg'), 'back')
    if count >= 3:
        rocks['C'] = rock(choose('rock_library'), uniform('third_x_m'),
                          uniform('third_y_m'), round(float(rng.uniform(-90, 90)), 6), 'third')
    if count == 4:
        # A non-target scatter rock is behind the first camera and outside the
        # approach lane. Up to three foreground rocks remain observed targets.
        rocks['D'] = rock(choose('rock_library'), 1.3, 1.7, round(float(rng.uniform(-90, 90)), 6))
    craters = []
    if family in ('F2', 'F3'):
        for index in range(int(rng.choice(parameters['crater_counts']))):
            side = 'upper' if index == 0 else 'lower'
            craters.append({'center': [uniform(side + '_crater_x_m'), uniform(side + '_crater_y_m')],
                            'radius': uniform('crater_radius_m'), 'depth': uniform('crater_depth_m')})
    if family == 'F2':
        # Every F2 foreground rock sits along a known crater rim. The angle and
        # rim gap are sampled before any run, without inspecting its outcome.
        order = parameters.get('rim_crater_order', list(range(len(craters))))
        if sorted(order) != list(range(len(craters))):
            raise ValueError('rim_crater_order must be a permutation of the generated craters')
        for index, value in enumerate(rocks.values()):
            crater = craters[order[index % len(order)]]
            angle = np.radians(uniform('rim_angle_deg'))
            distance = crater['radius'] + uniform('rim_gap_m')
            sign_x = -1 if index == 0 else 1
            sign_y = -1 if crater['center'][1] > 0 else 1
            value['x'] = round(crater['center'][0] + sign_x * distance * np.sin(angle), 6)
            value['y'] = round(crater['center'][1] + sign_y * distance * np.cos(angle), 6)
    scene_id = f"suite_{parameters['revision']}_{family}_{seed:03d}"
    scene = {'id': scene_id, 'purpose': 'R2 preregistered candidate pool; classification pending',
             'rocks': rocks, 'start': parameters['start'], 'first_stop': parameters['first_stop'],
             'goal': [uniform('goal_x_m'), uniform('goal_y_m')],
             'terrain': {'type': 'corridor' if family == 'F0' else 'plain',
                         'right_wall': family == 'F0', 'craters': craters},
             'sun': {'elevation_deg': uniform('sun_elevation_deg'),
                     'azimuth_deg': uniform('sun_azimuth_deg')},
             'rehearse_reference': parameters['rehearse_reference'],
             'asset_cache_precision': parameters.get('asset_cache_precision', 'legacy_mm'),
             'suite': {'family': family, 'seed': seed, 'revision': parameters['revision'],
                       'generator_rng': 'numpy PCG64 / SeedSequence(version,family,seed)',
                       'layout': 'broad' if broad else 'compact',
                       'target_rocks': list(rocks)[:3],
                       'note': 'Target labels describe layout intent; production capture uses only observed connected components.'}}
    distance = float(np.linalg.norm(np.array(scene['goal']) - scene['start']))
    assert 8 <= distance <= 12
    assert 1 <= len(scene['suite']['target_rocks']) <= 3
    assert all(.35 <= r['height'] <= .6 for r in rocks.values())
    return scene


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--params', default='config/suite/pool_v1.json')
    parser.add_argument('--family', nargs='+', choices=['F0', 'F1', 'F2', 'F3'])
    parser.add_argument('--seeds', nargs=2, type=int)
    args = parser.parse_args()
    parameter_file = ROOT / args.params
    parameters = json.loads(parameter_file.read_text())
    families = args.family or parameters['families']
    seeds = args.seeds or parameters['seeds']
    if not 1 <= seeds[0] <= seeds[1] <= 24:
        parser.error('Only preregistered seeds 1–24 are allowed')
    entries = []
    for family in families:
        for seed in range(seeds[0], seeds[1] + 1):
            scene = generate(parameters, family, seed)
            for r in scene['rocks'].values():
                if not (ROOT / 'assets/rocks' / r['rock'] / 'h1/body_vis.obj').is_file():
                    raise ValueError('Rock not in existing scan library: ' + r['rock'])
            path = ROOT / 'config/scenes' / (scene['id'] + '.json')
            content = json.dumps(scene, ensure_ascii=False, indent=2) + '\n'
            if path.exists() and path.read_text() != content:
                raise ValueError('Existing scene differs: preserve it and preregister a new whole-pool revision')
            path.write_text(content)
            entries.append({'scene': scene['id'], 'family': family, 'seed': seed,
                            'path': str(path.relative_to(ROOT)),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    out = ROOT / 'evidence/suite/pool' / parameters['revision']
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'schema': 'beforestep-suite-pool-manifest/v1',
                'parameters': args.params, 'parameters_sha256': hashlib.sha256(parameter_file.read_bytes()).hexdigest(),
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'scenes': entries}
    path = out / ('manifest_' + '_'.join(families) + f'_{seeds[0]}_{seeds[1]}.json')
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'manifest': str(path.relative_to(ROOT)), 'scenes': len(entries)}))


if __name__ == '__main__':
    main()
