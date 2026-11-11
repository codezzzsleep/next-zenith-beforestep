import unittest
from unittest.mock import patch

import numpy as np
import trimesh

from beforestep import scene as S
from beforestep.navigation import map as N, shadows as SH


class StrictShadowTests(unittest.TestCase):
    def test_known_block_shadow_length_and_direction(self):
        height = np.zeros((120, 40))
        height[20:30, 15:25] = 1
        actual = SH.shadow_from_height(height, np.zeros_like(height), np.array([-1., 0.]), np.tan(np.radians(30)))
        last = np.flatnonzero(actual[:, 20])[-1]
        length = (last - 29) * N.RES
        self.assertLessEqual(abs(length - 1 / np.tan(np.radians(30))), N.RES)
        self.assertFalse(actual[10, 20])

    def test_rendered_light_is_the_only_direction_source(self):
        S.configure('stress_v8')
        toward, tangent = SH.toward_sun()
        light = S.sun_dir()
        np.testing.assert_allclose(toward, -light[:2] / np.linalg.norm(light[:2]))
        self.assertAlmostEqual(tangent, np.tan(np.radians(10)))

    def test_mesh_surface_fills_cell_interiors(self):
        height = np.zeros((30, 30))
        mesh = trimesh.Trimesh(vertices=[[.2,.2,1],[1.2,.2,1],[.2,1.2,1]], faces=[[0,1,2]], process=False)
        SH.add_mesh_height(height, mesh, (0., 0.))
        self.assertEqual(height[10, 10], 1)
        self.assertEqual(height[27, 27], 0)

    def test_only_explained_dark_can_be_opened(self):
        state = np.full((N.NX, N.NY), N.FREE)
        state[20, 20] = N.DARK; state[21, 20] = N.DARK
        state[22, 20] = N.HIDDEN; state[23, 20] = N.UNSEEN
        shadow = np.ones_like(state, bool); shadow[21, 20] = False
        with patch.object(N, 'prior_nogo', return_value=np.zeros_like(state, bool)):
            occ = N.occupancy(state, 'imagination_strict', predicted_shadow=shadow)
        self.assertFalse(occ[20, 20])
        self.assertTrue(occ[21, 20]); self.assertTrue(occ[22, 20]); self.assertTrue(occ[23, 20])

    def test_original_imagination_on_frozen_r1_map_is_identical(self):
        S.configure('stress_v8')
        root = S.ROOT / 'evidence/reviews/beforestep_r1/lux/original_b'
        state = np.load(root / 'decision/look1_state.npy')
        footprint = np.load(root / 'looks/look1/T2/decide/footprint_A2.npy')
        original = (state == N.ROCK) | (state == N.NOGO) | N.prior_nogo() | footprint
        np.testing.assert_array_equal(N.occupancy(state, 'imagination', footprint), original)

    def test_conservative_viewpoint_ranking_keeps_reachable_observations(self):
        from beforestep.strict_pipeline import viewpoint_need
        root = S.ROOT / 'evidence/reviews/beforestep_r3/viewpoint-diagnostic'
        for scene, name in [('suite_r2_v4_F1_020', 'F1-first'), ('stress_v8', 'stress-fourth')]:
            with self.subTest(scene=scene), np.load(root / (name + '.npz')) as fixture:
                S.configure(scene)
                state, pose = fixture['state'], fixture['pose']
                occ = N.occupancy(state, 'conservative', known_free=fixture['known'])
                candidates = N.choose_second_look(state, pose, viewpoint_need(state, pose[0]), occ)
                reachable = [c for c in candidates[:40] if c[4] >= 20 and
                             N.plan(occ, pose, c[:2]) is not None]
                self.assertTrue(reachable, 'The original conservative ranking has a safe reachable observation')


    def test_explained_solar_shadow_allows_a_safe_forward_viewpoint(self):
        from beforestep.strict_pipeline import viewpoint_need
        S.configure('stress_v8')
        path = S.ROOT / 'evidence/reviews/beforestep_r3/viewpoint-diagnostic/strict-motion.npz'
        with np.load(path) as fixture:
            state, pose = fixture['state'], fixture['pose']
            occ = N.occupancy(state, 'imagination_strict', fixture['imagined'], fixture['known'],
                              predicted_shadow=fixture['shadow'])
            need = viewpoint_need(state, pose[0], occupied=occ)
            candidates = N.choose_second_look(state, pose, need, occ)
            reachable = [c for c in candidates[:40] if c[4] >= 20 and N.plan(occ, pose, c[:2]) is not None]
            self.assertTrue(reachable)
            self.assertGreater(reachable[0][0], pose[0] + 1.0)


if __name__ == '__main__':
    unittest.main()
