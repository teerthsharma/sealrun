import sys
import unittest
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import b_permutations


def all_subsets(n):
    return {frozenset(c) for r in range(1, n + 1) for c in combinations(range(1, n + 1), r)}


def intervals(n):
    return {frozenset(range(i, j + 1)) for i in range(1, n + 1) for j in range(i, n + 1)}


class Lab(unittest.TestCase):
    def prefix_rule_counts_24_and_14(self):
        counts = {}
        for n in (3, 4):
            counts[("subsets", n)] = b_permutations.count(n, all_subsets(n))
            counts[("intervals", n)] = b_permutations.count(n, intervals(n))
        for key, value in counts.items():
            print(key, value)
        self.assertEqual(counts[("subsets", 4)], 24)
        self.assertEqual(counts[("intervals", 4)], 14)
        self.assertEqual(counts[("subsets", 3)], 6)
        self.assertEqual(counts[("intervals", 3)], 5)


if __name__ == "__main__":
    unittest.main()
