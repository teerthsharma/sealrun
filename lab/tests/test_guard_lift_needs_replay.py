import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aim


class Lab(unittest.TestCase):
    def test_guard_lift_needs_replay(self):
        with self.subTest("two replays equal to found, above default: accepted"):
            self.assertEqual(aim.accept(9, [9, 9], 5)["accepted"], True)
        refusals = [
            ("one replay", 9, [9], 5),
            ("replay differs", 9, [9, 8], 5),
            ("no default", 9, [9, 9], None),
            ("no lift", 5, [5, 5], 5),
        ]
        for name, found, replays, default in refusals:
            with self.subTest(f"refused: {name}"):
                result = aim.accept(found, replays, default)
                self.assertEqual(result["accepted"], False)
                self.assertIsInstance(result.get("reason"), str)
                self.assertTrue(result["reason"].strip())


if __name__ == "__main__":
    unittest.main()
