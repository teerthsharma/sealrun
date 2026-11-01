import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import orderrun
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))


class Lab(unittest.TestCase):
    def run_order_returns_window_for_two_chunks(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        try:
            blocks = orderrun.run_order(scratch, [(64, 64), (65, 64)])
            self.assertEqual(len(blocks), 131072)
            self.assertEqual(sum(v is None for v in blocks.values()), 0)
            for pos in [(1024, 0, 1024), (1040, 64, 1024), (1055, 255, 1039)]:
                print(f"{pos} -> {blocks[pos]!r}")
        finally:
            serverdir.remove(scratch["dir"])

    def run_order_stops_and_raises_when_a_chunk_does_not_load(self):
        class Fake:
            stops = 0

            def command(self, text):
                return ""

            def stop(self, grace=30.0):
                Fake.stops += 1
                return 0

        with mock.patch.object(orderrun.server, "boot", return_value=Fake()), \
                mock.patch.object(orderrun, "wait_loaded", return_value=False):
            with self.assertRaisesRegex(RuntimeError, r"chunk \(64, 64\)"):
                orderrun.run_order({"dir": Path("unused")}, [(64, 64)])
        self.assertEqual(Fake.stops, 1)


if __name__ == "__main__":
    unittest.main()
