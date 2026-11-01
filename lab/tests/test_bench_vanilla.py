import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bench_vanilla
import server
import serverdir

ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RESULT = Path(__file__).resolve().parents[1] / "results" / "worlds_vanilla.json"
KEYS = {"n", "secs", "worlds", "worlds_per_minute", "peak_mb_total", "mb_per_world", "other_java", "when"}


class Lab(unittest.TestCase):
    def n_vanilla_servers_worlds_per_minute_and_ram_per_world(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        made = []
        real_make = serverdir.make_scratch

        def record(src, root):
            scratch = real_make(src, root)
            made.append(scratch["dir"])
            return scratch

        with mock.patch.object(serverdir, "make_scratch", side_effect=record):
            r = bench_vanilla.measure(1, 60, ROOT)
        self.assertEqual(set(r), KEYS, r)
        self.assertEqual(r["n"], 1)
        self.assertGreaterEqual(r["worlds"], 1, r)
        self.assertTrue(200 < r["mb_per_world"] < 2000, r)
        self.assertEqual(server.running_count(), 0)
        self.assertEqual(len(made), 1)
        for d in made:
            self.assertFalse(d.exists(), f"measure left its scratch folder {d}")

        with mock.patch.object(server, "boot") as boot, mock.patch.object(serverdir, "make_scratch") as mk:
            with self.assertRaises(ValueError):
                bench_vanilla.measure(3, 1, ROOT)
            boot.assert_not_called()
            mk.assert_not_called()

        self.assertTrue(RESULT.is_file(), f"missing {RESULT}")
        saved = json.loads(RESULT.read_text())
        runs = {run["n"]: run for run in saved["runs"]}
        self.assertEqual(set(runs), {1, 2})
        for n in (1, 2):
            self.assertEqual(set(runs[n]), KEYS, runs[n])
            self.assertEqual(runs[n]["other_java"], 0, runs[n])
            self.assertGreaterEqual(runs[n]["worlds"], 1, runs[n])
        self.assertEqual(saved["not_run"], {"n": 3, "why": "owner cap of 2 real servers"})


if __name__ == "__main__":
    unittest.main()
