import unittest

from ticketfield import (
    chi_at_minus_one,
    classes,
    full_set,
    level,
    rect,
)


class LevelTests(unittest.TestCase):
    def test_level_is_31_plus_min_chebyshev(self):
        self.assertEqual(level((65, 64), [(64, 64)]), 32)
        self.assertEqual(level((64, 64), [(64, 64), (70, 64)]), 31)

    def test_full_set_is_chebyshev_ball_of_radius_two(self):
        f = full_set([(64, 64)])
        self.assertIn((66, 66), f)
        self.assertNotIn((67, 64), f)
        self.assertEqual(len(f), 25)


class ClassTests(unittest.TestCase):
    def test_far_tickets_have_one_class(self):
        W = rect(0, 1, 0, 1)
        self.assertEqual(len(classes([(0, 0), (100, 100)], W, r_dec=2)), 1)

    def test_adjacent_tickets_have_two_classes(self):
        W = rect(64, 65, 64, 65)
        self.assertEqual(len(classes([(64, 64), (65, 64)], W, r_dec=2)), 2)

    def test_e0_square_reproduces_four_classes(self):
        tickets = [(64, 64), (65, 64), (64, 65), (65, 65)]
        W = rect(64, 65, 64, 65)
        self.assertEqual(len(classes(tickets, W, r_dec=2)), 4)
        self.assertEqual(len(classes(tickets, W, r_dec=3)), 4)


class ChromaticTests(unittest.TestCase):
    def test_path_p3_has_four_acyclic_orientations(self):
        self.assertEqual(chi_at_minus_one([0, 1, 2], [(0, 1), (1, 2)]), 4)

    def test_triangle_has_six(self):
        self.assertEqual(chi_at_minus_one([0, 1, 2], [(0, 1), (1, 2), (0, 2)]), 6)

    def test_k4_has_twentyfour(self):
        V = [0, 1, 2, 3]
        E = [(a, b) for a in V for b in V if a < b]
        self.assertEqual(chi_at_minus_one(V, E), 24)


if __name__ == "__main__":
    unittest.main()
