import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blockdiff


class Lab(unittest.TestCase):
    def blockdiff_finds_changed_added_and_missing(self):
        a = {(-5, 64, -7): "minecraft:stone", (0, 0, 0): "minecraft:dirt", (9, 9, 9): "minecraft:gold_ore"}
        same = blockdiff.diff(a, dict(a))
        self.assertEqual(same, {"changed": [], "added": [], "missing": []})

        b = {(-5, 64, -7): "minecraft:deepslate", (0, 0, 0): "minecraft:dirt", (-1, 0, 0): "minecraft:coal_ore", (-2, 1, 0): "minecraft:diamond_ore"}
        got = blockdiff.diff(a, b)
        self.assertEqual(got["changed"], [((-5, 64, -7), "minecraft:stone", "minecraft:deepslate")])
        self.assertEqual(got["added"], [((-2, 1, 0), "minecraft:diamond_ore"), ((-1, 0, 0), "minecraft:coal_ore")])
        self.assertEqual(got["missing"], [((9, 9, 9), "minecraft:gold_ore")])

        mirror = blockdiff.diff(b, a)
        self.assertEqual(mirror["changed"], [((-5, 64, -7), "minecraft:deepslate", "minecraft:stone")])
        self.assertEqual(mirror["added"], [((9, 9, 9), "minecraft:gold_ore")])
        self.assertEqual(mirror["missing"], [((-2, 1, 0), "minecraft:diamond_ore"), ((-1, 0, 0), "minecraft:coal_ore")])

        full = {(x, y, z): "minecraft:stone" for x in range(16) for y in range(256) for z in range(16)}
        flipped = dict(full)
        flipped[(7, 100, 9)] = "minecraft:air"
        self.assertEqual(len(full), 65536)
        self.assertEqual(blockdiff.diff(full, dict(full)), {"changed": [], "added": [], "missing": []})
        self.assertEqual(blockdiff.diff(full, flipped), {"changed": [((7, 100, 9), "minecraft:stone", "minecraft:air")], "added": [], "missing": []})


if __name__ == "__main__":
    unittest.main()
