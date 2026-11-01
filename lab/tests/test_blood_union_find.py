import random
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blood import union_find


def flood_fill_groups(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen = [False] * n
    groups = 0
    for s in range(n):
        if seen[s]:
            continue
        groups += 1
        seen[s] = True
        stack = [s]
        while stack:
            v = stack.pop()
            for w in adj[v]:
                if not seen[w]:
                    seen[w] = True
                    stack.append(w)
    return groups


class Lab(unittest.TestCase):
    def components_match_flood_fill(self):
        ds = union_find.DisjointSet(10)
        for a, b in [(0, 1), (2, 3), (1, 3), (4, 5), (6, 7), (5, 7), (8, 9)]:
            ds.union(a, b)
        self.assertEqual(ds.groups, 3)
        sizes = Counter(ds.find(i) for i in range(10))
        self.assertEqual(sorted(sizes.values()), [2, 4, 4])

        for seed in range(200):
            rng = random.Random(seed)
            n = 30
            edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(20)]
            ds = union_find.DisjointSet(n)
            for a, b in edges:
                ds.union(a, b)
            self.assertEqual(ds.groups, flood_fill_groups(n, edges), f"seed {seed}")


if __name__ == "__main__":
    unittest.main()
