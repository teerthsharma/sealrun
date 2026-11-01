import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import trace_counts


class Lab(unittest.TestCase):
    def commuting_letters_series(self):
        only_a_b_commute = {("a", "b"), ("b", "a")}
        counts = trace_counts.count_by_length(("a", "b", "c"), only_a_b_commute, 4)
        self.assertEqual(counts, [1, 3, 8, 21, 55])
        self.assertEqual(counts, trace_counts.series_coefficients([1, -3, 1], 4))

        all_commute = {(x, y) for x in "abc" for y in "abc" if x != y}
        self.assertEqual(trace_counts.count_by_length(("a", "b", "c"), all_commute, 3)[3], 10)


if __name__ == "__main__":
    unittest.main()
