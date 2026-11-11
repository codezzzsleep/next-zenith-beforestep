import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
from beforestep.generation import client as C
from r3_known_results import complete_known_request


class KnownResultReuseTests(unittest.TestCase):
    def prepare(self, root):
        (root / 'ledger/tasks').mkdir(parents=True)
        (root / 'old.jpg').write_bytes(b'original image bytes')
        (root / 'current.jpg').write_bytes(b'original image bytes')
        (root / 'model.glb').write_bytes(b'glTF opaque test payload')
        request = {'mode': 'img', 'version': 'G1-Turbo', 'faceCount': 30000,
                   'items': [{'id': 'A1', 'path': 'current.jpg', 'sha256': C.sha(root / 'current.jpg')}]}
        path = root / 'outputs/r3/target/lux_request.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(request))
        identity = C.request_identity(request, request['items'][0])
        record = {'id': 'A1', 'identity': identity, 'task_id': 123, 'status': 'ok',
                  'inputs': ['old.jpg'], 'input_sha256': [C.sha(root / 'old.jpg')],
                  'api_field': 'img', 'n_images': 1, 'glb': 'model.glb', 'glb_sha256': C.sha(root / 'model.glb')}
        ledger = root / 'ledger/tasks' / (identity + '.json')
        ledger.write_text(json.dumps(record))
        return path, ledger

    def test_same_image_different_path_reuses_task_and_keeps_original_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(C, 'ROOT', root), patch.object(C, 'LEDGER', root / 'ledger'), \
                    patch.object(C, 'api', side_effect=AssertionError('No network allowed')):
                request, ledger = self.prepare(root)
                original = ledger.read_bytes()
                self.assertTrue(complete_known_request(request))
                result = json.loads((request.parent / 'lux_result.json').read_text())
                self.assertEqual(result['tasks'][0]['task_id'], 123)
                self.assertEqual(result['tasks'][0]['inputs'], ['current.jpg'])
                self.assertEqual(result['tasks'][0]['original_task_inputs'], ['old.jpg'])
                self.assertEqual(ledger.read_bytes(), original)
                self.assertEqual(result['new_tasks_created'], 0)

    def test_unknown_identity_stays_pending_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(C, 'ROOT', root), patch.object(C, 'LEDGER', root / 'ledger'), \
                    patch.object(C, 'api', side_effect=AssertionError('No network allowed')):
                request, ledger = self.prepare(root)
                ledger.unlink()
                self.assertFalse(complete_known_request(request))
                self.assertFalse((request.parent / 'lux_result.json').exists())

    def test_mismatched_recorded_input_digest_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(C, 'ROOT', root), patch.object(C, 'LEDGER', root / 'ledger'), \
                    patch.object(C, 'api', side_effect=AssertionError('No network allowed')):
                request, ledger = self.prepare(root)
                record = json.loads(ledger.read_text()); record['input_sha256'] = ['incorrect']
                ledger.write_text(json.dumps(record))
                with self.assertRaises(ValueError):
                    complete_known_request(request)
                self.assertFalse((request.parent / 'lux_result.json').exists())


if __name__ == '__main__':
    unittest.main()
