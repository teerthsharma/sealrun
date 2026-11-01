import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import edits

LOADED = {(0, -1), (-2, -1)}


class Lab(unittest.TestCase):
    def edit_commands_stay_inside_loaded_chunks(self):
        got = edits.commands(
            [("break", 3, 64, -5, None), ("place", -17, 70, -1, "minecraft:stone")],
            LOADED,
        )
        self.assertEqual(got, ["setblock 3 64 -5 minecraft:air", "setblock -17 70 -1 minecraft:stone"])

        self.assertEqual(
            edits.commands([("break", -1, 0, -16, None)], {(-1, -1)}),
            ["setblock -1 0 -16 minecraft:air"],
        )

        with self.assertRaises(ValueError) as cm:
            edits.commands(
                [
                    ("place", 5, 64, -5, "minecraft:stone"),
                    ("break", 16, 64, -1, None),
                    ("place", 3, 64, -5, "minecraft:stone"),
                ],
                LOADED,
            )
        self.assertIn("(1, -1)", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
