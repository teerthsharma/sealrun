# SOURCE: https://en.wikipedia.org/wiki/Permutohedron "The number of edges is (n − 1) n!/2"
from collections import Counter
from itertools import permutations


def elements(n):
    return list(permutations(range(1, n + 1)))


def inversions(p):
    pos = {v: i for i, v in enumerate(p)}
    return frozenset((a, b) for a in p for b in p if a < b and pos[b] < pos[a])


def below(a, b):
    return inversions(a) <= inversions(b)


def rank(p):
    return len(inversions(p))


def covers(elems):
    less = {(a, b) for a in elems for b in elems if a != b and below(a, b)}
    return [(a, b) for (a, b) in less if not any((a, c) in less and (c, b) in less for c in elems)]
