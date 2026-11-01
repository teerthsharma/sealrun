import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import ticket_levels

RESULT = Path(__file__).resolve().parents[1] / "results" / "forceload_tile.json"


class Lab(unittest.TestCase):
    def full_tile_is_25_chunks(self):
        tile = ticket_levels.full_tile()
        block = {(dx, dz) for dx in range(-2, 3) for dz in range(-2, 3)}
        self.assertEqual(len(tile), 25)
        self.assertEqual(tile, block)
        self.assertFalse(any(max(abs(x), abs(z)) == 3 for x, z in tile))
        with open(RESULT) as f:
            grid = json.load(f)["grid"]
        measured = {tuple(map(int, k.split(","))) for k, v in grid.items() if v == "full"}
        self.assertEqual(tile, measured)


if __name__ == "__main__":
    unittest.main()
