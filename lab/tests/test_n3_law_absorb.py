import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import n3_law


class Lab(unittest.TestCase):
    def absorb_square_collapses_to_first_ticket(self):
        tickets = [(64, 64), (65, 64), (64, 65), (65, 65)]
        chunks = [(cx, cz) for cx in (64, 65) for cz in (64, 65)]
        family = n3_law.ball_family(tickets, chunks, 3)
        self.assertEqual(n3_law.count_classes(4, family), 4)
        orders = list(itertools.permutations(range(4)))
        agree = 0
        for a, b in itertools.combinations(orders, 2):
            same = n3_law.signature(a, family) == n3_law.signature(b, family)
            self.assertEqual(same, a[0] == b[0], (a, b))
            agree += same
        print(f"agreeing pairs: {agree}/{len(orders) * (len(orders) - 1) // 2}")
        self.assertEqual(agree, 60)


if __name__ == "__main__":
    unittest.main()
