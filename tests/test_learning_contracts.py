"""Safety and provenance checks for deployment of the trained controller."""
import json
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from beforestep.learning import checkpoints, ppo
from beforestep.paths import ROOT
from beforestep.learning.policy import apply_action
from beforestep.learning.policy import GoalPolicy, completed
from beforestep.learning.pose import PosePolicy, SCHEMA
from beforestep.pipeline import initialize_recorded_look, recorded_scene_matches


class LearningContracts(unittest.TestCase):
    def test_pose_evidence_keeps_fair_inputs_and_original_capture_tolerances(self):
        proof = json.loads((ROOT/'evidence/learning/observation_pose_v2/validation.json').read_text())
        model = ROOT/'assets/models/observation_pose_v2/pose.npz'
        self.assertEqual(hashlib.sha256(model.read_bytes()).hexdigest(), proof['pose_model_sha256'])
        a = json.loads((ROOT/'evidence/learning/pose_v2_recorded/run_identity.json').read_text())
        b = json.loads((ROOT/'evidence/learning/pose_v2_joint/run_identity.json').read_text())
        self.assertEqual(a['source_sha256'], b['source_sha256'])
        self.assertEqual(a['recorded_initial_state'], b['recorded_initial_state'])
        self.assertEqual(a['controller']['checkpoint_sha256'], b['controller']['checkpoint_sha256'])
        self.assertEqual(proof['trials']['pose_v2_joint']['summary']['result'], 'stopped_short')
        for label in ('pose_v2_live', 'pose_v2_recorded'):
            trial = proof['trials'][label]
            self.assertEqual(trial['summary']['result'], 'arrived')
            self.assertEqual(len(trial['capture_poses']), 3)
            for pose in trial['capture_poses']:
                self.assertLess(pose['position_error_m'], .075)
                self.assertLess(pose['yaw_error_degrees'], 4.)
                self.assertLess(pose['linear_speed_mps'], .035)
                self.assertLess(pose['yaw_rate_rps'], .08)
            folder = ROOT/'evidence/learning'/label
            with np.load(folder/'traj.npz', allow_pickle=False) as trace:
                self.assertIn('learned_pose', trace['control_sources'])
                self.assertNotIn('rules', trace['control_sources'])
            sources = json.loads((folder/'source_manifest.json').read_text())['source_files']
            for source in sources.values():
                self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(), source['sha256'])

    def test_trained_pose_head_has_finite_actions_without_forward_motion(self):
        env = SimpleNamespace(data=SimpleNamespace(qpos=np.array([0., 0., 0., 1., 0., 0., 0.]),
                                                  qvel=np.zeros(6)))
        for version in ('v1', 'v2'):
            policy = PosePolicy(ROOT/f'assets/models/observation_pose_{version}/pose.npz')
            for target in (-2.5, -.1, 0., .1, 2.5):
                action = policy.action(env, target)
                self.assertEqual(action.shape, (4,))
                self.assertTrue(np.isfinite(action).all())
                np.testing.assert_array_equal(action[:3], np.zeros(3))
            self.assertLess(policy.action(env, -.1)[3], -.1)
            self.assertGreater(policy.action(env, .1)[3], .1)

    def test_invalid_pose_weights_are_rejected_before_motor_control(self):
        params = ppo.init_params(np.random.default_rng(0), obs_dim=2, act_dim=4, hidden=8)
        params['W1'][0, 0] = np.nan
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'pose.npz'
            np.savez_compressed(path, **params, schema=np.array(SCHEMA))
            with self.assertRaisesRegex(ValueError, 'invalid dimensions or values'):
                PosePolicy(path)

    def test_terminal_rotation_uses_learned_head_and_recenters_after_drift(self):
        policy = GoalPolicy(ROOT/'assets/models/goal_controller_v4/behavior_cloning.npz')
        policy.pose_policy = Mock()
        policy.pose_policy.action.return_value = np.array([0., 0., 0., .25])
        env = SimpleNamespace(data=SimpleNamespace(qpos=np.array([.024, 0., 0., 1., 0., 0., 0.]),
                                                  qvel=np.zeros(6)), _obs=lambda: np.zeros(35))
        env.data.qvel[0] = .04
        policy.action(env, (0., 0.), .5)
        policy.pose_policy.action.assert_not_called()
        env.data.qvel[0] = 0.
        np.testing.assert_array_equal(policy.action(env, (0., 0.), .5), [0., 0., 0., .25])
        self.assertEqual(env._control_source, 'learned_pose')
        env.data.qpos[0] = .05
        policy.action(env, (0., 0.), .5)
        self.assertEqual(policy.pose_policy.action.call_count, 2)
        env.data.qpos[0] = .061
        with patch('beforestep.learning.policy.observation', return_value=np.zeros(49)) as obs, \
             patch('beforestep.learning.policy.ppo.deterministic_action', return_value=np.array([0., 0., .2, 0.])):
            policy.action(env, (0., 0.), .5)
        self.assertEqual(env._control_source, 'learned')
        self.assertIsNone(obs.call_args.args[2])
        np.testing.assert_allclose(obs.call_args.args[1], [-.04, 0.])
        self.assertEqual(policy.pose_policy.action.call_count, 2)

    def test_rotation_never_relaxes_original_position_or_heading_acceptance(self):
        env = SimpleNamespace(data=SimpleNamespace(qpos=np.array([.08, 0., 0., 1., 0., 0., 0.]),
                                                  qvel=np.zeros(6)))
        self.assertFalse(completed(env, (0., 0.), 0.))
        env.data.qpos[0] = .04
        self.assertFalse(completed(env, (0., 0.), np.radians(5.)))
        env.data.qvel[5] = .09
        self.assertFalse(completed(env, (0., 0.), 0.))
        env.data.qvel[5] = 0.
        self.assertTrue(completed(env, (0., 0.), 0.))

    def test_shipped_live_model_changes_route_and_completes_independent_trials(self):
        proof=json.loads((ROOT/'evidence/scenes/trained_live_gate_001/validation.json').read_text())
        model=ROOT/proof['controller']['path']
        self.assertEqual(hashlib.sha256(model.read_bytes()).hexdigest(),proof['controller']['sha256'])
        ids=set()
        for trial in proof['production_trials']:
            self.assertNotIn(trial['run_id'],ids)
            ids.add(trial['run_id'])
            path=ROOT/trial['trajectory_path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),trial['trajectory_sha256'])
            with np.load(path,allow_pickle=False) as trace:
                self.assertLess(np.linalg.norm(trace['qpos'][-1,:2]-[5.7,-.5]),.075)
                self.assertIn('learned',trace['control_sources'])
                self.assertNotIn('rules',trace['control_sources'])
            events=[json.loads(line) for line in (ROOT/trial['events_path']).read_text().splitlines()]
            panes=[pane for event in events if event['kind']=='rehearsal' for pane in event['panes']]
            self.assertEqual(len(panes),6)
            self.assertTrue(all(p['completed'] and not p['collided'] for p in panes))
            decision=next(event for event in events if event['kind']=='decision_comparison')
            self.assertNotEqual(decision['reference_path'],decision['selected_path'])
            self.assertEqual(events[-1]['result'],'arrived')
        self.assertGreaterEqual(len(ids),2)

    def test_fair_live_comparison_keeps_observation_identity_and_real_failures(self):
        proof=json.loads((ROOT/'evidence/scenes/trained_live_gate_001/validation.json').read_text())
        primary=proof['production_trials'][0]
        comparison={row['label']:row for row in proof['comparisons_and_failures']}
        for label in ('trained_detour_reference_v4','trained_detour_conservative_v4_failed'):
            row=comparison[label]
            self.assertEqual(row['raw_first_observation_sha256'],primary['raw_first_observation_sha256'])
            self.assertEqual(row['summary']['controller_sha256'],primary['summary']['controller_sha256'])
        self.assertEqual(comparison['trained_detour_reference_v4']['summary']['result'],'arrived')
        self.assertEqual(comparison['trained_detour_conservative_v4_failed']['summary']['result'],'stopped_short')
        self.assertEqual(comparison['trained_near_goal_v4_rejected']['summary']['result'],'stuck')

    def test_explicit_goal_variant_never_accepts_changed_scene_geometry(self):
        original={'id':'gate','rocks':{'A':{'x':1.}},'start':[0.,0.],
                  'first_stop':[.5,0.],'goal':[2.,0.]}
        variant={**original,'goal':[1.5,-.4]}
        self.assertFalse(recorded_scene_matches(variant,original))
        self.assertTrue(recorded_scene_matches(variant,original,explicit_goal=True))
        changed={**variant,'rocks':{'A':{'x':1.1}}}
        self.assertFalse(recorded_scene_matches(changed,original,explicit_goal=True))

    def test_complete_checkpoint_preserves_optimizer_randomness_and_next_physics(self):
        from beforestep.learning.train import environment
        params = ppo.init_params(np.random.default_rng(3), obs_dim=49, act_dim=4, hidden=8)
        optimizer = ppo.Adam(params, lr=.0001)
        gradients = {k: np.full_like(v, .001) for k,v in params.items()}
        optimizer.step(params, gradients)
        generator = np.random.default_rng(31)
        env = environment('checkpoint_contract')
        action = np.array([0., 0., .3, .05])
        for _ in range(5):apply_action(env, action)
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary)/'complete.npz'
            checkpoints.save(file, params, params, optimizer, {'action': generator},
                             {'environment': checkpoints.physical_state(env)})
            expected_random = generator.standard_normal(12)
            optimizer.step(params, gradients)
            apply_action(env, action)
            expected_position = env.data.qpos.copy()
            restored, _, restored_optimizer, generators, metadata = checkpoints.load(file)
            np.testing.assert_array_equal(generators['action'].standard_normal(12), expected_random)
            restored_optimizer.step(restored, gradients)
            for key in params:np.testing.assert_array_equal(restored[key], params[key])
            env.restore_state(metadata['environment'])
            apply_action(env, action)
            np.testing.assert_allclose(env.data.qpos, expected_position, atol=1e-12, rtol=0)

    def test_substep_collision_is_reported_even_if_contact_monitor_is_transient(self):
        policy = GoalPolicy.__new__(GoalPolicy)
        policy.action = lambda *args: np.zeros(4)
        env = SimpleNamespace(t=0., terminated=False, truncated=False, last_termination={})
        def step(*args):
            env.t += .002
            env.terminated = True
            env.last_termination = {'reason': 'collision'}
        with patch('beforestep.learning.policy.apply_action', side_effect=step):
            result = policy.reach(env, (1., 0.), on_step=lambda _: False)
        self.assertTrue(result.collision)
        self.assertFalse(result.completed)
        self.assertEqual(env.t, .002)

    def test_changed_recorded_observation_is_rejected_before_state_initialization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root/'looks/look1/T1'
            target.mkdir(parents=True)
            state = {'robot_qpos_world': [0., 0., 0., 1., 0., 0., 0.],
                     't_sim': 1., 'observation_sha256': {'rgb.png': 'incorrect'}}
            (target/'state.json').write_text(json.dumps(state))
            (target/'camera_world.json').write_text(json.dumps({'robot_qpos': state['robot_qpos_world'], 'robot_qvel': [0.]*6}))
            (target/'rgb.png').write_bytes(b'changed')
            env = SimpleNamespace(data=SimpleNamespace(qpos=np.ones(7), qvel=np.ones(6)), t=0.)
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                initialize_recorded_look(env, root)
            np.testing.assert_array_equal(env.data.qpos, np.ones(7))
            self.assertEqual(env.t, 0.)

    def test_camera_and_robot_mismatch_is_rejected_before_initialization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root/'looks/look1/T1'
            target.mkdir(parents=True)
            (target/'state.json').write_text(json.dumps({'robot_qpos_world': [0.]*7, 't_sim': 1., 'observation_sha256': {}}))
            (target/'camera_world.json').write_text(json.dumps({'robot_qpos': [1.]*7, 'robot_qvel': [0.]*6}))
            env = SimpleNamespace(data=SimpleNamespace(qpos=np.ones(7), qvel=np.ones(6)), t=0.)
            with self.assertRaisesRegex(ValueError, 'poses differ'):
                initialize_recorded_look(env, root)
            np.testing.assert_array_equal(env.data.qpos, np.ones(7))


if __name__ == '__main__':
    unittest.main()
