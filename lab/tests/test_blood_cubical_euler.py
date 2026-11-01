import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import cubical_euler


def pieces(cells):
    seen, count = set(), 0
    for start in sorted(cells):
        if start in seen:
            continue
        count += 1
        seen.add(start)
        stack = [start]
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in cells and n not in seen:
                        seen.add(n)
                        stack.append(n)
    return count


def holes(cells, w, h):
    empty = {(x, y) for x in range(-1, w + 1) for y in range(-1, h + 1)} - cells
    seen, components = set(), 0
    for start in sorted(empty):
        if start in seen:
            continue
        components += 1
        seen.add(start)
        stack = [start]
        while stack:
            x, y = stack.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in empty and n not in seen:
                    seen.add(n)
                    stack.append(n)
    return components - 1


WORKED = [
    ("solid 2 by 2", {(0, 0), (1, 0), (0, 1), (1, 1)}, 2, 2, 1),
    ("ring of 8 around a hole", {(x, y) for x in range(3) for y in range(3)} - {(1, 1)}, 3, 3, 0),
    ("two separate cells", {(0, 0), (2, 0)}, 3, 1, 2),
]


class Lab(unittest.TestCase):
    def vertices_edges_faces_equal_b0_minus_b1(self):
        for name, cells, w, h, expected in WORKED:
            v, e, f = cubical_euler.cell_counts(cells)
            print(f"{name}: V={v} E={e} F={f} V-E+F={v - e + f}")
            with self.subTest(example=name):
                self.assertEqual(cubical_euler.euler(cells), expected)
                self.assertEqual(pieces(cells) - holes(cells, w, h), expected)
        for seed in range(100):
            rng = random.Random(seed)
            cells = {(x, y) for x in range(6) for y in range(6) if rng.random() < 0.5}
            with self.subTest(seed=seed):
                self.assertEqual(
                    cubical_euler.euler(cells),
                    pieces(cells) - holes(cells, 6, 6),
                )


if __name__ == "__main__":
    unittest.main()
