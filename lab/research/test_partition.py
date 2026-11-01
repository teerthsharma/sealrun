import itertools
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partition as P

SQ = [[0, 0], [1, 0], [0, 1], [1, 1]]


def world(order, **shas):
    return {"order": order, "chunks": {k: {"sha": v} for k, v in shas.items()}}


class Hand(unittest.TestCase):
    def test_three_orders_two_equal_give_two_classes(self):
        o1 = [[0, 0], [1, 0]]
        o2 = [[1, 0], [0, 0]]
        o3 = [[0, 0], [0, 1]]
        worlds = [
            world(o1, **{"0,0": "a", "1,0": "b"}),
            world(o2, **{"0,0": "a", "1,0": "b"}),
            world(o3, **{"0,0": "a", "1,0": "c"}),
        ]
        r = P.partition(worlds)
        self.assertEqual(r["n_orders"], 3)
        self.assertEqual(r["n_classes"], 2)
        self.assertTrue(r["valid_partition"])

    def test_per_chunk_partition_is_coarser_and_whole_world_refines_it(self):
        orders = [[[0, 0], [1, 0]], [[1, 0], [0, 0]], [[0, 0], [0, 1]], [[0, 1], [0, 0]]]
        shas = [("x", "a", "c"), ("x", "a", "d"), ("x", "b", "c"), ("x", "b", "d")]
        worlds = [world(o, **{"0,0": s[0], "1,0": s[1], "0,1": s[2]}) for o, s in zip(orders, shas)]
        whole = P.partition(worlds)
        per = P.per_chunk(worlds)
        self.assertEqual(whole["n_classes"], 4)
        self.assertEqual(per["0,0"]["n_classes"], 1)
        self.assertEqual(per["1,0"]["n_classes"], 2)
        self.assertEqual(per["0,1"]["n_classes"], 2)
        self.assertEqual(P.refinement_violations(whole, per), 0)

    def test_bits_lost_24_orders_4_classes_is_log2_6(self):
        worlds = []
        for order in itertools.permutations(SQ):
            first = order[0]
            worlds.append(world([list(c) for c in order], **{"0,0": str(first)}))
        r = P.partition(worlds)
        self.assertEqual(r["n_orders"], 24)
        self.assertEqual(r["n_classes"], 4)
        self.assertAlmostEqual(r["bits_lost"], math.log2(6), places=12)

    def test_transitivity_violation_is_detected(self):
        orders = [[[0, 0]], [[1, 0]], [[0, 1]]]
        bad = [[0, 0, 5], [0, 0, 0], [5, 0, 0]]
        good = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.assertEqual(P.transitivity(orders, bad)["violating_triples"], 2)
        self.assertEqual(P.transitivity(orders, good)["violating_triples"], 0)

    def test_asymmetric_matrix_is_reported(self):
        orders = [[[0, 0]], [[1, 0]]]
        r = P.transitivity(orders, [[0, 3], [0, 0]])
        self.assertEqual(r["symmetry_violations"], 1)

    def test_missing_predictions_refuse_instead_of_matching(self):
        r = P.compare_predictions("square", 4, None, Path("/nonexistent/quotient_predictions.json"))
        self.assertEqual(r["status"], "predictions_missing")
        self.assertIsNone(r.get("match"))

    def test_predictions_match_and_mismatch_per_layout(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pred.json"
            p.write_text(json.dumps({"layouts": {"square": {"classes": 4}, "line": {"classes": 2}}}))
            self.assertTrue(P.compare_predictions("square", 4, None, p)["match"])
            self.assertFalse(P.compare_predictions("line", 3, None, p)["match"])
            self.assertEqual(P.compare_predictions("nope", 1, None, p)["status"], "no_prediction")

    def test_repeat_conflict_breaks_partition_validity(self):
        worlds = [world([[0, 0]], **{"0,0": "a"}), world([[0, 0]], **{"0,0": "b"})]
        r = P.partition(worlds)
        self.assertEqual(r["conflicted_orders"], 1)
        self.assertFalse(r["valid_partition"])

    def test_round2_square_uses_only_measured_rows(self):
        doc = {"rows": [
            {"order": [[0, 0], [1, 0]], "measured": True, "differing_blocks": 0, "ores": {"0,0": {"iron": 1}, "1,0": {"iron": 2}}},
            {"order": [[1, 0], [0, 0]], "measured": True, "differing_blocks": 30, "ores": {"0,0": {"iron": 3}, "1,0": {"iron": 4}}},
            {"order": [[0, 0], [1, 0]], "measured": False, "differing_blocks": 0, "inferred_from": "n2-F6", "ores": {"0,0": {"iron": 9}, "1,0": {"iron": 9}}},
        ]}
        worlds, meta = P.from_round2(doc, "order_square.json")
        self.assertEqual(len(worlds), 2)
        self.assertEqual(meta["excluded_inferred"], 1)
        self.assertEqual(P.partition(worlds)["n_classes"], 2)

    def test_round2_square_diff_count_separates_ore_identical_worlds(self):
        ores = {"0,0": {"iron": 1}, "1,0": {"iron": 2}}
        doc = {"rows": [
            {"order": [[0, 0], [1, 0]], "measured": True, "differing_blocks": 0, "ores": ores},
            {"order": [[1, 0], [0, 0]], "measured": True, "differing_blocks": 30, "ores": ores},
        ]}
        worlds, _ = P.from_round2(doc, "order_square.json")
        self.assertEqual(P.partition(worlds)["n_classes"], 2)

    def test_round2_collapse_maps_fingerprints_positionally(self):
        doc = {"orders": [[[0, 0], [1, 0]], [[1, 0], [0, 0]]], "fingerprints": ["f", "f", "f"]}
        worlds, meta = P.from_round2(doc, "order_collapse.json")
        self.assertEqual(meta["unmapped_fingerprints"], 1)
        r = P.partition(worlds)
        self.assertEqual(r["n_classes"], 1)
        self.assertAlmostEqual(r["bits_lost"], 1.0, places=12)

    def test_append_result_replaces_same_experiment(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "partitions.json"
            P.append_result(out, {"experiment": "E1", "n_classes": 1})
            P.append_result(out, {"experiment": "E1", "n_classes": 2})
            runs = json.loads(out.read_text())["runs"]
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["n_classes"], 2)


if __name__ == "__main__":
    unittest.main()
