import json
import sys
import tempfile
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]


class Lab(unittest.TestCase):
    def test_guard_site_numbers_from_files(self):
        sys.path.insert(0, str(SITE))
        from r2_numbers import numbers

        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)

            empty = numbers(results)
            self.assertTrue(empty, "numbers() must name every expected result file")
            for name, value in empty.items():
                self.assertEqual(value, "not run", f"missing {name} must read as not run, never 0 or None")

            name = next(iter(empty))
            (results / name).write_text(json.dumps({"lever": False, "orders": 24}), encoding="utf-8")
            self.assertEqual(numbers(results)[name], {"lever": False, "orders": 24})

            (results / name).write_text(json.dumps({"lever": False, "orders": 12}), encoding="utf-8")
            self.assertEqual(numbers(results)[name], {"lever": False, "orders": 12}, "site must follow the file on disk")

            (results / name).unlink()
            after = numbers(results)[name]
            self.assertEqual(after, "not run")
            self.assertIsNot(after, 0)
            self.assertIsNot(after, None)
            for value in numbers(results).values():
                self.assertNotIn(value, (0, None))


if __name__ == "__main__":
    unittest.main()
