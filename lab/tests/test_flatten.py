import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flatten

STONE = "minecraft:stone"
GRASS = "minecraft:grass_block"
AIR = "minecraft:air"
IRON = "minecraft:iron_ore"
Y0, Y1 = 54, 70


def column(x, z, ground, name=GRASS, over=None):
    col = {(x, y, z): (STONE if y < ground else AIR) for y in range(Y0, Y1 + 1)}
    col[(x, ground, z)] = name
    for y, n in (over or {}).items():
        col[(x, y, z)] = n
    return col


def world(*columns):
    out = {}
    for c in columns:
        out.update(c)
    return out


class Lab(unittest.TestCase):
    def flatten_marks_tree_water_iron_and_cliff(self):
        blocks = world(
            column(0, 0, 64),
            column(1, 0, 62),
            column(2, 0, 62, "minecraft:oak_log", {63: "minecraft:oak_leaves", 64: "minecraft:oak_leaves"}),
            column(3, 0, 62, "minecraft:water"),
            column(0, 1, 62, GRASS, {59: IRON}),
            column(1, 1, 62, GRASS, {63: "minecraft:poppy"}),
            column(2, 1, 62, GRASS, {55: IRON}),
            column(3, 1, 62),
            column(0, 2, 62),
            column(1, 2, 61),
            column(2, 2, 62),
            column(3, 2, 62),
        )
        self.assertEqual(
            flatten.grid(blocks, 0, 0, 4, 3),
            [
                [1, 1, 3, 2],
                [4, 0, 0, 0],
                [0, 0, 0, 0],
            ],
        )
        self.assertEqual(flatten.TILES["tree"], 3)
        empty = {(0, y, 0): None for y in range(Y0, Y1 + 1)}
        with self.assertRaises(ValueError):
            flatten.grid(empty, 0, 0, 1, 1)

    def missing_column_raises_value_error(self):
        blocks = column(0, 0, 64)
        with self.assertRaises(ValueError) as cm:
            flatten.grid(blocks, 0, 0, 2, 1)
        self.assertIn("(1, 0)", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
