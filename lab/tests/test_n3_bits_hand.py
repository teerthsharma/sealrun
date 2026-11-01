import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import n3_bits


class Lab(unittest.TestCase):
    def bits_lost_square_is_log2_six(self):
        eps = 1e-12
        self.assertAlmostEqual(n3_bits.bits_lost(24, 4), math.log2(6), delta=eps)
        self.assertAlmostEqual(n3_bits.exact_loss([6, 6, 6, 6]), math.log2(6), delta=eps)
        self.assertAlmostEqual(n3_bits.exact_loss([3, 1, 1, 1]), 0.5 * math.log2(3), delta=eps)
        self.assertAlmostEqual(n3_bits.exact_loss([1] * 24), 0, delta=eps)
        self.assertAlmostEqual(n3_bits.bits_lost(6, 6), 0, delta=eps)
        with self.assertRaises(ValueError):
            n3_bits.bits_lost(4, 5)
        with self.assertRaises(ValueError):
            n3_bits.bits_lost(4, 0)
        with self.assertRaises(ValueError):
            n3_bits.exact_loss([])


if __name__ == "__main__":
    unittest.main()
