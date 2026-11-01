import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import squares_plan

CORNERS = [(0, 0), (1, 0), (0, 1), (1, 1)]
SQUARES = [(64, 64), (-64, 64), (64, -64)]
ORDERS = list(itertools.permutations(CORNERS))


def cells(square):
    sx, sz = square
    return {(sx + dx, sz + dz) for dx, dz in CORNERS}


class Lab(unittest.TestCase):
    def test_three_squares_one_boot_per_order(self):
        boots = squares_plan.plan(SQUARES, ORDERS)
        self.assertEqual(len(boots), 24)
        seen = {square: [] for square in SQUARES}
        for boot in boots:
            self.assertEqual(len(boot), 12)
            self.assertEqual(len(set(boot)), 12)
            order = None
            for square in SQUARES:
                seq = [c for c in boot if c in cells(square)]
                self.assertEqual(len(seq), 4)
                this = tuple((cx - square[0], cz - square[1]) for cx, cz in seq)
                if order is None:
                    order = this
                self.assertEqual(this, order)
                seen[square].append(this)
            self.assertIn(order, ORDERS)
        for square in SQUARES:
            self.assertEqual(sorted(seen[square]), sorted(ORDERS))
        self.assertEqual(72 - 24, 48)
        self.assertEqual((72 - 24) * 20, 960)


if __name__ == "__main__":
    unittest.main()
