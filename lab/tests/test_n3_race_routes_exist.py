import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE = Path(os.environ.get("RACE_REALMODEL_JSON") or ROOT / "lab" / "results" / "research" / "race_realmodel.json")
SPAWN = (32, 32)


class Lab(unittest.TestCase):
    # Round-1 side unchecked: no round-1 record exists in the repo (the 0-of-1,417 probe is cited in house/prognosis-r2.md, its grid was only in a session scratchpad).
    # Only the priced side is asserted here.
    def priced_model_finds_route_where_round1_found_none(self):
        data = json.loads(RACE.read_text())
        spawn = [r for r in data["rows"] if r["kind"] == "centre" and (r["x"], r["y"]) == SPAWN]
        self.assertEqual(len(spawn), 1, f"expected one spawn start row at {SPAWN}")
        top = max(spawn[0]["levels"], key=lambda lv: lv["level"])
        print(f"spawn {SPAWN} level {top['level']}: plan routed {top['plan']['routed']} ticks {top['plan']['ticks']}")
        self.assertTrue(top["plan"]["routed"], f"plan_real does not route from spawn at budget {top['level']}")


if __name__ == "__main__":
    unittest.main()
