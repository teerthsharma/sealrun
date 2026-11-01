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
LINE = [[0, 0], [1, 0], [2, 0], [3, 0]]


def world(order, **shas):
    return {"order": order, "chunks": {k: {"sha": v} for k, v in shas.items()}}


def cworld(order, label, shas, ores=None):
    chunks = {}
    for k, s in shas.items():
        c = {"sha256": s}
        if ores is not None:
            c["ores"] = ores[k]
        chunks[k] = c
    return {"order": order, "chunks": chunks, "label": label}


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


class Campaign(unittest.TestCase):
    def test_sha256_key_is_the_campaign_hash(self):
        worlds = [cworld([[0, 0], [1, 0]], "a", {"0,0": "x"}),
                  cworld([[1, 0], [0, 0]], "b", {"0,0": "y"})]
        self.assertEqual(P.partition(worlds)["n_classes"], 2)

    def test_single_world_file_and_list_file_load(self):
        with tempfile.TemporaryDirectory() as d:
            single = Path(d) / "w1.json"
            single.write_text(json.dumps({"order": [[0, 0]], "window": "0,0,0,0",
                                          "chunks": {"0,0": {"sha256": "a", "none": 0}}}))
            lst = Path(d) / "l.json"
            lst.write_text(json.dumps([{"order": [[0, 0]], "chunks": {"0,0": {"sha256": "a"}}},
                                       {"order": [[1, 0]], "chunks": {"0,0": {"sha256": "b"}}}]))
            ws, _ = P.load_worlds([single])
            self.assertEqual(len(ws), 1)
            self.assertEqual(ws[0]["label"], "w1")
            ws, _ = P.load_worlds([lst])
            self.assertEqual(len(ws), 2)


class Shape(unittest.TestCase):
    def test_square_and_line_shapes(self):
        self.assertEqual(P.shape(SQ), ("square", 1))
        self.assertEqual(P.shape(LINE), ("line4", 1))
        self.assertEqual(P.shape([[0, 0], [2, 0], [4, 0], [6, 0]]), ("line4", 2))
        self.assertIsNone(P.shape([[0, 0], [5, 0], [1, 3], [2, 2]]))


class Predictions(unittest.TestCase):
    def sim_file(self, d, tickets, r_dec, orders_considered, predicted, classes):
        p = Path(d) / "sim.json"
        p.write_text(json.dumps({"records": [{"layout": "E0", "r_dec": r_dec, "tickets": tickets,
                                              "orders_considered": orders_considered,
                                              "predicted_classes": predicted, "classes": classes}]}))
        return p

    def two_orders(self):
        return [world([[0, 0], [1, 0]], **{"0,0": "a"}), world([[1, 0], [0, 0]], **{"0,0": "b"})]

    def sim_of(self, p, worlds, r_dec):
        return {e["source"]: e for e in P.predictions(P.partition(worlds), [[0, 0], [1, 0]], r_dec, p,
                                                      Path("/nonexistent/quotient_polytope.json"))}

    def test_partial_coverage_gives_no_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.sim_file(d, [[0, 0], [1, 0]], 2, 2, 2, [[[[0, 0], [1, 0]]], [[[1, 0], [0, 0]]]])
            e = self.sim_of(p, self.two_orders()[:1], 2)["sim"]
            self.assertEqual(e["status"], "partial_coverage")
            self.assertIsNone(e["match"])

    def test_full_coverage_matches_count_and_partition(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.sim_file(d, [[0, 0], [1, 0]], 2, 2, 2, [[[[0, 0], [1, 0]]], [[[1, 0], [0, 0]]]])
            e = self.sim_of(p, self.two_orders(), 2)["sim"]
            self.assertEqual(e["status"], "compared")
            self.assertTrue(e["match"])
            self.assertTrue(e["partition_match"])

    def test_wrong_prediction_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.sim_file(d, [[0, 0], [1, 0]], 2, 2, 1, [[[[0, 0], [1, 0]], [[1, 0], [0, 0]]]])
            e = self.sim_of(p, self.two_orders(), 2)["sim"]
            self.assertFalse(e["match"])
            self.assertFalse(e["partition_match"])

    def test_sim_needs_r_dec(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.sim_file(d, [[0, 0], [1, 0]], 2, 2, 2, [])
            e = self.sim_of(p, self.two_orders(), None)["sim"]
            self.assertEqual(e["status"], "r_dec_required")

    def test_absent_polytope_is_reported_not_skipped(self):
        e = P.predictions(P.partition(self.two_orders()), [[0, 0], [1, 0]], 2,
                          Path("/nonexistent/sim.json"), Path("/nonexistent/quotient_polytope.json"))
        poly = [x for x in e if x["source"] == "polytope"][0]
        self.assertEqual(poly["status"], "absent")

    def test_cameron_square_spacing_one_full_coverage(self):
        worlds = [world([list(c) for c in o], **{"0,0": str(o[0])}) for o in itertools.permutations(SQ)]
        e = P.predictions(P.partition(worlds), SQ, None, Path("/nonexistent/s.json"),
                          Path("/nonexistent/p.json"))
        cam = [x for x in e if x["source"] == "cameron"][0]
        self.assertEqual(cam["status"], "compared")
        self.assertEqual(cam["predicted_classes"], 4)
        self.assertTrue(cam["match"])

    def test_cameron_line4_depends_on_r(self):
        worlds = [world([list(c) for c in o], **{"0,0": str(o[0])}) for o in itertools.permutations(LINE)]
        part = P.partition(worlds)
        at2 = [x for x in P.predictions(part, LINE, 2, Path("/nonexistent/s.json"),
                                        Path("/nonexistent/p.json")) if x["source"] == "cameron"][0]
        at4 = [x for x in P.predictions(part, LINE, 4, Path("/nonexistent/s.json"),
                                        Path("/nonexistent/p.json")) if x["source"] == "cameron"][0]
        self.assertEqual(at2["predicted_classes"], 12)
        self.assertFalse(at2["match"])
        self.assertEqual(at4["predicted_classes"], 4)
        self.assertTrue(at4["match"])


class Bootstrap(unittest.TestCase):
    def test_identical_samples_ci_contains_zero(self):
        r = P.bootstrap_diff([5, 5], [5, 5], n=1000)
        self.assertEqual(r["mean_diff"], 0)
        self.assertFalse(r["excludes_zero"])

    def test_separated_samples_ci_excludes_zero(self):
        r = P.bootstrap_diff([1, 1, 2], [9, 10, 10])
        self.assertTrue(r["excludes_zero"])
        self.assertAlmostEqual(r["mean_diff"], (4 / 3) - (29 / 3), places=9)
        self.assertEqual((r["n_a"], r["n_b"]), (3, 3))

    def test_default_is_10000_resamples_with_fixed_seed(self):
        r1 = P.bootstrap_diff([1, 2, 3], [2, 3, 4])
        r2 = P.bootstrap_diff([1, 2, 3], [2, 3, 4])
        self.assertEqual(r1["resamples"], 10000)
        self.assertEqual(r1["seed"], 20261101)
        self.assertEqual(r1["ci95"], r2["ci95"])


class OreComparison(unittest.TestCase):
    def test_class_without_repeats_is_not_compared(self):
        ores = {"0,0": {"iron": 1}, "1,0": {"iron": 0}}
        worlds = [cworld([[0, 0], [1, 0]], "A1", {"0,0": "x", "1,0": "x"}, ores),
                  cworld([[0, 0], [1, 0]], "A2", {"0,0": "x", "1,0": "x"}, ores),
                  cworld([[1, 0], [0, 0]], "B1", {"0,0": "y", "1,0": "y"},
                         {"0,0": {"iron": 9}, "1,0": {"iron": 0}})]
        r = P.ore_comparison(worlds, P.partition(worlds))
        self.assertEqual(r["comparisons"], [])
        self.assertEqual([c["members"] for c in r["insufficient_repeats"]], [["1,0;0,0"]])

    def test_repeat_classes_compared_with_ci(self):
        a = {"0,0": {"iron": 1}, "1,0": {"iron": 0}}
        b = {"0,0": {"iron": 9}, "1,0": {"iron": 0}}
        worlds = [cworld([[0, 0], [1, 0]], "A1", {"0,0": "x", "1,0": "x"}, a),
                  cworld([[0, 0], [1, 0]], "A2", {"0,0": "x", "1,0": "x"}, a),
                  cworld([[1, 0], [0, 0]], "B1", {"0,0": "y", "1,0": "y"}, b),
                  cworld([[1, 0], [0, 0]], "B2", {"0,0": "y", "1,0": "y"}, b)]
        r = P.ore_comparison(worlds, P.partition(worlds))
        iron = [c for c in r["comparisons"] if c["ore"] == "iron"][0]
        self.assertAlmostEqual(iron["mean_diff"], -8.0, places=9)
        self.assertTrue(iron["excludes_zero"])
        self.assertEqual(r["repeat_spread_max"], 0)
        self.assertEqual(r["keys_tested"], 8)


if __name__ == "__main__":
    unittest.main()
