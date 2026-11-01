import unittest

import polytope as P


class PolytopeTests(unittest.TestCase):
    def test_one_ticket_gives_one_class_and_one_vertex(self):
        F = {frozenset({0})}
        self.assertEqual(len(P.classes_by_min([(0, 0)], F)), 1)
        self.assertEqual(P.vertices(F, 1), 1)

    def test_two_tickets_covering_everything_give_a_segment(self):
        F = {frozenset({0, 1})}
        self.assertEqual(len(P.classes_by_min([(0, 0), (1, 0)], F)), 2)
        self.assertEqual(P.vertices(F, 2), 2)

    def test_path_p3_gives_four(self):
        F = {frozenset({0, 1}), frozenset({1, 2})}
        tickets = [(0, 0), (1, 0), (2, 0)]
        self.assertEqual(len(P.classes_by_min(tickets, F)), 4)
        self.assertEqual(P.vertices(F, 3), 4)

    def test_triangle_k3_gives_six(self):
        F = {frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})}
        tickets = [(0, 0), (1, 0), (0, 1)]
        self.assertEqual(len(P.classes_by_min(tickets, F)), 6)
        self.assertEqual(P.vertices(F, 3), 6)

    def test_full_set_of_four_is_a_simplex(self):
        F = {frozenset({0, 1, 2, 3})}
        tickets = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.assertEqual(len(P.classes_by_min(tickets, F)), 4)
        self.assertEqual(P.vertices(F, 4), 4)

    def test_points_match_classes_on_k3(self):
        F = {frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})}
        tickets = [(0, 0), (1, 0), (0, 1)]
        self.assertEqual(len(P.vertex_points(F, 3)), 6)

    def test_family_from_window(self):
        tickets = [(64, 64), (69, 64)]
        window = P.rect(62, 62, 72, 66)
        F = P.family(tickets, window, 2)
        self.assertEqual(F, {frozenset({0}), frozenset({1})})

    def test_family_skips_uncovered_chunks(self):
        tickets = [(64, 64)]
        window = P.rect(60, 60, 61, 61)
        self.assertEqual(P.family(tickets, window, 2), set())


if __name__ == "__main__":
    unittest.main()
