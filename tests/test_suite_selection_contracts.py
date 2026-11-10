"""Selection uses every pool's pre-Lux classification and the earliest seeds."""
import unittest

from ops.freeze_suite import select


class SelectionTests(unittest.TestCase):
    def test_earliest_seeds_and_anchor_slot_are_preserved(self):
        rows = [{'family': family, 'seed': seed, 'classification': classification}
                for family in ('F0', 'F1') for seed, classification in
                ((8, 'decisive'), (6, 'ordinary'), (2, 'decisive'), (1, 'ordinary'), (5, 'decisive'))]
        chosen = select(rows, ['F0', 'F1'])
        self.assertEqual([(r['family'], r['seed']) for r in chosen],
                         [('F0', 2), ('F0', 1), ('F1', 2), ('F1', 5), ('F1', 1)])

    def test_insufficient_decisive_pool_cannot_be_replaced_by_ordinary_cases(self):
        with self.assertRaises(ValueError):
            select([{'family': 'F2', 'seed': i, 'classification': 'ordinary'} for i in range(1, 13)], ['F2'])
