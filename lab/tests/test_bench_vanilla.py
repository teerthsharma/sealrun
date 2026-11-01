import json
import os
import sys
import threading
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bench
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
        self.assertLessEqual(abs(runs[1]["worlds_per_minute"] - r["worlds_per_minute"]), 0.5 * r["worlds_per_minute"], (runs[1], r))
        self.assertLessEqual(abs(runs[1]["mb_per_world"] - r["mb_per_world"]), 0.5 * r["mb_per_world"], (runs[1], r))
        self.assertEqual(saved["not_run"], {"n": 3, "why": "owner cap of 2 real servers"})

    def measure_runs_lanes_together_and_counts_finished_resets(self):
        scratch = {"dir": Path("fake-scratch")}
        lock = threading.Lock()
        first_boot, finished = {}, []

        def boot(sc, timeout=120.0):
            with lock:
                first_boot.setdefault(threading.get_ident(), time.monotonic())
            return mock.Mock(scratch=sc)

        def reset_ok(srv, root):
            time.sleep(0.2)
            with lock:
                finished.append(srv)
            return mock.Mock(scratch=srv.scratch)

        def run(reset, n):
            with ExitStack() as st:
                st.enter_context(mock.patch.object(server, "boot", side_effect=boot))
                st.enter_context(mock.patch.object(server, "reset", side_effect=reset))
                st.enter_context(mock.patch.object(serverdir, "make_scratch", return_value=scratch))
                st.enter_context(mock.patch.object(serverdir, "remove"))
                st.enter_context(mock.patch.object(bench, "peak_mb", return_value=800.0))
                return bench_vanilla.measure(n, 1.0, Path("unused"))

        r = run(reset_ok, 2)
        starts = sorted(first_boot.values())
        self.assertEqual(len(starts), 2, first_boot)
        self.assertLess(starts[1] - starts[0], 0.1, first_boot)
        self.assertGreaterEqual(r["worlds"], 2, r)
        self.assertEqual(r["worlds"], len(finished), r)
        self.assertEqual(r["peak_mb_total"], 1600.0, r)
        self.assertEqual(r["mb_per_world"], r["peak_mb_total"] / 2, r)

        calls = []

        def reset_fails_second(srv, root):
            calls.append(srv)
            if len(calls) == 2:
                raise RuntimeError("fake reset failed")
            return reset_ok(srv, root)

        with self.assertRaises(RuntimeError):
            run(reset_fails_second, 2)


if __name__ == "__main__":
    unittest.main()
