import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ticket_world  # noqa: E402


class Lab(unittest.TestCase):
    def test_window_and_reach(self):
        chunks = ticket_world.parse_window("62,62,69,69")
        self.assertEqual(len(chunks), 64)
        near, far = ticket_world.reach(chunks, [(64, 64), (67, 64), (64, 67)])
        self.assertIn((69, 66), near)
        self.assertIn((69, 69), far)
        self.assertEqual(len(near) + len(far), 64)

    def test_dump_is_fixed_order_with_none(self):
        text = ticket_world.dump({(1, 0, 0): "minecraft:stone", (0, 0, 0): None})
        self.assertEqual(text.split("\n"), [ticket_world.NONE, "minecraft:stone"])


if __name__ == "__main__":
    unittest.main()
