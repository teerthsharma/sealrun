import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ores

ZERO = {ore: 0 for ore in ores.ORES}


class Lab(unittest.TestCase):
    def ore_tally_counts_per_chunk(self):
        self.assertEqual(ores.ORES, ("diamond", "iron", "coal", "gold", "lapis", "redstone", "emerald"))

        floor = {(-1, 5, 3): "minecraft:diamond_ore", (16, 5, 3): "minecraft:emerald_ore"}
        got = ores.tally(floor)
        self.assertEqual(got[(-1, 0)], {**ZERO, "diamond": 1})
        self.assertEqual(got[(1, 0)], {**ZERO, "emerald": 1})

        decoys = {
            (0, 0, 0): "minecraft:diamond_block",
            (0, 1, 0): "minecraft:nether_gold_ore",
            (0, 2, 0): "minecraft:deepslate_diamond_ore",
        }
        self.assertEqual(ores.tally(decoys), {(0, 0): ZERO})

        self.assertEqual(ores.tally({(32, 0, 0): "minecraft:stone"}), {(2, 0): ZERO})

        box = {}
        for x in range(0, 16):
            box[(x, 0, 0)] = "minecraft:stone"
        box[(0, 1, 0)] = "minecraft:diamond_ore"
        box[(1, 1, 0)] = "minecraft:diamond_ore"
        box[(2, 1, 0)] = "minecraft:diamond_ore"
        for x in range(0, 5):
            box[(x, 2, 0)] = "minecraft:coal_ore"
        for x in range(16, 32):
            box[(x, 0, 0)] = "minecraft:stone"
        box[(16, 1, 0)] = "minecraft:emerald_ore"
        self.assertEqual(
            ores.tally(box),
            {
                (0, 0): {**ZERO, "diamond": 3, "coal": 5},
                (1, 0): {**ZERO, "emerald": 1},
            },
        )


if __name__ == "__main__":
    unittest.main()
