import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import first_ticket_classes as ftc
from blood import sylvester_fibers as syl
from blood import weak_order as wo


def partition(elems, key):
    groups = {}
    for p in elems:
        groups.setdefault(key(p), set()).add(p)
    return {frozenset(g) for g in groups.values()}


class Lab(unittest.TestCase):
    def fourteen_convex_classes(self):
        n = 4
        perms = list(itertools.permutations(range(n)))
        bst = partition(perms, syl.shape)
        self.assertEqual(len(bst), 14)

        fam = ftc.intervals(n)
        self.assertEqual(ftc.classes(n, fam), 14)

        def sig(p):
            return tuple(next(x for x in p if x in s) for s in fam)

        direct = partition(perms, sig) == bst
        reversed_orders = partition(perms, lambda p: sig(p[::-1])) == bst
        print(f"first-element partition equals BST partition: direct={direct} reversed={reversed_orders}")
        self.assertTrue(direct)
        self.assertFalse(reversed_orders)

        for cls in bst:
            for a in cls:
                for c in cls:
                    if wo.below(a, c):
                        for b in perms:
                            if wo.below(a, b) and wo.below(b, c):
                                self.assertIn(b, cls)


if __name__ == "__main__":
    unittest.main()
