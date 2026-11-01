"""Both solvers in the realmodel race get the same expanded-node budget on every row.

plan_real's allowance is the top-level node_cap (rows carry no plan budget); bfs_real's
allowance is each row's bfs[].budget. A row holds when every BFS budget equals the plan
allowance and neither solver expanded more cells than its allowance.
"""
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE = Path(os.environ.get("RACE_REALMODEL_JSON") or ROOT / "lab" / "results" / "research" / "race_realmodel.json")
MIN_LEVELS = 3
MIN_ROWS = 100


class Lab(unittest.TestCase):
    def race_node_budgets_equal(self):
        data = json.loads(RACE.read_text())
        if "node_cap" not in data:
            self.fail(f"{RACE.name}: missing top-level field 'node_cap' (the plan_real budget)")
        plan_budget = data["node_cap"]
        rows = data["rows"]
        for i, r in enumerate(rows):
            for b in r["bfs"]:
                if "budget" not in b:
                    self.fail(f"{RACE.name}: row {i} bfs entry is missing field 'budget' (the bfs_real budget)")
        levels = sorted({b["budget"] for r in rows for b in r["bfs"]})
        print(f"rows={len(rows)} bfs budget levels={levels}")
        print(f"routed plan_real (budget {plan_budget}): {sum(r['plan']['ticks'] is not None for r in rows)}/{len(rows)}")
        for lv in levels:
            routed = sum(b["ticks"] is not None for r in rows for b in r["bfs"] if b["budget"] == lv)
            print(f"routed bfs_real (budget {lv}): {routed}/{len(rows)}")
        self.assertGreaterEqual(len(levels), MIN_LEVELS, "fewer than 3 budget levels in the file")
        self.assertGreaterEqual(len(rows), MIN_ROWS, "fewer than 100 rows in the file")

        bad_rows = []
        for r in rows:
            where = f"{r['kind']} x={r['x']} y={r['y']}"
            notes = []
            mismatched = [b["budget"] for b in r["bfs"] if b["budget"] != plan_budget]
            if mismatched:
                notes.append(f"bfs budget {mismatched} != plan_real budget {plan_budget}")
            if r["plan"]["nodes"] > plan_budget:
                notes.append(f"plan_real expanded {r['plan']['nodes']} > budget {plan_budget}")
            for b in r["bfs"]:
                if b["nodes"] > b["budget"]:
                    notes.append(f"bfs_real@{b['budget']} expanded {b['nodes']} > budget")
            if notes:
                bad_rows.append(f"{where}: " + "; ".join(notes))
        if bad_rows:
            pairs = sum(len(r["bfs"]) for r in rows)
            differ = sum(b["budget"] != plan_budget for r in rows for b in r["bfs"])
            self.fail(
                f"{len(bad_rows)}/{len(rows)} rows break the equal-budget claim "
                f"({differ}/{pairs} row-level budget pairs differ)\n" + "\n".join(bad_rows)
            )


if __name__ == "__main__":
    unittest.main()
