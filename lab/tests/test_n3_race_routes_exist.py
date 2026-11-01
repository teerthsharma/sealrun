import json
import os
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE = Path(os.environ.get("RACE_REALMODEL_JSON") or ROOT / "lab" / "results" / "research" / "race_realmodel.json")
ROUND1 = Path(os.environ.get("ROUND1_REACH_JSON") or ROOT / "lab" / "results" / "research" / "round1_reach.json")
GRID = ROOT / "lab" / "results" / "research" / "seed7_spawn.grid"
SPAWN = (32, 32)


def air_count(path):
    raw = path.read_bytes()
    w, h = struct.unpack("<II", raw[:8])
    return raw[8:8 + w * h].count(0)


class Lab(unittest.TestCase):
    def priced_model_finds_route_where_round1_found_none(self):
        self.assertTrue(ROUND1.exists(), f"missing round-1 record {ROUND1.name}: run crates/route/tests/round1_reach.rs")
        r1 = json.loads(ROUND1.read_text())
        self.assertEqual(r1["grid"], "lab/results/research/seed7_spawn.grid")
        self.assertEqual(r1["starts"], air_count(GRID), "round-1 start count is not the grid's air tiles")
        print(f"round 1: starts {r1['starts']} routed {r1['routed']} at {r1['source_commit']}")
        self.assertEqual(r1["routed"], 0, "round-1 planner routes from its starts")

        data = json.loads(RACE.read_text())
        spawn = [r for r in data["rows"] if r["kind"] == "centre" and (r["x"], r["y"]) == SPAWN]
        self.assertEqual(len(spawn), 1, f"expected one spawn start row at {SPAWN}")
        top = max(spawn[0]["levels"], key=lambda lv: lv["level"])
        print(f"spawn {SPAWN} level {top['level']}: plan routed {top['plan']['routed']} ticks {top['plan']['ticks']}")
        self.assertTrue(top["plan"]["routed"], f"plan_real does not route from spawn at budget {top['level']}")


if __name__ == "__main__":
    unittest.main()
