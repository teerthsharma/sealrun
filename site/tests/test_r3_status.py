import json
import os
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import build_r3

CHARTS = HERE / "charts" / "r3"
STATUS = Path(os.environ.get("R3_STATUS_JSON", HERE / "r3_status.json"))
VALID = {"pending", "active", "reached", "blocked", "retired"}
KEY = re.compile(r"^N3\.[A-Za-z0-9.]+$")


def chart_ids():
    return sorted(
        card["id"]
        for path in CHARTS.glob("*.json")
        for card in json.loads(path.read_text(encoding="utf-8"))
    )


class Lab(unittest.TestCase):
    def r3_status_keys_and_values_valid(self):
        statuses = json.loads(STATUS.read_text(encoding="utf-8"))
        self.assertIsInstance(statuses, dict)
        bad_keys = sorted(k for k in statuses if not KEY.match(k))
        self.assertEqual(bad_keys, [])
        bad_values = {k: v for k, v in statuses.items() if v not in VALID}
        self.assertEqual(bad_values, {})
        ids = chart_ids()
        missing = sorted(set(ids) - set(statuses))
        self.assertEqual(missing, [], "chart goal ids with no status")
        read = {e["id"]: e["status"] for e in build_r3.build(CHARTS, STATUS)}
        self.assertEqual({i: read[i] for i in ids}, {i: statuses[i] for i in ids})
        counts = Counter(statuses.values())
        print(f"r3 status keys: {len(statuses)}")
        for s in sorted(VALID):
            print(f"  {s}: {counts.get(s, 0)}")


if __name__ == "__main__":
    unittest.main()
