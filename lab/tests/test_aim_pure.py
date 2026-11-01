import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import aim

A = [[0, 0], [1, 0]]
B = [[0, 1], [1, 1]]
C = [[2, 0], [2, 1]]


class Lab(unittest.TestCase):
    def best_order_picks_max_or_says_no_lever(self):
        self.assertEqual(
            aim.best_order([{"order": A, "diamonds": 2}, {"order": B, "diamonds": None}, {"order": C, "diamonds": 4}]),
            {"lever": True, "order": C, "diamonds": 4, "mean": 3.0},
        )
        tied = aim.best_order([{"order": A, "diamonds": 7}, {"order": B, "diamonds": 3}, {"order": C, "diamonds": 7}])
        self.assertEqual(tied["lever"], True)
        self.assertEqual(tied["order"], A)
        self.assertEqual(tied["diamonds"], 7)
        self.assertEqual(
            aim.best_order([{"order": A, "diamonds": 4}, {"order": B, "diamonds": 4}, {"order": C, "diamonds": 4}]),
            {"lever": False, "diamonds": 4, "reason": "all orders equal"},
        )
        self.assertEqual(
            aim.best_order([{"order": A, "diamonds": None}, {"order": B, "diamonds": None}]),
            {"lever": None, "reason": "not run"},
        )


if __name__ == "__main__":
    unittest.main()
