"""Both solvers in the realmodel race get the same expanded-node budget at every level of every row.

Each row carries levels[]; each level holds a plan and a bfs record with budget, expanded and
routed. A level holds when plan_real's budget equals bfs_real's and neither solver expanded
more cells than its budget. The legacy_plan_cap_2000000 field is ignored.
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
        if "rows" not in data:
            self.fail(f"{RACE.name}: missing top-level field 'rows'")
        rows = data["rows"]
        for i, r in enumerate(rows):
            if "levels" not in r:
                self.fail(f"{RACE.name}: row {i} is missing field 'levels'")
            for lv in r["levels"]:
                for solver in ("plan", "bfs"):
                    if "budget" not in lv[solver]:
                        self.fail(f"{RACE.name}: row {i} level {lv.get('level')} {solver} is missing field 'budget'")
        levels = sorted({lv["level"] for r in rows for lv in r["levels"]})
        print(f"rows={len(rows)} levels={levels}")
        for lv in levels:
            recs = [x for r in rows for x in r["levels"] if x["level"] == lv]
            print(
                f"level {lv}: routed plan_real {sum(x['plan']['routed'] for x in recs)}/{len(recs)}, "
                f"routed bfs_real {sum(x['bfs']['routed'] for x in recs)}/{len(recs)}"
            )
        self.assertGreaterEqual(len(levels), MIN_LEVELS, "fewer than 3 budget levels in the file")
        self.assertGreaterEqual(len(rows), MIN_ROWS, "fewer than 100 rows in the file")

        bad_rows = []
        pairs = differ = 0
        for r in rows:
            where = f"{r['kind']} x={r['x']} y={r['y']}"
            notes = []
            for lv in r["levels"]:
                p, b = lv["plan"], lv["bfs"]
                pairs += 1
                if p["budget"] != b["budget"]:
                    differ += 1
                    notes.append(f"level {lv['level']}: plan_real budget {p['budget']} != bfs_real budget {b['budget']}")
                if p["expanded"] > p["budget"]:
                    notes.append(f"level {lv['level']}: plan_real expanded {p['expanded']} > budget {p['budget']}")
                if b["expanded"] > b["budget"]:
                    notes.append(f"level {lv['level']}: bfs_real expanded {b['expanded']} > budget {b['budget']}")
            if notes:
                bad_rows.append(f"{where}: " + "; ".join(notes))
        if bad_rows:
            self.fail(
                f"{len(bad_rows)}/{len(rows)} rows break the equal-budget claim "
                f"({differ}/{pairs} level pairs differ)\n" + "\n".join(bad_rows)
            )


if __name__ == "__main__":
    unittest.main()
