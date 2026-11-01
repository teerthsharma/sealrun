"""Euler characteristic of the terrain sublevel complex vs the saved b0, b1.

Convention (terrain_persistence.json): vertices are walkable tile centres, edges join
4-neighbours, faces are full 2x2 blocks; a tile is walkable iff cost <= T, with
cost air 0, water s, stone d, tree and iron never walkable.
"""
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "lab" / "results" / "research"
AIR, STONE, WATER, TREE, IRON, GOAL = range(6)


def load_grid(path):
    raw = path.read_bytes()
    w, h = struct.unpack("<II", raw[:8])
    cells = list(raw[8:])
    assert len(cells) == w * h
    return w, h, cells


def walkable_points(w, h, cells, s, d, T):
    cost = {AIR: 0, WATER: s, STONE: d}
    return {
        (x, y)
        for y in range(h)
        for x in range(w)
        if cells[y * w + x] in cost and cost[cells[y * w + x]] <= T
    }


def cubical_counts(points):
    V = len(points)
    E = sum(1 for (x, y) in points if (x + 1, y) in points) + sum(
        1 for (x, y) in points if (x, y + 1) in points
    )
    F = sum(
        1
        for (x, y) in points
        if (x + 1, y) in points and (x, y + 1) in points and (x + 1, y + 1) in points
    )
    return V, E, F


class Lab(unittest.TestCase):
    def terrain_euler_matches_betti(self):
        data = json.loads((RES / "terrain_persistence.json").read_text())
        w, h, cells = load_grid(ROOT / data["grid"])
        self.assertEqual([w, h], data["size"])
        rows_out = []
        bad = []
        for name, sysrep in data["systems"].items():
            s, d = sysrep["s"], sysrep["d"]
            print(f"\n{name}  s={s} d={d}")
            print(f"{'T':>3} {'V':>5} {'E':>5} {'F':>5} {'chi':>5} {'b0':>5} {'b1':>5}  ok")
            for row in sysrep["table"]:
                t = row["T"]
                V, E, F = cubical_counts(walkable_points(w, h, cells, s, d, t))
                chi = V - E + F
                ok = chi == row["b0"] - row["b1"]
                print(f"{t:>3} {V:>5} {E:>5} {F:>5} {chi:>5} {row['b0']:>5} {row['b1']:>5}  {'yes' if ok else 'NO'}")
                rows_out.append((name, t))
                if not ok:
                    bad.append((name, t, chi, row["b0"] - row["b1"]))
        print(f"\nlevels checked: {len(rows_out)}, mismatches: {len(bad)}")
        self.assertGreaterEqual(len(rows_out), 3)
        self.assertEqual(bad, [], f"chi != b0 - b1 at (system, T, chi, b0-b1): {bad}")


if __name__ == "__main__":
    unittest.main()
