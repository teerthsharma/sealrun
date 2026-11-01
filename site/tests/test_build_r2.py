import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_r2


def write(folder, name, data):
    (folder / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class Lab(unittest.TestCase):
    def build_r2_merges_cards_and_ancestor_departments(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write(folder, "foreman.json", [
                {"id": "N2.G3.2", "title": "Foreman title", "plain": "from foreman"},
                {"id": "N2.G3.9", "title": "Unlisted goal", "plain": "unlisted"},
            ])
            write(folder, "chase.json", [{"id": "N2.G3.2", "why": "from chase", "done_when": "chase done"}])
            write(folder, "cameron.json", [{"id": "N2.G3.4.A1", "plain": "cameron card"}])
            write(folder, "departments.json", {"departments": [
                {"name": "neurology", "goals": ["N2.G3.2"]},
                {"name": "surgery", "goals": ["N2.G3.6"]},
            ]})

            result = build_r2.build(folder, {"N2.G3.2": "reached"})

        ids = [g["id"] for g in result["goals"]]
        goals = {g["id"]: g for g in result["goals"]}
        self.assertEqual(ids.count("N2.G3.2"), 1)
        merged = goals["N2.G3.2"]
        self.assertEqual(merged["plain"], "from foreman")
        self.assertEqual(merged["why"], "from chase")
        self.assertEqual(merged["fellows"], ["foreman", "chase"])
        self.assertEqual(merged["status"], "reached")
        self.assertEqual(merged["department"], "neurology")
        self.assertEqual(goals["N2.G3.9"]["status"], "pending")
        self.assertIsNone(goals["N2.G3.9"]["department"])
        self.assertEqual(result["route"], {"played": False, "note": "planned on a map, not yet played in the real game"})

        depts = json.loads((build_r2.CHARTS / "departments.json").read_text(encoding="utf-8"))["departments"]
        self.assertEqual(build_r2.department("N2.G3.6.1", depts), "surgery")
        self.assertEqual(build_r2.department("N2.G1.1.1", depts), "immunology")
        self.assertIsNone(build_r2.department("N2.G6.1", depts))


if __name__ == "__main__":
    unittest.main()
