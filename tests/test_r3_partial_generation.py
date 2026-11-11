"""A budget cutoff must settle existing IDs without creating missing samples."""
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
import suite_lux_budget as B
from r3_lux_budget import R3Budget
from r3_partial_results import settle_request
from run_r3_holdouts import first_view_ready
import preserve_suite_scene as P


class PartialGenerationTests(unittest.TestCase):
    def setUp(self):
        timer = patch('r3_lux_budget.datetime')
        clock = timer.start()
        clock.now.return_value = datetime(2026, 11, 11, tzinfo=timezone.utc)
        self.addCleanup(timer.stop)

    def test_request_cutoff_queries_last_created_id_and_keeps_missing_sample_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'image.png').write_bytes(b'fixed observation bytes')
            request = {'mode': 'img', 'items': [
                {'id': name, 'path': 'image.png', 'sha256': B.C.sha(root / 'image.png')}
                for name in ('A1', 'A2')]}
            request_path = root / 'request.json'
            B.C.atomic_json(request_path, request)
            budget_path = root / 'budget.json'
            B.C.atomic_json(budget_path, {'schema': 'beforestep-r3-paid-budget/v1', 'limit': 170,
                'prior_identities': [], 'tasks': {
                    str(i): {'new_r3_task': True, 'task_id': i + 1, 'status': 'ok'} for i in range(169)}})
            client = root / 'client'

            def submit(specification, item):
                record = {'id': item['id'], 'identity': item['id'], 'task_id': 999,
                          'status': 'pending', 'inputs': ['image.png'],
                          'input_sha256': [B.C.sha(root / 'image.png')]}
                B.C.atomic_json(client / 'tasks' / (item['id'] + '.json'), record)
                return record

            def poll(record, timeout):
                glb = root / 'assets/candidates/999/tex_mesh.glb'
                glb.parent.mkdir(parents=True, exist_ok=True)
                glb.write_bytes(b'known provider model bytes')
                value = {**record, 'status': 'ok', 'glb': str(glb.relative_to(root)),
                         'glb_sha256': B.C.sha(glb)}
                B.C.atomic_json(client / 'tasks/A1.json', value)
                return value

            with patch.object(B.C, 'ROOT', root), patch.object(B.C, 'LEDGER', client), \
                 patch.object(B.C, 'request_identity', side_effect=lambda specification, item: item['id']), \
                 patch.object(B.C, 'submit', side_effect=submit) as create, \
                 patch.object(B.C, 'poll', side_effect=poll) as query:
                budget = R3Budget(budget_path)
                with self.assertRaises(B.BudgetExhausted):
                    B.generate_request(request_path, budget, 'unit_scene')
                create.assert_called_once()
                query.assert_not_called()
                create.reset_mock()
                partial = settle_request(request_path, budget, scene='unit_scene')
                create.assert_not_called()
                query.assert_called_once()
                self.assertEqual(partial['missing_item_ids'], ['A2'])
                self.assertEqual([row['task_id'] for row in partial['tasks']], [999])
                self.assertTrue((root / 'lux_result.partial.json').exists())
                self.assertFalse((root / 'lux_result.json').exists())
                final = json.loads(budget_path.read_text())
                self.assertEqual(R3Budget.usage(final), 170)
                self.assertEqual(final['tasks']['A1']['status'], 'ok')
                self.assertFalse((client / 'tasks/A2.json').exists())

    def test_captured_first_observation_does_not_make_unfinished_first_generation_reusable(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary)
            (original / 'looks').mkdir()
            (original / 'looks/look1_state.npy').write_bytes(b'captured sensor state')
            self.assertFalse(first_view_ready(original, {'completed': False, 'pending': {'look': 1}}))
            self.assertTrue(first_view_ready(original, {'completed': False, 'pending': {'look': 2}}))
            self.assertTrue(first_view_ready(original, {'completed': True}))

    def test_partial_provider_model_is_included_in_complete_scene_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'checkout'
            baseline = root / 'outputs/unit_scene/baseline'
            baseline.mkdir(parents=True)
            B.C.atomic_json(baseline / 'summary.json', {'scene_id': 'unit_scene', 'result': 'stuck'})
            B.C.atomic_json(baseline / 'run_identity.json', {'run_id': 'baseline-id'})
            model = root / 'assets/candidates/999/tex_mesh.glb'
            model.parent.mkdir(parents=True)
            model.write_bytes(b'partial but successful provider asset')
            partial = root / 'outputs/unit_scene/imagination/looks/look1/T1/lux_result.partial.json'
            B.C.atomic_json(partial, {'tasks': [{'task_id': 999, 'status': 'ok',
                'glb': str(model.relative_to(root)), 'glb_sha256': B.C.sha(model)}]})
            B.C.atomic_json(root / 'runs.json', {'baseline': str(baseline.relative_to(root))})
            B.C.atomic_json(root / 'extras.json', ['outputs/unit_scene'])
            args = SimpleNamespace(scene='unit_scene', runs='runs.json', extras='extras.json',
                out='evidence/scenes', archive_dir=str(Path(temporary) / 'archives'),
                reuse_public_objects=False)
            with patch.object(P, 'ROOT', root):
                P.preserve(args)
            manifest = json.loads((root / 'evidence/scenes/unit_scene/manifest.json').read_text())
            entries = {row['path']: row for row in manifest['files']}
            self.assertEqual(entries[str(model.relative_to(root))]['sha256'], B.C.sha(model))
            self.assertIn('public_object', entries[str(partial.relative_to(root))])
            with tarfile.open(manifest['complete_archive']['path']) as archive:
                self.assertEqual(archive.extractfile('repo/' + str(model.relative_to(root))).read(), model.read_bytes())
            self.assertFalse((partial.parent / 'lux_result.json').exists())


if __name__ == '__main__':
    unittest.main()
