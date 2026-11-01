import os
import sys
import unittest
from pathlib import Path

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
            self.assertNotIn(None, blocks.values())
            for pos in [(1024, 0, 1024), (1040, 64, 1024), (1055, 255, 1039)]:
                print(f"{pos} -> {blocks[pos]!r}")
        finally:
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
