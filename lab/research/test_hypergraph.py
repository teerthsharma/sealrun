import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hypergraph as H  # noqa: E402

PERMS = list(itertools.permutations(range(3)))
ALL = frozenset(range(3))


class Hypergraph(unittest.TestCase):
    def test_sha_from_first_ticket_overall_needs_all_tickets(self):
        shas = [o[0] for o in PERMS]
        self.assertEqual(H.minimal(PERMS, shas, 3), [ALL])

    def test_constant_chunk_fits_every_singleton(self):
        shas = ["x"] * 6
        self.assertTrue(H.is_constant(shas))
        self.assertEqual(H.minimal(PERMS, shas, 3), [frozenset({0}), frozenset({1}), frozenset({2})])

    def test_sha_from_order_of_tickets_0_and_1_gives_pair(self):
        shas = [o.index(0) < o.index(1) for o in PERMS]
        self.assertEqual(H.minimal(PERMS, shas, 3), [frozenset({0, 1})])

    def test_sha_from_last_ticket_fits_no_set(self):
        shas = [o[-1] for o in PERMS]
        self.assertEqual(H.fitting_sets(PERMS, shas, 3), [])

    def test_chebyshev_ball_and_ball_test(self):
        tickets = [(0, 0), (3, 0), (0, 4)]
        self.assertEqual(H.ball((0, 0), tickets, 3), frozenset({0, 1}))
        self.assertEqual(H.ball((0, 0), tickets, 4), ALL)
        self.assertTrue(H.is_ball(frozenset({0, 1}), (0, 0), tickets))
        self.assertFalse(H.is_ball(frozenset({0, 2}), (0, 0), tickets))

    def test_repeat_control_flags_same_order_different_sha(self):
        order = [[0, 0], [1, 0]]
        same = [{"order": order, "chunks": {"5,5": {"sha256": "a"}}}] * 2
        diff = [{"order": order, "chunks": {"5,5": {"sha256": "a"}}},
                {"order": order, "chunks": {"5,5": {"sha256": "b"}}}]
        self.assertEqual(H.repeat_mismatches(same), [])
        self.assertEqual(len(H.repeat_mismatches(diff)), 1)


if __name__ == "__main__":
    unittest.main()
