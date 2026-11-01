import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import async_ca


class Lab(unittest.TestCase):
    def rules_independent_of_order(self):
        start = time.perf_counter()
        independent = async_ca.independent_rules(5)
        elapsed = time.perf_counter() - start
        print(f"independent rules on 5-ring: {len(independent)} in {elapsed:.2f}s")
        self.assertEqual(len(independent), 104)
        self.assertIn(110, independent)
        self.assertIn(150, independent)
        self.assertNotIn(90, independent)


if __name__ == "__main__":
    unittest.main()
