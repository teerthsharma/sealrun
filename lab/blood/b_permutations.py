# SOURCE: https://arxiv.org/abs/math/0609184
"""B-permutations (Postnikov, Reiner, Williams, Sec. 8.2, Def. 8.7).

w is a B-permutation when, for each i, w(i) and max{w(1..i)} "lie in the same connected
component" of B restricted to {w(1..i)}. Sec. 8.1-8.2: these are in bijection with the
B-trees, which index the vertices of the nestohedron P_B, so count(n, B) is that vertex count.
"""
from itertools import permutations


def components(B, U):
    comps = [{u} for u in U]
    for I in B:
        if I <= U:
            merged = set().union(*[c for c in comps if c & I], I)
            comps = [c for c in comps if not c & I] + [merged]
    return comps


def is_b_permutation(w, B):
    return all(
        any(w[i - 1] in c and max(w[:i]) in c for c in components(B, set(w[:i])))
        for i in range(1, len(w) + 1)
    )


def count(n, B):
    return sum(is_b_permutation(w, B) for w in permutations(range(1, n + 1)))
