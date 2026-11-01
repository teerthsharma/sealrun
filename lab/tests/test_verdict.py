import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verdict


def write(folder, name, **fields):
    doc = {"seed": 987654, "area": "ring-7", "height": 73, "orders": 24,
           "control": {"repeat_diff": 0}, "lever": True}
    doc.update(fields)
    path = folder / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class Lab(unittest.TestCase):
    def verdict_states_bound_and_reroute(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)

            absent = folder / "order_absent.json"
            self.assertEqual(verdict.statements([absent]), ["order_absent.json: not run"])

            ok = write(folder, "order_ok.json")
            (s,) = verdict.statements([ok])
            for field in ("987654", "ring-7", "73", "24"):
                self.assertIn(field, s)

            unmeasured = write(folder, "order_unmeasured.json", control={"repeat_diff": None})
            (s,) = verdict.statements([unmeasured])
            self.assertIn("noise floor not measured", s)
            self.assertNotIn("matter", s)

            shaky = write(folder, "order_shaky.json", control={"repeat_diff": 3})
            (s,) = verdict.statements([shaky])
            self.assertIn("shaky", s)

            dead = write(folder, "order_dead.json", lever=False)
            (s,) = verdict.statements([dead])
            self.assertTrue(s.endswith("next route: " + verdict.NEXT_ROUTE), s)


if __name__ == "__main__":
    unittest.main()
