import json
import os
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bench
import serverdir
import server

ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RESULT = Path(__file__).resolve().parents[1] / "results" / "lab_timing.json"


class Lab(unittest.TestCase):
    def lab_timing_records_boot_reset_and_peak_ram(self):
        own = bench.peak_mb(os.getpid())
        self.assertGreater(own, 1)
        self.assertLess(own, 2000)

        ROOT.mkdir(parents=True, exist_ok=True)
        made = []
        real_make = serverdir.make_scratch

        def record(src, root):
            scratch = real_make(src, root)
            made.append(scratch["dir"])
            return scratch

        with mock.patch.object(serverdir, "make_scratch", side_effect=record):
            r = bench.measure(ROOT)
        self.assertTrue(5 < r["boot_secs"] < 120, r)
        self.assertTrue(5 < r["reset_secs"] < 120, r)
        self.assertTrue(200 < r["peak_mb"] < 2000, r)
        self.assertEqual(r["xmx"], "1G")
        self.assertEqual(r["runs"], 1)
        self.assertEqual(server.running_count(), 0)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists(), f"measure left its scratch folder {made[0]}")

        self.assertTrue(RESULT.is_file(), f"missing {RESULT}")
        saved = json.loads(RESULT.read_text())
        self.assertEqual(set(saved), set(r))
        self.assertTrue(5 < saved["boot_secs"] < 120, saved)
        self.assertTrue(5 < saved["reset_secs"] < 120, saved)
        self.assertTrue(200 < saved["peak_mb"] < 2000, saved)
        self.assertEqual(saved["xmx"], "1G")
        self.assertEqual(saved["runs"], 1)


if __name__ == "__main__":
    unittest.main()
