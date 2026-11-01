import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import weak_order


def adjacent_swap(a, b):
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]]


class Lab(unittest.TestCase):
    def permutohedron_of_4(self):
        elems = weak_order.elements(4)
        covers = weak_order.covers(elems)
        self.assertEqual(len(elems), 24)
        self.assertEqual(len(covers), 36)
        ranks = Counter(weak_order.rank(p) for p in elems)
        self.assertEqual([ranks[k] for k in range(7)], [1, 3, 5, 6, 5, 3, 1])
        bottoms = [x for x in elems if not any(y != x and weak_order.below(y, x) for y in elems)]
        tops = [x for x in elems if not any(y != x and weak_order.below(x, y) for y in elems)]
        self.assertEqual(len(bottoms), 1)
        self.assertEqual(len(tops), 1)
        for a, b in covers:
            self.assertTrue(adjacent_swap(a, b), (a, b))


if __name__ == "__main__":
    unittest.main()
