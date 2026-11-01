import gzip
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anvil
import nbt
import orderrun
import orders
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))


class Lab(unittest.TestCase):
    def far_chunk_absent_before_and_full_after_forceload(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            cx, cz = orders.SQUARES[0]
            region = scratch["dir"] / "world" / "region"

            srv.command("save-all flush")
            before = anvil.chunk_status(region, cx, cz)
            print(f"before chunk ({cx}, {cz}) -> {before!r}")
            self.assertIsNone(before)

            level = nbt.read(gzip.decompress((scratch["dir"] / "world" / "level.dat").read_bytes()))[1]["Data"]
            spawn_x, spawn_z = level["SpawnX"], level["SpawnZ"]
            distance = max(abs(cx - (spawn_x >> 4)), abs(cz - (spawn_z >> 4)))
            print(f"spawn ({spawn_x}, {spawn_z}) distance {distance} chunks")
            self.assertGreaterEqual(distance, 50)

            self.assertTrue(orderrun.wait_loaded(srv, cx, cz))
            srv.command("save-all flush")
            srv.stop()

            after = anvil.chunk_status(region, cx, cz)
            print(f"after chunk ({cx}, {cz}) -> {after!r}")
            self.assertEqual(after, "full")
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
