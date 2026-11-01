# SOURCE: https://mathworld.wolfram.com/AcyclicOrientation.html "the number of acyclic orientations is" (-1)^n π_G(-1) (Stanley 1973)
from fractions import Fraction
from itertools import product


def acyclic_count(n, edges):
    total = 0
    for flips in product((0, 1), repeat=len(edges)):
        arcs = [(w, v) if f else (v, w) for (v, w), f in zip(edges, flips)]
        if _is_acyclic(n, arcs):
            total += 1
    return total


def _is_acyclic(n, arcs):
    indeg = [0] * n
    out = [[] for _ in range(n)]
    for v, w in arcs:
        out[v].append(w)
        indeg[w] += 1
    ready = [v for v in range(n) if indeg[v] == 0]
    seen = 0
    while ready:
        v = ready.pop()
        seen += 1
        for w in out[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                ready.append(w)
    return seen == n


def chromatic_at(n, edges, x):
    # ponytail: brute colourings + Lagrange interpolation, exponential; fine for n<=5, ceiling is k^n loops
    points = []
    for k in range(n + 1):
        proper = sum(
            1
            for col in product(range(k), repeat=n)
            if all(col[v] != col[w] for v, w in edges)
        )
        points.append((k, proper))
    total = Fraction(0)
    for i, (xi, yi) in enumerate(points):
        term = Fraction(yi)
        for j, (xj, _) in enumerate(points):
            if j != i:
                term *= Fraction(x - xj, xi - xj)
        total += term
    return total
