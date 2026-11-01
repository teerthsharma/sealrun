"""Start-to-iron join price vs the minimax (bottleneck) path and a union-find sweep.

Convention (terrain_persistence.json): vertices are walkable tile centres, edges join
4-neighbours; a tile is walkable at price T iff its cost <= T (air 0, water s, stone d,
tree and iron never walkable). The join price is the least T at which the start
component is 4-adjacent to an iron tile.
"""
import heapq
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


def neighbours4(i, w, h):
    x, y = i % w, i // w
    for X, Y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= X < w and 0 <= Y < h:
            yield Y * w + X


def price_of(cells, s, d):
    table = {AIR: 0, WATER: s, STONE: d}
    return [table.get(c) for c in cells]


def iron_adjacent(w, h, cells):
    out = set()
    for i, c in enumerate(cells):
        if c == IRON:
            out.update(neighbours4(i, w, h))
    return out


def minimax_join(w, h, cost, start, target):
    dist = {start: cost[start]}
    heap = [(cost[start], start)]
    while heap:
        v, i = heapq.heappop(heap)
        if v > dist[i]:
            continue
        for j in neighbours4(i, w, h):
            if cost[j] is None:
                continue
            nv = max(v, cost[j])
            if nv < dist.get(j, float("inf")):
                dist[j] = nv
                heapq.heappush(heap, (nv, j))
    reached = [dist[t] for t in target if t in dist]
    return min(reached) if reached else None


def sweep_join(w, h, cost, start, target, T_grid):
    n = w * h
    for T in T_grid:
        walk = [cost[i] is not None and cost[i] <= T for i in range(n)]
        parent = list(range(n))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(n):
            if walk[i]:
                for j in neighbours4(i, w, h):
                    if walk[j]:
                        parent[find(i)] = find(j)
        if walk[start] and any(walk[t] and find(t) == find(start) for t in target):
            return T
    return None


class Lab(unittest.TestCase):
    def start_iron_join_price_equals_bottleneck_path(self):
        data = json.loads((RES / "terrain_persistence.json").read_text())
        w, h, cells = load_grid(ROOT / data["grid"])
        self.assertEqual([w, h], data["size"])
        sx, sy = data["start"]
        start = sy * w + sx
        self.assertEqual(cells[start], AIR)
        target = iron_adjacent(w, h, cells)
        self.assertTrue(target)
        rows = []
        for name, sysrep in data["systems"].items():
            s, d = sysrep["s"], sysrep["d"]
            saved = sysrep["bottleneck_T"]["iron_touch"]
            cost = price_of(cells, s, d)
            mm = minimax_join(w, h, cost, start, target)
            sw = sweep_join(w, h, cost, start, target, data["T_grid"])
            print(f"{name}  s={s} d={d}  saved={saved} minimax={mm} sweep={sw}")
            rows.append((name, saved, mm, sw))
        for name, saved, mm, sw in rows:
            self.assertEqual(mm, saved, f"{name}: minimax != saved join price")
            self.assertEqual(sw, mm, f"{name}: union-find sweep != minimax")


if __name__ == "__main__":
    unittest.main()
