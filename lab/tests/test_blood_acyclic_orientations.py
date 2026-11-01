import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import acyclic_orientations

GRAPHS = {
    "triangle": (3, [(0, 1), (1, 2), (0, 2)], 6),
    "path_4": (4, [(0, 1), (1, 2), (2, 3)], 8),
    "cycle_4": (4, [(0, 1), (1, 2), (2, 3), (3, 0)], 14),
    "complete_4": (4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)], 24),
}


class Lab(unittest.TestCase):
    def stanley_equals_chromatic_at_minus_one(self):
        for name, (n, edges, expected) in GRAPHS.items():
            with self.subTest(graph=name):
                count = acyclic_orientations.acyclic_count(n, edges)
                chrom = acyclic_orientations.chromatic_at(n, edges, -1)
                self.assertEqual(count, expected)
                self.assertEqual(abs(chrom), expected)
                self.assertEqual(count, abs(chrom))


if __name__ == "__main__":
    unittest.main()
