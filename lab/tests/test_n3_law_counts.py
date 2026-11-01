import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import n3_law


class Lab(unittest.TestCase):
    def law_counts_match_hand_values(self):
        self.assertEqual(n3_law.count_classes(4, [{0, 1, 2, 3}]), 4)
        self.assertEqual(n3_law.count_classes(3, [{0, 1}, {1, 2}]), 4)
        self.assertEqual(n3_law.count_classes(3, [{0, 1}, {1, 2}, {0, 2}]), 6)
        pairs = [{a, b} for a in range(4) for b in range(a + 1, 4)]
        self.assertEqual(n3_law.count_classes(4, pairs), 24)
        self.assertEqual(n3_law.count_classes(4, []), 1)
        self.assertEqual(n3_law.count_classes(3, [{0, 1, 2}, {0, 1}, {0, 2}]), 5)
        self.assertEqual(n3_law.count_classes(1, [{0}]), 1)
        tickets = [(64, 64), (65, 64), (64, 65), (65, 65)]
        chunks = [(cx, cz) for cx in (64, 65) for cz in (64, 65)]
        family = n3_law.ball_family(tickets, chunks, 3)
        self.assertEqual(family, {frozenset({0, 1, 2, 3})})
        self.assertEqual(n3_law.count_classes(4, family), 4)


if __name__ == "__main__":
    unittest.main()
