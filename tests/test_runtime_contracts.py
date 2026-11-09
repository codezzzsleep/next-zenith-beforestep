"""Behavioral regressions for collision stop, paid resume and frozen evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from beforestep.generation import client
from beforestep.geometry import admission, registration
from beforestep.navigation import controller
from beforestep.pipeline import Recorder


class MotionTests(unittest.TestCase):
    def env(self):
        env = SimpleNamespace(t=0., control_hz=50, steps=0,
                              data=SimpleNamespace(qpos=np.array([0.,0.,0.,1.,0.,0.,0.])))
        def step_command(**kwargs):
            env.steps += 1; env.t += .02
        env.step_command = step_command
        return env

    def test_contact_during_turn_stops_before_next_step(self):
        env = self.env()
        result = controller.run_waypoints(env, [(0.,1.)], on_step=lambda e:e.steps >= 2)
        self.assertTrue(result.collision); self.assertFalse(result.completed)
        self.assertEqual(env.steps, 2)

    def test_contact_during_drive_does_not_brake_after_contact(self):
        env = self.env()
        error, stopped = controller.drive_to(env, 1.,0.,on_step=lambda e:e.steps>=2)
        self.assertTrue(stopped); self.assertEqual(env.steps,2)
        self.assertGreater(error,.3)

    def test_hold_on_existing_contact_never_advances_physics(self):
        env = self.env(); recorder = Recorder(); recorder.monitor = lambda e:True
        self.assertFalse(recorder.hold(env,'contact',2.))
        self.assertEqual(env.steps,0)

    def test_no_motion_cannot_claim_arrival(self):
        env = self.env()
        with patch.object(controller,'turn_to'), patch.object(controller,'drive_to',return_value=(1.,False)):
            result=controller.run_waypoints(env,[(1.,0.)],final_yaw=None)
        self.assertFalse(result.completed); self.assertFalse(result.collision)


class GenerationTests(unittest.TestCase):
    def test_known_paid_task_is_queried_without_create(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'input.jpg').write_bytes(b'input')
            request={'mode':'img'};item={'id':'A1','path':'input.jpg'}
            with patch.object(client,'ROOT',root), patch.object(client,'LEDGER',root/'ledger'), patch.object(client,'api') as api:
                identity=client.request_identity(request,item)
                client.atomic_json(root/'ledger/tasks'/f'{identity}.json',{'task_id':12,'status':'pending'})
                self.assertEqual(client.submit(request,item)['task_id'],12)
                api.assert_not_called()

    def test_lost_create_response_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'input.jpg').write_bytes(b'input')
            with patch.object(client,'ROOT',root), patch.object(client,'LEDGER',root/'ledger'), patch.object(client,'upload_image',return_value='https://example.org/input'), patch.object(client,'api',side_effect=TimeoutError) as api:
                request={'mode':'img'};item={'id':'A1','path':'input.jpg'}
                with self.assertRaises(TimeoutError):client.submit(request,item)
                record=client.submit(request,item)
                self.assertEqual(record['status'],'uncertain');self.assertIsNone(record['task_id'])
                self.assertEqual(api.call_count,1)

    def test_independent_samples_are_not_deduplicated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'input.jpg').write_bytes(b'input')
            with patch.object(client,'ROOT',root):
                a=client.request_identity({'mode':'img'},{'id':'M1','path':'input.jpg'})
                b=client.request_identity({'mode':'img'},{'id':'M2','path':'input.jpg'})
            self.assertNotEqual(a,b)


class EvidenceTests(unittest.TestCase):
    def test_imagination_import_does_not_replace_shared_registration(self):
        loader=registration.load_observation
        from beforestep.geometry import imagination
        self.assertIs(registration.load_observation,loader)
        obs=imagination.load_observation(client.ROOT/'assets/observations/reference_v8/looks/look2/T2')
        self.assertEqual(obs['care'].shape,obs['mask'].shape)

    def test_nonfinite_metrics_are_rejected(self):
        good={'scale_ratio':1.,'hidden_frac':.7,'shell_contact':.9,'free_intrusion_frac':0.,'contour_iou':.9}
        for key in good:
            for invalid in (float('nan'),float('inf'),None):
                with self.subTest(key=key,invalid=invalid):
                    self.assertFalse(admission.admitted({**good,key:invalid}))

    def test_curated_assets_match_provenance(self):
        manifest=json.loads((client.ROOT/'assets/manifest.json').read_text())
        for entry in manifest['entries']:
            with self.subTest(path=entry['path']):
                self.assertEqual(client.sha(client.ROOT/entry['path']),entry['sha256'])


if __name__=='__main__':unittest.main()
