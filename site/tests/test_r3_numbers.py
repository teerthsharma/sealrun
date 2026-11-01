import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import r3_numbers

REAL = Path(__file__).resolve().parents[2] / "lab" / "results" / "research"


class Lab(unittest.TestCase):
    def r3_numbers_missing_is_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            shutil.copy(REAL / "race_realmodel.json", folder / "race_realmodel.json")
            got = r3_numbers.numbers(folder)

        race = json.loads((REAL / "race_realmodel.json").read_text(encoding="utf-8"))
        for row in race["summary"]:
            for arm in ("plan", "bfs"):
                key = f"race/{arm}/{row['level']}/routed"
                self.assertEqual(got[key], row[arm]["routed"], key)

        missing = {k: v for k, v in got.items() if not k.startswith("race/")}
        self.assertTrue(any(k.startswith("quotient/") for k in missing))
        self.assertTrue(any(k.startswith("partitions/") for k in missing))
        for key, value in missing.items():
            self.assertEqual(value, "not run", key)


if __name__ == "__main__":
    unittest.main()
