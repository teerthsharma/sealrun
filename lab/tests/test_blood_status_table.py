import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import status_table

RESULTS = Path(__file__).resolve().parents[1] / "results"
META_KEYS = {"ticket", "when"}


def statuses_in(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in META_KEYS:
                continue
            if isinstance(value, str):
                yield value.removeprefix("minecraft:")
            else:
                yield from statuses_in(value)


class Lab(unittest.TestCase):
    def thirteen_statuses_in_order(self):
        statuses = status_table.STATUSES
        self.assertEqual(len(statuses), 13)
        self.assertEqual(statuses[0], "empty")
        self.assertEqual(statuses[8], "features")
        self.assertEqual(statuses[-1], "full")
        saved = set()
        for name in ("neighbour_status.json", "forceload_tile.json"):
            with open(RESULTS / name) as f:
                saved |= set(statuses_in(json.load(f)))
        print("saved status names:", sorted(saved))
        self.assertTrue(saved, "no status names found in saved results")
        self.assertLessEqual(saved, set(statuses), f"not in STATUSES: {sorted(saved - set(statuses))}")


if __name__ == "__main__":
    unittest.main()
