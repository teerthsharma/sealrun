import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import r2_numbers


class Lab(unittest.TestCase):
    def test_numbers_are_read_fresh_and_missing_says_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aim.json").write_text(json.dumps({"lever": True}), encoding="utf-8")

            first = r2_numbers.numbers(root)
            self.assertEqual(first["aim.json"], {"lever": True})
            self.assertEqual(first["order_control.json"], "not run")

            (root / "aim.json").write_text(json.dumps({"lever": False}), encoding="utf-8")

            second = r2_numbers.numbers(root)
            self.assertEqual(second["aim.json"], {"lever": False})


if __name__ == "__main__":
    unittest.main()
