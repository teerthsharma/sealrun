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
PLACED = {
    "gold_block": (0, 100, 0),
    "diamond_block": (15, 70, 15),
    "emerald_block": (-1, 70, 0),
    "lapis_block": (3, 5, 4),
    "redstone_block": (7, 200, 9),
}


class Lab(unittest.TestCase):
    def reader_matches_setblock_on_live_server(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            self.assertTrue(orderrun.wait_loaded(srv, 0, 0))
            self.assertTrue(orderrun.wait_loaded(srv, -1, 0))
            for name, (x, y, z) in PLACED.items():
                reply = srv.command(f"setblock {x} {y} {z} minecraft:{name}")
                print(f"setblock {x} {y} {z} minecraft:{name} -> {reply!r}")
                self.assertIn("Changed the block", reply)
            srv.command("save-all flush")
            srv.stop()

            region = scratch["dir"] / "world" / "region"
            for name, (x, y, z) in PLACED.items():
                got = anvil.block_at(region, x, y, z)
                print(f"block_at {x} {y} {z} -> {got!r}")
                self.assertEqual(got, f"minecraft:{name}")
            unplaced = anvil.block_at(region, 1, 100, 0)
            print(f"block_at 1 100 0 (next to gold) -> {unplaced!r}")
            self.assertNotEqual(unplaced, "minecraft:gold_block")
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
