import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import persistence_reduction

SQUARE = [(0,), (1,), (2,), (3,), (0, 1), (1, 2), (2, 3), (0, 3)]
TRIANGLE = [(0,), (1,), (2,), (0, 1), (1, 2), (0, 2), (0, 1, 2)]


class Lab(unittest.TestCase):
    def hollow_square_pairs(self):
        pairs, essential = persistence_reduction.reduce(SQUARE)
        self.assertEqual(sorted(pairs), [(0, 1, 4), (0, 2, 5), (0, 3, 6)])
        self.assertEqual(essential, [(0, 0), (1, 7)])
        _, triangle_essential = persistence_reduction.reduce(TRIANGLE)
        self.assertEqual(triangle_essential, [(0, 0)])


if __name__ == "__main__":
    unittest.main()
