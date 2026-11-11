"""Counterexamples for rounded look times crossing the intervention boundary."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
from run_r3_counterfactuals import prefix_check


class CounterfactualPrefixTests(unittest.TestCase):
    def fixture(self, root, corrupt_before=False):
        event = {'kind': 'look', 'k': 1, 't': .02, 'measured_pose': [1., 2., 0.]}
        directories = [root / name for name in ('original', 'counterfactual')]
        for index, directory in enumerate(directories):
            target = directory / 'looks/look1/T1'
            target.mkdir(parents=True)
            (target / 'state.json').write_text(json.dumps({
                'look': 'look1', 't_sim': .018, 'robot_qpos_world': [1., 2.]}))
            for suffix in ('rgb.png', 'depth.npy', 'dark.npy', 'state.npy', 'zmax.npy'):
                (directory / 'looks' / ('look1_' + suffix)).write_bytes(b'original observation')
            (directory / 'events.jsonl').write_text(json.dumps(event) + '\n')
            qpos = np.array([[0., 1.], [1., 2.], [2., 3.]])
            phase = np.array(['look1', 'look1', 'execute'])
            source = np.array(['brake', 'brake', 'rules'])
            if index:
                qpos[-1] = [1., 2.]
                phase[-1], source[-1] = 'stuck', 'brake'
                if corrupt_before:
                    qpos[0, 0] += .001
            np.savez(directory / 'traj.npz', t=np.array([.016, .018, .02]), qpos=qpos,
                     phase=phase, control_actions=np.zeros((3, 4)), control_sources=source)
        return directories, [event]

    def test_different_first_post_intervention_step_is_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            (original, actual), events = self.fixture(Path(folder))
            check = prefix_check(original, actual, events, 1, 'T1')
            self.assertTrue(check['passed'])
            self.assertEqual(check['prefix_sample_count'], 2)
            self.assertTrue(check['sensor_qpos_exact'])

    def test_actual_pre_intervention_change_still_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            (original, actual), events = self.fixture(Path(folder), corrupt_before=True)
            check = prefix_check(original, actual, events, 1, 'T1')
            self.assertFalse(check['passed'])
            self.assertFalse(check['arrays_equal']['qpos'])


if __name__ == '__main__':
    unittest.main()
