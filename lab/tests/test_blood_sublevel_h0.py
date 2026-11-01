import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import sublevel_h0


def local_minima(heights):
    n = len(heights)
    count = 0
    for i in range(n):
        left_ok = i == 0 or heights[i] < heights[i - 1]
        right_ok = i == n - 1 or heights[i] < heights[i + 1]
        if left_ok and right_ok:
            count += 1
    return count


class Lab(unittest.TestCase):
    def elder_rule_example(self):
        finite, essential = sublevel_h0.h0_pairs([1, 5, 2, 6, 3])
        self.assertEqual(finite, [(2, 5), (3, 6)])
        self.assertEqual(essential, [1])
        for seed in range(50):
            heights = random.Random(seed).sample(range(1000), 8)
            finite, _ = sublevel_h0.h0_pairs(heights)
            self.assertEqual(len(finite), local_minima(heights) - 1)


if __name__ == "__main__":
    unittest.main()
