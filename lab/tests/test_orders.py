import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import orders

OUT = ROOT / "results" / "order_squares_more.json"


def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class Lab(unittest.TestCase):
    def square_orders_are_24_distinct_permutations(self):
        for cx, cz in orders.SQUARES:
            found = orders.square_orders(cx, cz)
            self.assertEqual(len(found), 24)
            self.assertTrue(all(isinstance(o, tuple) for o in found))
            self.assertEqual(len(set(found)), 24)
            for o in found:
                self.assertEqual(sorted(o), sorted(orders.square(cx, cz)))
            self.assertEqual(found[0], tuple(orders.square(cx, cz)))

    def squares_are_at_least_32_chunks_apart(self):
        chunks = {sq: orders.square(*sq) for sq in orders.SQUARES}
        for a in orders.SQUARES:
            self.assertGreaterEqual(min(chebyshev(p, (0, 0)) for p in chunks[a]), 32)
            for b in orders.SQUARES:
                if a < b:
                    gap = min(chebyshev(p, q) for p in chunks[a] for q in chunks[b])
                    self.assertGreaterEqual(gap, 32, f"{a} vs {b}")

    def table_has_72_not_run_rows(self):
        t = orders.table()
        self.assertEqual(t["squares"], [list(s) for s in orders.SQUARES])
        self.assertEqual(len(t["rows"]), 72)
        for row in t["rows"]:
            self.assertEqual(row["status"], "not run")
            self.assertIsNone(row["differing_blocks"])
            self.assertIsNone(row["diamonds"])

    def committed_json_equals_table(self):
        self.assertEqual(json.loads(OUT.read_text()), orders.table())


if __name__ == "__main__":
    unittest.main()
