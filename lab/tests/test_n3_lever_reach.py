import json
import unittest
from pathlib import Path

CHUNK = "64,64"
ORES = ("iron", "gold", "diamond")


class Lab(unittest.TestCase):
    def lever_reaches_iron_not_diamonds(self):
        path = Path(__file__).resolve().parents[1] / "results" / "order_square.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("classes", data, "missing top-level key 'classes'")
        worlds = data["classes"]
        self.assertEqual(len(worlds), 4, "expected the 4 measured worlds of the square")
        for i, w in enumerate(worlds):
            self.assertIn("ores", w, f"world {i} missing key 'ores'")
            self.assertIn(CHUNK, w["ores"], f"world {i} ores missing chunk '{CHUNK}'")
            for ore in ORES:
                self.assertIn(ore, w["ores"][CHUNK], f"world {i} chunk '{CHUNK}' missing '{ore}'")
        chunks = sorted(worlds[0]["ores"])
        for ch in chunks:
            for i, w in enumerate(worlds):
                self.assertIn(ch, w["ores"], f"world {i} ores missing chunk '{ch}'")

        for i, w in enumerate(worlds):
            c = w["ores"][CHUNK]
            print(f"world {i} order {w['order']}: iron {c['iron']} gold {c['gold']} diamond {c['diamond']}")

        def spreads(ch):
            out = {}
            for ore in ORES:
                vals = [w["ores"][ch][ore] for w in worlds]
                out[ore] = max(vals) - min(vals)
            return out

        for ch in chunks:
            if ch == CHUNK:
                continue
            s = spreads(ch)
            print(f"chunk {ch}: iron spread {s['iron']} gold spread {s['gold']} diamond spread {s['diamond']}")

        s = spreads(CHUNK)
        print(f"chunk {CHUNK}: iron spread {s['iron']} gold spread {s['gold']} diamond spread {s['diamond']}")
        self.assertEqual(s["iron"], 2, f"chunk {CHUNK} iron spread {s['iron']} != 2")
        self.assertEqual(s["gold"], 2, f"chunk {CHUNK} gold spread {s['gold']} != 2")
        self.assertEqual(s["diamond"], 0, f"chunk {CHUNK} diamond spread {s['diamond']} != 0")


if __name__ == "__main__":
    unittest.main()
