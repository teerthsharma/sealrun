import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import restriction as R  # noqa: E402

TICK = [(0, 0), (0, 4), (3, 0)]  # sorted: index i is TICK[i]
PERMS = list(itertools.permutations(range(3)))


def toy_worlds():
    worlds = []
    for p in PERMS:
        worlds.append({
            "order": [list(TICK[i]) for i in p],
            "chunks": {
                "0,1": {"sha256": str(p[-1])},
                "0,0": {"sha256": str(tuple(t for t in p if t in (0, 2)))},
            },
        })
    return worlds


class Restriction(unittest.TestCase):
    def test_last_of_all_tickets_fits_last_and_pattern_all_not_first(self):
        fam = R.analyze(toy_worlds())["chunks"]["0,1"]["families"]
        self.assertEqual(fam["last"]["min_sets"], [[0, 1, 2]])
        self.assertFalse(fam["first"]["fits"])
        self.assertEqual(fam["pattern"]["min_sets"], [[0, 1, 2]])

    def test_pattern_of_pair_is_minimal_at_size_two(self):
        fam = R.analyze(toy_worlds())["chunks"]["0,0"]["families"]
        self.assertEqual(fam["pattern"]["min_size"], 2)
        self.assertEqual(fam["pattern"]["min_sets"], [[0, 2]])
        self.assertEqual(fam["first"]["min_sets"], [[0, 2]])

    def test_ball_match_per_radius(self):
        chunks = R.analyze(toy_worlds())["chunks"]
        self.assertEqual(chunks["0,0"]["families"]["pattern"]["ball"],
                         {"2": False, "3": True, "4": False, "5": False})
        self.assertEqual(chunks["0,1"]["families"]["last"]["ball"],
                         {"2": False, "3": True, "4": True, "5": True})

    def test_pattern_of_all_tickets_always_fits(self):
        res = R.analyze(toy_worlds())
        self.assertEqual(res["summary"]["pattern_all_fits_failures"], 0)

    def test_restriction_classes_exact_match_counts_the_pair_chunk(self):
        classes = R.analyze(toy_worlds())["classes"]
        self.assertEqual(classes["measured"], 2)
        self.assertEqual(classes["restriction"]["3"], {"predicted": 2, "exact": 1})


if __name__ == "__main__":
    unittest.main()
