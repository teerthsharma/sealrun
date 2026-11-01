import os
import shutil
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import orderrun
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
PLACED = "execute if block 0 100 0 minecraft:gold_block"


def remove_scratch(d: Path) -> None:
    if not (d / serverdir.MARKER).is_file():
        return
    deadline = time.monotonic() + 10
    while True:
        try:
            shutil.rmtree(d)
            return
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.5)


class Lab(unittest.TestCase):
    def reset_wipes_placed_block_and_leaves_no_java(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        servers = []
        try:
            srv = server.boot(scratch)
            servers.append(srv)
            self.assertTrue(orderrun.wait_loaded(srv, 0, 0))
            srv.command("setblock 0 100 0 minecraft:gold_block")
            before = srv.command(PLACED)
            print(f"before reset: {PLACED!r} -> {before!r}")
            self.assertIn("Test passed", before)

            t0 = time.monotonic()
            srv2 = server.reset(srv, ROOT)
            servers.append(srv2)
            self.assertTrue(orderrun.wait_loaded(srv2, 0, 0))
            after = srv2.command(PLACED)
            reset_secs = time.monotonic() - t0
            print(f"after reset: {PLACED!r} -> {after!r}")
            print(f"reset_secs={reset_secs:.2f} (stop + delete + boot)")
            self.assertNotIn("Test passed", after)

            srv2.stop()
            self.assertIsNotNone(srv.proc.poll())
            self.assertIsNotNone(srv2.proc.poll())
            self.assertEqual(server.running_count(), 0)
        finally:
            for s in servers:
                s.stop()
            remove_scratch(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
