import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lever

ADMIN_WORDS = ["forceload", "setblock", "fill", "tp", "teleport", "gamerule", "time", "weather",
               "execute", "save-all", "stop", "kill", "summon", "give"]
PLAYER_STEPS = ["timer 5", "kills", "stopper", "giver", "fills", "times", "teleporting",
                "walk 3 north", "break 1 2 3", ""]


class Lab(unittest.TestCase):
    def lever_marks_admin_steps_lab_only(self):
        self.assertEqual(len(lever.ADMIN), 14)
        self.assertEqual(set(lever.ADMIN), set(ADMIN_WORDS))
        for word in ADMIN_WORDS:
            for step in (word, "/" + word, word + " 1 2 3", "/" + word + " 1 2 3"):
                with self.subTest(step=step):
                    self.assertEqual(lever.kinds([step]), ["admin"])
                    self.assertEqual(lever.label([step]), "lab-only")
        for step in PLAYER_STEPS:
            with self.subTest(step=step):
                self.assertEqual(lever.kinds([step]), ["player"])
                self.assertEqual(lever.label([step]), "player-legal")
        self.assertEqual(lever.kinds([]), [])
        self.assertEqual(lever.label([]), "player-legal")
        mixed = ["walk 3 north", "/tp 1 2 3", "break 1 2 3", "kills"]
        self.assertEqual(lever.kinds(mixed), ["player", "admin", "player", "player"])
        self.assertEqual(lever.label(mixed), "lab-only")
        self.assertEqual(lever.kinds(["/fill 0 0 0 1 1 1 air", "give x"]), ["admin", "admin"])


if __name__ == "__main__":
    unittest.main()
