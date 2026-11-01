# SOURCE: https://en.wikipedia.org/wiki/Persistent_homology "connecting the birth and the death values"
from blood import union_find


def h0_pairs(heights):
    """Sublevel H0 on a path, elder rule of Edelsbrunner, Letscher and Zomorodian (2002)."""
    n = len(heights)
    present = [False] * n
    ds = union_find.DisjointSet(n)
    birth = list(heights)
    pairs = []
    for v in sorted(range(n), key=lambda i: heights[i]):
        present[v] = True
        t = heights[v]
        roots = sorted({ds.find(w) for w in (v - 1, v + 1) if 0 <= w < n and present[w]}, key=lambda r: birth[r])
        if not roots:
            continue
        for r in roots[1:]:
            pairs.append((birth[r], t))
        elder = birth[roots[0]]
        for r in roots:
            ds.union(v, r)
        birth[ds.find(v)] = elder
    essential = sorted({birth[ds.find(v)] for v in range(n)})
    return sorted(pairs), essential
