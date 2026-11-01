import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gridfile
import seed7_area

SPAWN = (100, 200)
HEADER = bytes([64, 0, 0, 0, 64, 0, 0, 0])


def synthetic_blocks():
    blocks = {}
    for x in range(68, 132):
        for z in range(168, 232):
            for y in range(60, 64):
                blocks[(x, y, z)] = "minecraft:stone"
            blocks[(x, 64, z)] = "minecraft:grass_block"
    blocks[(70, 65, 170)] = "minecraft:oak_log"
    blocks[(90, 64, 190)] = "minecraft:water"
    return blocks


class Lab(unittest.TestCase):
    def area_script_turns_window_into_grid_bytes(self):
        blocks = synthetic_blocks()
        expected = bytearray(HEADER + bytes(64 * 64))
        expected[8 + 2 + 64 * 2] = 3
        expected[8 + 22 + 64 * 22] = 2

        rows = seed7_area.rows(blocks, SPAWN)
        self.assertEqual(len(rows), 64)
        self.assertEqual(rows[2][2], 3)
        self.assertEqual(rows[22][22], 2)

        data = gridfile.to_bytes(rows)
        self.assertEqual(len(data), 4104)
        self.assertEqual(data, bytes(expected))

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "seed7.grid"
            seed7_area.write(blocks, SPAWN, path)
            self.assertEqual(path.read_bytes(), bytes(expected))

        for y in range(60, 65):
            del blocks[(131, y, 231)]
        with self.assertRaises(ValueError):
            seed7_area.rows(blocks, SPAWN)


if __name__ == "__main__":
    unittest.main()
