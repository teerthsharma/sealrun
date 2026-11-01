import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import first_ticket_classes as ftc
from n3_law import count_classes


class Lab(unittest.TestCase):
    def counts_24_14_20_4(self):
        self.assertEqual(ftc.classes(4, ftc.all_subsets(4)), 24)
        self.assertEqual(ftc.classes(4, ftc.intervals(4)), 14)
        self.assertEqual(ftc.classes(4, ftc.cyclic_intervals(4)), 20)
        self.assertEqual(ftc.classes(4, ftc.whole(4)), 4)
        self.assertEqual(ftc.classes(3, ftc.all_subsets(3)), 6)
        self.assertEqual(ftc.classes(3, ftc.intervals(3)), 5)
        self.assertEqual(ftc.classes(3, ftc.cyclic_intervals(3)), 6)
        self.assertEqual(ftc.classes(3, ftc.whole(3)), 3)
        for n, fam in [
            (4, ftc.all_subsets(4)),
            (4, ftc.intervals(4)),
            (4, ftc.cyclic_intervals(4)),
            (4, ftc.whole(4)),
        ]:
            self.assertEqual(ftc.classes(n, fam), count_classes(n, fam))


if __name__ == "__main__":
    unittest.main()
