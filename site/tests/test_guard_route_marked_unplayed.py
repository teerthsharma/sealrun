import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def card(goal_id, title):
    return {"id": goal_id, "title": title, "plain": "p", "why": "w", "done_when": "d"}


class Lab(unittest.TestCase):
    def test_guard_route_marked_unplayed(self):
        from build_r2 import build

        with tempfile.TemporaryDirectory() as tmp:
            charts = Path(tmp)
            (charts / "foreman.json").write_text(json.dumps([card("N2.G1.1", "Talking to the server")]), encoding="utf-8")
            (charts / "chase.json").write_text(json.dumps([card("N2.G5.A1", "Numbers read live")]), encoding="utf-8")
            (charts / "cameron.json").write_text(json.dumps([card("N2.G1.C1", "No server left running")]), encoding="utf-8")
            (charts / "departments.json").write_text(
                json.dumps({"departments": [{"name": "immunology", "head": "Cameron", "goals": ["N2.G1", "N2.G5"]}]}),
                encoding="utf-8",
            )
            result = build(charts, {})

        self.assertIn("route", result)
        self.assertIs(result["route"]["played"], False)
        self.assertIn("not yet played", result["route"]["note"])


if __name__ == "__main__":
    unittest.main()
