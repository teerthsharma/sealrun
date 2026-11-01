"""At equal expanded-node budget, the planner's routed price is never above the breadth-first price.

Each row carries levels[]; each level holds a plan and a bfs record with budget, routed and ticks.
A pair counts when both solvers routed and their budgets are equal. For each counted pair the
planner's ticks must be <= the bfs ticks. The legacy_plan_cap_2000000 field is ignored.
"""
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE = Path(os.environ.get("RACE_REALMODEL_JSON") or ROOT / "lab" / "results" / "research" / "race_realmodel.json")


class Lab(unittest.TestCase):
    def planner_price_not_above_bfs_at_equal_budget(self):
        data = json.loads(RACE.read_text())
        self.assertIn("rows", data, f"{RACE.name}: missing top-level field 'rows'")
        rows = data["rows"]
        levels = sorted({lv["level"] for r in rows for lv in r["levels"]})
        pairs = {lv: 0 for lv in levels}
        cheaper = {lv: 0 for lv in levels}
        violations = []
        for r in rows:
            where = f"{r['kind']} x={r['x']} y={r['y']}"
            for lv in r["levels"]:
                p, b = lv["plan"], lv["bfs"]
                if not (p["routed"] and b["routed"] and p["budget"] == b["budget"]):
                    continue
                pairs[lv["level"]] += 1
                if p["ticks"] is None or b["ticks"] is None:
                    violations.append(f"{where} level {lv['level']}: routed pair without ticks")
                    continue
                if p["ticks"] < b["ticks"]:
                    cheaper[lv["level"]] += 1
                if p["ticks"] > b["ticks"]:
                    violations.append(
                        f"{where} level {lv['level']} budget {p['budget']}: "
                        f"plan ticks {p['ticks']} > bfs ticks {b['ticks']}"
                    )
        for lv in levels:
            print(f"level {lv}: equal-budget routed pairs={pairs[lv]} plan_strictly_cheaper={cheaper[lv]}")
        total = sum(pairs.values())
        print(f"total pairs={total} plan_strictly_cheaper={sum(cheaper.values())} violations={len(violations)}")
        self.assertGreaterEqual(total, 1, "no equal-budget pair where both solvers routed")
        self.assertFalse(violations, f"{len(violations)} pairs break the price claim\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
