from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
from award_lux_budget import AwardBudget
from r3_lux_budget import ExperimentDeadline
from suite_lux_budget import BudgetExhausted


class AwardBudgetTests(unittest.TestCase):
    def fixture(self, root, prior_r3=120):
        (root / 'tasks').mkdir()
        (root / 'tasks/known.json').write_text(json.dumps({'task_id': 7, 'status': 'ok'}))
        rows = {str(i): {'new_r3_task': True, 'task_id': i + 1, 'status': 'ok'} for i in range(prior_r3)}
        (root / 'r3-budget.json').write_text(json.dumps({'r2_new_tasks': 168, 'tasks': rows}))

    def test_cumulative_cap_counts_reserved_and_uncertain_and_allows_known_query(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            with patch('award_lux_budget.C.LEDGER', root), patch('award_lux_budget.C.ROOT', root):
                budget = AwardBudget(root / 'award.json')
                for i in range(28):
                    budget.reserve('new' + str(i), {})
                budget.sync('new0', {'task_id': None, 'status': 'uncertain'})
                with self.assertRaises(BudgetExhausted):
                    budget.reserve('would-exceed-316', {})
                budget.reserve('known', {}, {'task_id': 7, 'status': 'ok'})
                self.assertEqual(budget.reserve('new0', {})['status'], 'uncertain')
                self.assertEqual(AwardBudget.usage(json.loads(budget.path.read_text())), 28)

    def test_separate_twenty_eight_task_cap_even_with_larger_global_allowance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root, prior_r3=0)
            with patch('award_lux_budget.C.LEDGER', root):
                budget = AwardBudget(root / 'award.json')
                for i in range(28):
                    budget.reserve('new' + str(i), {})
                with self.assertRaises(BudgetExhausted):
                    budget.reserve('task29', {})

    def test_deadline_and_lost_known_identity_block_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            with patch('award_lux_budget.C.LEDGER', root):
                budget = AwardBudget(root / 'award.json')
                with self.assertRaises(RuntimeError):
                    budget.reserve('known', {})
                with patch('award_lux_budget.datetime') as clock:
                    clock.now.return_value = datetime(2026, 11, 18, tzinfo=timezone.utc)
                    budget.reserve('known', {}, {'task_id': 7, 'status': 'ok'})
                    with self.assertRaises(ExperimentDeadline):
                        budget.reserve('late', {})
                self.assertEqual(AwardBudget.usage(json.loads(budget.path.read_text())), 0)


if __name__ == '__main__':
    unittest.main()
