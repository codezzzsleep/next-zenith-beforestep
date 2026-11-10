"""Configured terrain must preserve frozen scenes and known crater exclusions."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from beforestep import scene as S
from beforestep.navigation import map as N


class SuiteSceneTests(unittest.TestCase):
    def setUp(self):
        self.previous = S.SCENE_ID
        self.legacy = json.loads((S.ROOT / 'config/scenes/stress_v8.json').read_text())
        S.configure('stress_v8')

    def tearDown(self):
        S.configure(self.previous)

    def select(self, **fields):
        definition = {**copy.deepcopy(self.legacy), **fields, 'id': 'unit_suite'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config/scenes').mkdir(parents=True)
            (root / 'config/scenes/unit_suite.json').write_text(json.dumps(definition))
            with patch.object(S, 'ROOT', root):
                return S.configure('unit_suite')

    def test_legacy_height_and_prior_are_exact(self):
        actual = S.height_map()
        frozen = S.ROOT / 'tests/fixtures/r1_terrain.npz'
        manifest = json.loads(frozen.with_suffix('.json').read_text())
        self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(), manifest['height_array_sha256'])
        np.testing.assert_array_equal(actual, np.load(frozen)['height'])
        np.testing.assert_array_equal(N.prior_nogo(),
            (N.GY > S.rille_edge(N.GX) - .05) | (N.GY < S.WALL['y_inner']))
        self.assertEqual(S.terrain_cache_name(), 'stress_v8_terrain_vis.obj')

    def test_plain_removes_corridor_and_wall(self):
        self.select(terrain={'type': 'plain', 'right_wall': False})
        self.assertFalse(N.prior_nogo().any())
        np.testing.assert_array_equal(S.height_map(), np.zeros((S.NGRID, S.NGRID)))
        with patch.object(S, 'rock_asset_uniform', return_value=('unused.obj', 'unused.png')):
            spec, _, meta = S.scene_spec(Path(tempfile.gettempdir()) / 'beforestep-suite-unit-world')
        self.assertEqual(len(spec['objects']), len(self.legacy['rocks']))
        self.assertEqual(meta['walls'], [])

    def test_crater_depth_rim_and_prior_apply_to_every_policy(self):
        crater = {'center': [5., .2], 'radius': .8, 'depth': .6}
        self.select(terrain={'type': 'plain', 'right_wall': False, 'craters': [crater]})
        height = S.height_at(np.array([5., 5.8, 5.9]), np.array([.2, .2, .2]))
        np.testing.assert_allclose(height, [-.6, 0., 0.], atol=1e-12)
        expected = (N.GX - 5.) ** 2 + (N.GY - .2) ** 2 <= .85 ** 2
        np.testing.assert_array_equal(N.prior_nogo(), expected)
        state = np.full(N.GX.shape, N.FREE, np.int8)
        for policy in ('optimistic', 'conservative', 'imagination'):
            np.testing.assert_array_equal(N.occupancy(state, policy), expected)

    def test_reconfigure_restores_sun_and_terrain_defaults(self):
        self.select(terrain={'type': 'plain', 'right_wall': False},
                    sun={'elevation_deg': 6., 'azimuth_deg': -80.})
        changed = S.sun_dir().copy()
        S.configure('stress_v8')
        self.assertEqual(S.TERRAIN, S.DEFAULT_TERRAIN)
        self.assertEqual((S.SUN_EL_DEG, S.SUN_AZ_DEG), (10., 35.))
        self.assertFalse(np.allclose(changed, S.sun_dir()))
        self.assertFalse(S.REHEARSE_REFERENCE)

    def test_recorded_identity_rejects_different_terrain_or_sun(self):
        from beforestep.pipeline import recorded_scene_matches
        for field in ({'terrain': {'type': 'plain'}}, {'sun': {'azimuth_deg': 55.}}):
            self.assertFalse(recorded_scene_matches(self.legacy, {**self.legacy, **field}))
        explicit_defaults = {**self.legacy, 'terrain': S.DEFAULT_TERRAIN, 'sun': S.DEFAULT_SUN}
        self.assertTrue(recorded_scene_matches(self.legacy, explicit_defaults))

    def test_same_named_terrain_revision_cannot_hit_old_visual_cache(self):
        self.select(terrain={'type': 'plain', 'right_wall': False})
        first = S.terrain_cache_name()
        self.select(terrain={'type': 'plain', 'right_wall': False,
                             'craters': [{'center': [6., 0.], 'radius': .8, 'depth': .4}]})
        self.assertNotEqual(first, S.terrain_cache_name())

    def test_invalid_configuration_cannot_mutate_active_scene(self):
        for fields in ({'terrain': {'type': 'ocean'}}, {'terrain': {'right_wall': 1}},
                       {'terrain': {'craters': [{'center': [0., 0.], 'radius': -1., 'depth': .5}]}},
                       {'sun': {'elevation_deg': 0.}}, {'sun': {'azimuth_deg': float('nan')}},
                       {'rehearse_reference': 'yes'}):
            with self.assertRaises(ValueError):
                self.select(**fields)
            self.assertEqual(S.SCENE_ID, 'stress_v8')
            self.assertEqual(S.TERRAIN, S.DEFAULT_TERRAIN)


class PoolGeneratorTests(unittest.TestCase):
    def test_seeded_pool_is_reproducible_and_respects_preregistered_ranges(self):
        from ops.generate_suite_pool import generate
        parameters = json.loads((S.ROOT / 'config/suite/pool_v1.json').read_text())
        seen = set()
        for family in parameters['families']:
            for seed in range(1, 25):
                scene = generate(parameters, family, seed)
                self.assertEqual(scene, generate(parameters, family, seed))
                self.assertNotIn(scene['id'], seen)
                seen.add(scene['id'])
                distance = np.linalg.norm(np.array(scene['goal']) - scene['start'])
                self.assertTrue(8 <= distance <= 12)
                self.assertTrue(1 <= len(scene['suite']['target_rocks']) <= 3)
                self.assertTrue(5 <= scene['sun']['elevation_deg'] <= 12)
                self.assertTrue(all(.35 <= r['height'] <= .6 for r in scene['rocks'].values()))
                self.assertTrue(all(r['rock'] in parameters['rock_library'] for r in scene['rocks'].values()))
                self.assertEqual(bool(scene['terrain']['craters']), family in ('F2', 'F3'))
                self.assertEqual(scene['terrain']['right_wall'], family == 'F0')

    def test_f2_rocks_are_placed_at_crater_rims_before_classification(self):
        from ops.generate_suite_pool import generate
        parameters = json.loads((S.ROOT / 'config/suite/pool_v1.json').read_text())
        for seed in range(1, 25):
            scene = generate(parameters, 'F2', seed)
            craters = scene['terrain']['craters']
            for index, value in enumerate(scene['rocks'].values()):
                crater = craters[index % len(craters)]
                distance = np.linalg.norm(np.array([value['x'], value['y']]) - crater['center'])
                self.assertTrue(.149999 <= distance - crater['radius'] <= .350001)


class PoolClassificationTests(unittest.TestCase):
    def runs(self, truth='arrived', optimistic='collision', conservative='stuck', looks=5):
        return {name: {'exit_code': 0, 'summary': {'result': result, 'looks': count, 'collision':
                    {'body': 'obstacle'} if result == 'collision' else None}}
                for name, result, count in [('truth', truth, 1), ('optimistic', optimistic, 1),
                                            ('conservative', conservative, looks), ('see_dark', 'arrived', 3)]}

    def test_truth_failure_is_unsolvable_even_if_other_results_match(self):
        from ops.run_suite_pool import classify
        self.assertEqual(classify(self.runs(truth='stuck')), 'unsolvable')
        self.assertEqual(classify(self.runs()), 'decisive')

    def test_ordinary_and_unmatched_cases_do_not_broaden_decisive_definition(self):
        from ops.run_suite_pool import classify
        self.assertEqual(classify(self.runs(optimistic='arrived')), 'ordinary')
        self.assertEqual(classify(self.runs(conservative='arrived', looks=3)), 'unclassified')
        self.assertEqual(classify(self.runs(conservative='collision')), 'unclassified')

    def test_failed_process_cannot_be_classified_as_physical_no_solution(self):
        from ops.run_suite_pool import classify
        runs = self.runs(); runs['truth']['exit_code'] = 1
        self.assertEqual(classify(runs), 'incomplete')

