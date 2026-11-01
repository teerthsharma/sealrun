import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import choice

RESULTS = Path(__file__).resolve().parents[1] / "results"
BLOCKED = "Fabric/mod download needs the owner's approval of the file list (permissions ledger row 15)"


def run(n, wpm, peak):
    return {"n": n, "worlds_per_minute": wpm, "peak_mb_total": peak}


def proc(wpm, peak, **extra):
    return {"route": "in_process", "worlds_per_minute": wpm, "peak_mb_total": peak, **extra}


class Lab(unittest.TestCase):
    def route_choice_picks_more_worlds_per_gb_and_falls_back(self):
        vanilla = [run(1, 3.07, 812.2), run(2, 4.42, 1609.2)]
        self.assertAlmostEqual(choice.per_gb(vanilla[0]), 3.07 / (812.2 / 1024))
        self.assertAlmostEqual(choice.per_gb(vanilla[1]), 4.42 / (1609.2 / 1024))

        missing = choice.pick(vanilla, None)
        self.assertEqual(missing["route"], "vanilla", missing)
        self.assertEqual(missing["vanilla_best_n"], 1, missing)
        self.assertEqual(missing["why"], "missing", missing)

        better = choice.pick(vanilla, proc(5.0, 1024.0))
        self.assertEqual(better["route"], "in_process", better)
        self.assertAlmostEqual(better["worlds_per_minute_per_gb"], 5.0)
        self.assertEqual(better["vanilla_best_n"], 1, better)

        worse = choice.pick(vanilla, proc(1.0, 1024.0))
        self.assertEqual(worse["route"], "vanilla", worse)
        self.assertAlmostEqual(worse["worlds_per_minute_per_gb"], 3.07 / (812.2 / 1024))

        equal = choice.pick([run(1, 2.0, 1024.0)], proc(2.0, 1024.0))
        self.assertEqual(equal["route"], "vanilla", equal)

        blocked = choice.pick(vanilla, proc(9.0, 1024.0, blocked=BLOCKED))
        self.assertEqual(blocked["route"], "vanilla", blocked)
        self.assertEqual(blocked["why"], BLOCKED, blocked)

        runs = json.loads((RESULTS / "worlds_vanilla.json").read_text())["runs"]
        self.assertEqual(choice.pick(runs, None)["vanilla_best_n"], 1)

        saved_path = RESULTS / "world_route.json"
        self.assertTrue(saved_path.is_file(), f"missing {saved_path}")
        saved = json.loads(saved_path.read_text())
        self.assertIn("when", saved, saved)
        when = saved.pop("when")
        self.assertTrue(when, saved)
        self.assertEqual(saved, choice.pick(runs, {"route": "in_process", "blocked": BLOCKED}))


if __name__ == "__main__":
    unittest.main()
