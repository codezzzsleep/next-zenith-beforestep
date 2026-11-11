import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
from r3_lux_budget import R3Budget
from suite_lux_budget import BudgetExhausted


class R3BudgetTests(unittest.TestCase):
    def test_hard_cap_reserves_uncertain_and_recovers_existing_tasks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'tasks').mkdir()
            (root / 'tasks/prior.json').write_text(json.dumps({'task_id': 'old', 'status': 'ok'}))
            with patch('r3_lux_budget.C.LEDGER', root), patch('r3_lux_budget.C.ROOT', root):
                budget = R3Budget(root / 'r3.json')
                budget.reserve('prior', {}, {'task_id': 'old', 'status': 'ok'})
                for index in range(170):
                    budget.reserve(str(index), {})
                budget.sync('0', {'status': 'uncertain', 'task_id': None})
                with self.assertRaises(BudgetExhausted):
                    budget.reserve('extra', {})
                # Recovery of a reserved slot or its known cloud ID remains legal.
                budget.reserve('1', {})
                budget.reserve('2', {}, {'task_id': 'new-known', 'status': 'running'})
                self.assertEqual(budget.reserve('0', {})['status'], 'uncertain')
                data = json.loads((root / 'r3.json').read_text())
                self.assertEqual(R3Budget.usage(data), 170)
                self.assertFalse(data['tasks']['prior']['new_r3_task'])

    def test_prior_identity_is_never_recreated_when_client_record_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'tasks').mkdir()
            (root / 'tasks/prior.json').write_text(json.dumps({'task_id': 'old', 'status': 'ok'}))
            with patch('r3_lux_budget.C.LEDGER', root):
                budget = R3Budget(root / 'r3.json')
                with self.assertRaises(RuntimeError):
                    budget.reserve('prior', {})


if __name__ == '__main__':
    unittest.main()
