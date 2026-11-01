import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import bridge_classes, first_ticket_classes

ROWS_PATH = Path(__file__).resolve().parents[1] / "results" / "research" / "quotient_polytope.json"


class Lab(unittest.TestCase):
    def seventy_two_rows_agree(self):
        rows = json.loads(ROWS_PATH.read_text(encoding="utf-8"))["results"]
        self.assertEqual(len(rows), 72)
        agree = 0
        disagree = []
        for row in rows:
            n, family = bridge_classes.row_to_family(row)
            got = first_ticket_classes.classes(n, family)
            if got == row["classes"]:
                agree += 1
            else:
                disagree.append((row["layout"], row["R"], row["variant"], got, row["classes"]))
        print(f"rows checked: {len(rows)}, agree: {agree}")
        self.assertEqual(disagree, [])


if __name__ == "__main__":
    unittest.main()
