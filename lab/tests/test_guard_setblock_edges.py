import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anvil
import orderrun
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
LOADED = [(0, 0), (1, 0), (0, -1), (-2, -3)]
PLACED = [
    (15, 80, 3, "gold_block"),
    (16, 80, 3, "diamond_block"),
    (3, 80, -1, "emerald_block"),
    (3, 80, 0, "lapis_block"),
    (-17, 64, -33, "redstone_block"),
    (5, 0, 5, "iron_block"),
    (5, 255, 5, "coal_block"),
]


class Lab(unittest.TestCase):
    def test_setblock_edges_read_back(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            for cx, cz in LOADED:
                self.assertTrue(orderrun.wait_loaded(srv, cx, cz))
            for x, y, z, name in PLACED:
                reply = srv.command(f"setblock {x} {y} {z} minecraft:{name}")
                print(f"setblock {x} {y} {z} minecraft:{name} -> {reply!r}")
                self.assertIn("Changed the block", reply)
            srv.command("save-all flush")
            srv.stop()

            region = scratch["dir"] / "world" / "region"
            self.assertTrue((region / "r.-1.-1.mca").is_file())
            for x, y, z, name in PLACED:
                got = anvil.block_at(region, x, y, z)
                print(f"block_at {x} {y} {z} -> {got!r}")
                self.assertEqual(got, f"minecraft:{name}")
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
