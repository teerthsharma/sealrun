import json
import os
import sys
import time
import unittest
from datetime import datetime
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
        before = bench.peak_mb(os.getpid())
        b = b"\x01" * (300 * 1024 * 1024)
        del b
        self.assertGreaterEqual(bench.peak_mb(os.getpid()), before + 250)
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

        real_reset = server.reset
        walls = []

        def timed(srv, root):
            t = time.monotonic()
            out = real_reset(srv, root)
            walls.append(time.monotonic() - t)
            return out

        with mock.patch.object(serverdir, "make_scratch", side_effect=record), mock.patch.object(server, "reset", side_effect=timed):
            r = bench.measure(ROOT)
        self.assertTrue(5 < r["boot_secs"] < 120, r)
        self.assertTrue(5 < r["reset_secs"] < 120, r)
        self.assertLess(abs(r["reset_secs"] - walls[0]), 0.25, (r, walls))
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
        for k in ("boot_secs", "reset_secs", "peak_mb"):
            self.assertLessEqual(abs(saved[k] - r[k]), 0.5 * r[k], (k, saved[k], r[k]))
        self.assertGreater(saved["free_mb_before"], 0)
        self.assertGreater(r["free_mb_before"], 0)
        self.assertIsNotNone(datetime.fromisoformat(saved["when"]).utcoffset())
        self.assertIsNotNone(datetime.fromisoformat(r["when"]).utcoffset())
        self.assertGreaterEqual(r["other_java"], 0)
        self.assertEqual(saved["other_java"], 0)


if __name__ == "__main__":
    unittest.main()
