import os
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import flatten
import serverdir
import spawn_area

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
HALF = 48


class Lab(unittest.TestCase):
    def test_boot_spawn_area_has_tree_stone_iron(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        try:
            blocks, (spawn_x, spawn_z) = spawn_area.read(scratch, half=HALF)
            none = sum(1 for v in blocks.values() if v is None)
            print(f"spawn ({spawn_x}, {spawn_z}) half {HALF} cells {len(blocks)}")
            print(f"None cells {none}")
            self.assertEqual(none, 0)
            tiles = flatten.grid(blocks, spawn_x - HALF, spawn_z - HALF, 2 * HALF + 1, 2 * HALF + 1)
            counts = Counter(t for row in tiles for t in row)
            for name, t in flatten.TILES.items():
                print(f"tile {name} {counts[t]}")
            for kind in ("tree", "stone", "iron"):
                self.assertGreaterEqual(counts[flatten.TILES[kind]], 1, f"no {kind} tile")
        finally:
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
