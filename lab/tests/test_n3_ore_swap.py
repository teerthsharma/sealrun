import itertools
import json
import unittest
from pathlib import Path

CHUNK = "64,64"


class Lab(unittest.TestCase):
    def ore_swap_conserves_iron_plus_gold(self):
        path = Path(__file__).resolve().parents[1] / "results" / "order_square.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("classes", data, "missing top-level key 'classes'")
        worlds = data["classes"]
        self.assertGreater(len(worlds), 1, "need at least two worlds to compare")
        counts = []
        for i, w in enumerate(worlds):
            self.assertIn("ores", w, f"class {i} missing key 'ores'")
            self.assertIn(CHUNK, w["ores"], f"class {i} ores missing chunk '{CHUNK}'")
            for ore in ("iron", "gold"):
                self.assertIn(ore, w["ores"][CHUNK], f"class {i} chunk '{CHUNK}' missing key '{ore}'")
            counts.append((w["ores"][CHUNK]["iron"], w["ores"][CHUNK]["gold"]))
        any_iron_change = False
        for (a, wa), (b, wb) in itertools.combinations(enumerate(counts), 2):
            d_iron = wb[0] - wa[0]
            d_gold = wb[1] - wa[1]
            print(f"pair class {a} -> class {b}: d_iron {d_iron} d_gold {d_gold}")
            with self.subTest(pair=(a, b)):
                self.assertEqual(d_iron + d_gold, 0, f"pair {a},{b}: d_iron {d_iron} + d_gold {d_gold} != 0")
            if d_iron != 0:
                any_iron_change = True
        self.assertTrue(any_iron_change, "no pair has d_iron != 0; the swap was never observed")


if __name__ == "__main__":
    unittest.main()
