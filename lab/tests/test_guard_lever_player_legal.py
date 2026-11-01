import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lever


class Lab(unittest.TestCase):
    def test_guard_lever_player_legal(self):
        admin_only = ["/forceload add 0 0", "setblock 1 2 3 minecraft:air"]
        self.assertEqual(lever.kinds(admin_only), ["admin", "admin"])
        self.assertEqual(lever.label(admin_only), "lab-only")

        player_only = ["walk 3 north", "break 1 2 3"]
        self.assertEqual(lever.kinds(player_only), ["player", "player"])
        self.assertEqual(lever.label(player_only), "player-legal")

        mixed = ["walk 3 north", "/forceload add 0 0", "break 1 2 3"]
        self.assertEqual(lever.kinds(mixed), ["player", "admin", "player"])
        self.assertEqual(lever.label(mixed), "lab-only")

        self.assertEqual(lever.kinds(["/setblock 1 2 3 minecraft:air"]),
                         lever.kinds(["setblock 1 2 3 minecraft:air"]))
        self.assertEqual(lever.label(["/setblock 1 2 3 minecraft:air"]), "lab-only")


if __name__ == "__main__":
    unittest.main()
