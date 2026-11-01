import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anvil
import nbt
import window

SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
REGION = SERVER / "world" / "region"


class Lab(unittest.TestCase):
    def window_box_and_digest_are_stable(self):
        lo, hi = (0, 0, 16), (3, 2, 19)
        box = window.box(REGION, lo, hi)
        self.assertEqual(len(box), 4 * 3 * 4)
        for x in range(0, 4):
            for z in range(16, 20):
                self.assertEqual(box[(x, 0, z)], "minecraft:bedrock")

        digest = window.fingerprint(box)
        self.assertEqual(digest, window.fingerprint(window.box(REGION, lo, hi)))

        shifted = window.box(REGION, (1, 0, 16), (4, 2, 19))
        self.assertNotEqual(digest, window.fingerprint(shifted))

        reversed_box = dict(reversed(list(box.items())))
        self.assertEqual(digest, window.fingerprint(reversed_box))

        region_file = REGION / "r.0.0.mca"
        lx, lz = anvil.present(region_file)[0]
        _, root = nbt.read(anvil.chunk_data(region_file, lx, lz))
        level = root["Level"]
        self.assertIn(-1, [s["Y"] for s in level["Sections"]])
        blocks = window.chunk_blocks(level)
        self.assertLessEqual(len(blocks), 65536)
        self.assertGreaterEqual(min(y for _, y, _ in blocks), 0)

    def test_box_is_none_in_absent_chunk_and_blocks_in_present_chunk(self):
        box = window.box(REGION, (0, 0, 0), (0, 0, 16))
        self.assertIsNone(box[(0, 0, 0)])
        self.assertEqual(box[(0, 0, 16)], "minecraft:bedrock")


if __name__ == "__main__":
    unittest.main()
