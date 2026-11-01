import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fibers import Permutohedron, analyse_class, analyse_partition, load_partition  # noqa: E402


class PermutohedronTests(unittest.TestCase):
    def test_k3_cell_counts(self):
        P = Permutohedron(3)
        self.assertEqual((len(P.verts), len(P.edges), len(P.squares), len(P.hexagons)), (6, 6, 0, 1))

    def test_k4_cell_counts_form_a_sphere(self):
        P = Permutohedron(4)
        self.assertEqual((len(P.verts), len(P.edges), len(P.squares), len(P.hexagons)), (24, 36, 6, 8))
        self.assertEqual(len(P.verts) - len(P.edges) + len(P.squares) + len(P.hexagons), 2)


class HandCaseTests(unittest.TestCase):
    def test_one_class_k3_hexagon_is_filled(self):
        P = Permutohedron(3)
        r = analyse_class(P, list(P.verts))
        self.assertEqual((r["b0"], r["b1"], r["b2"]), (1, 0, 0))
        self.assertTrue(r["agree"])
        self.assertTrue(r["convex"])

    def test_first_ticket_split_k3(self):
        P = Permutohedron(3)
        A = [p for p in P.verts if p[0] == 0]
        rest = [p for p in P.verts if p[0] != 0]
        ra = analyse_class(P, A)
        self.assertEqual(ra["b0"], 1)
        self.assertTrue(ra["agree"])
        rr = analyse_class(P, rest)
        self.assertFalse(rr["convex"])

    def test_first_ticket_split_k4(self):
        P = Permutohedron(4)
        part = [[p for p in P.verts if p[0] == a] for a in range(4)]
        res = analyse_partition(P, part)
        self.assertEqual(len(res["classes"]), 4)
        for c in res["classes"]:
            self.assertEqual((c["b0"], c["b1"], c["b2"]), (1, 0, 0))
            self.assertTrue(c["agree"])
            self.assertTrue(c["convex"])
            self.assertEqual(c["boundary_swaps"], [0])
            self.assertEqual(c["boundary_edges"], 6)
        self.assertEqual(res["cross_class_edges"], 12)

    def test_identity_and_reverse_class_is_disconnected_and_not_convex(self):
        P = Permutohedron(3)
        r = analyse_class(P, [(0, 1, 2), (2, 1, 0)])
        self.assertEqual(r["b0"], 2)
        self.assertFalse(r["convex"])
        self.assertTrue(r["agree"])

    def test_whole_k4_is_a_sphere_so_b2_is_not_zero(self):
        P = Permutohedron(4)
        r = analyse_class(P, list(P.verts))
        self.assertEqual((r["b0"], r["b1"], r["b2"]), (1, 0, 1))
        self.assertTrue(r["agree"])

    def test_k4_minus_two_antipodal_vertices_is_an_annulus(self):
        P = Permutohedron(4)
        C = [p for p in P.verts if p not in [(0, 1, 2, 3), (3, 2, 1, 0)]]
        r = analyse_class(P, C)
        self.assertEqual((r["b0"], r["b1"], r["b2"]), (1, 1, 0))
        self.assertTrue(r["agree"])


class LoaderTests(unittest.TestCase):
    def test_load_partition_maps_tickets_to_orders(self):
        rec = {
            "k": 3,
            "tickets": [[64, 64], [69, 64], [74, 64]],
            "classes": [
                [[[64, 64], [69, 64], [74, 64]], [[69, 64], [64, 64], [74, 64]]],
                [[[74, 64], [69, 64], [64, 64]]],
            ],
        }
        k, classes = load_partition(rec)
        self.assertEqual(k, 3)
        self.assertEqual(classes, [[(0, 1, 2), (1, 0, 2)], [(2, 1, 0)]])


if __name__ == "__main__":
    unittest.main()
