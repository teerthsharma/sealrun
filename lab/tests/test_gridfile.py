import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gridfile

FIXTURE = Path(__file__).resolve().parents[2] / "crates" / "route" / "tests" / "fixtures" / "contract_4x3.grid"
SAMPLE = [[0, 1, 2, 3], [4, 5, 0, 1], [2, 3, 4, 5]]
HAND = bytes([4, 0, 0, 0, 3, 0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5])


class Lab(unittest.TestCase):
    def gridfile_matches_committed_contract_bytes(self):
        self.assertEqual(gridfile.to_bytes(SAMPLE), HAND)
        self.assertEqual(FIXTURE.read_bytes(), HAND)
        self.assertEqual(FIXTURE.read_bytes(), gridfile.to_bytes(SAMPLE))
        with self.assertRaises(ValueError):
            gridfile.to_bytes([])
        with self.assertRaises(ValueError):
            gridfile.to_bytes([[0, 1], [2]])
        with self.assertRaises(ValueError):
            gridfile.to_bytes([[0, 6]])


if __name__ == "__main__":
    unittest.main()
