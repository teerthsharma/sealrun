import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import bug_ledger

SOURCES = Path(__file__).resolve().parents[1] / "results" / "research" / "sources.md"

EXPECTED = {
    "MC-55596": ("2014-05-21", None),
    "MC-199702": ("2020-09-06", "21w20a"),
}


class Lab(unittest.TestCase):
    def tracker_dates_and_short_quotes(self):
        entries = {e["id"]: e for e in bug_ledger.LEDGER}
        self.assertEqual(set(entries), set(EXPECTED))
        for bug_id, (created, fixed) in EXPECTED.items():
            entry = entries[bug_id]
            self.assertEqual(entry["url"], f"https://mojira.dev/{bug_id}")
            self.assertEqual(date.fromisoformat(entry["created"]).isoformat(), created)
            self.assertEqual(entry["fixed"], fixed)
            self.assertLess(len(entry["quote"].split()), 15, bug_id)
        text = SOURCES.read_text(encoding="utf-8")
        for bug_id in EXPECTED:
            self.assertIn(f"https://mojira.dev/{bug_id}", text)


if __name__ == "__main__":
    unittest.main()
