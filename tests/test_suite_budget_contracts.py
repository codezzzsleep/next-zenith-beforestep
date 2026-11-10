"""No network: paid reservations must precede creation and stop at 360."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops import suite_lux_budget as B


class BudgetTests(unittest.TestCase):
    def fixture(self, root, count):
        path = root / 'budget.json'
        path.write_text(json.dumps({'schema': 'beforestep-r2-paid-budget/v1', 'limit': 360,
            'tasks': {f'old{i}': {'status': 'ok', 'task_id': i + 1, 'new_r2_task': True}
                      for i in range(count)}}))
        return B.Budget(path)

    def test_last_slot_is_durable_before_create_and_next_slot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); budget = self.fixture(root, 359)
            request_path = root / 'request.json'
            request_path.write_text(json.dumps({'mode': 'img', 'items': [{'id': 'A1', 'path': 'image.png', 'sha256': 'test'}]}))
            client_ledger = root / 'client'
            def submit(request, item):
                data = json.loads(budget.path.read_text())
                self.assertEqual(data['tasks']['last']['status'], 'reserved')
                self.assertEqual(B.Budget.usage(data), 360)
                record = {'identity': 'last', 'id': 'A1', 'task_id': 999, 'status': 'pending'}
                B.C.atomic_json(client_ledger / 'tasks/last.json', record)
                return record
            def poll(record, timeout):
                record = {**record, 'status': 'ok'}
                B.C.atomic_json(client_ledger / 'tasks/last.json', record)
                return record
            with patch.object(B.C, 'ROOT', root), patch.object(B.C, 'LEDGER', client_ledger), \
                 patch.object(B.C, 'request_identity', return_value='last'), \
                 patch.object(B.C, 'submit', side_effect=submit) as create, patch.object(B.C, 'poll', side_effect=poll):
                self.assertEqual(B.generate_request(request_path, budget, 'unit_scene')[0]['task_id'], 999)
                create.assert_called_once()
                with self.assertRaises(B.BudgetExhausted):
                    budget.reserve('next', {'scene': 'unit_scene'})

    def test_uncertain_identity_is_queried_without_any_create(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); budget = self.fixture(root, 0)
            request_path = root / 'request.json'
            request_path.write_text(json.dumps({'mode': 'img', 'items': [{'id': 'A1', 'path': 'image.png', 'sha256': 'test'}]}))
            record = {'identity': 'uncertain', 'id': 'A1', 'status': 'uncertain', 'task_id': None}
            ledger = root / 'client'
            B.C.atomic_json(ledger / 'tasks/uncertain.json', record)
            with patch.object(B.C, 'ROOT', root), patch.object(B.C, 'LEDGER', ledger), \
                 patch.object(B.C, 'request_identity', return_value='uncertain'), \
                 patch.object(B.C, 'submit') as create, patch.object(B.C, 'poll', return_value=record) as query:
                with self.assertRaises(B.PendingTask):
                    B.generate_request(request_path, budget, 'unit_scene')
                create.assert_not_called(); query.assert_called_once()
            self.assertEqual(B.Budget.usage(json.loads(budget.path.read_text())), 1)

    def test_definite_no_submission_releases_capacity_without_erasing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); budget = self.fixture(root, 359)
            with patch.object(B.C, 'ROOT', root), patch.object(B.C, 'LEDGER', root / 'client'):
                budget.reserve('rejected', {'scene': 'unit_scene'})
                budget.sync('rejected', {'status': 'not_submitted', 'task_id': None})
                budget.reserve('new', {'scene': 'unit_scene'})
            data = json.loads(budget.path.read_text())
            self.assertIn('rejected', data['tasks'])
            self.assertEqual(B.Budget.usage(data), 360)
