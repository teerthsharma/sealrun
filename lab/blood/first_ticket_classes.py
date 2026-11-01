# SOURCE: https://arxiv.org/abs/math/0507163 "These polytopes are constructed as Minkowski sums of simplices."
"""Count the distinct first-element maps S -> min_order(S) over all orders, for a family of sets S."""
import itertools


def classes(n, family):
    orders = itertools.permutations(range(n))
    return len({tuple(next(x for x in o if x in s) for s in family) for o in orders})


def all_subsets(n):
    return [frozenset(c) for k in range(1, n + 1) for c in itertools.combinations(range(n), k)]


def intervals(n):
    return [frozenset(range(i, j)) for i in range(n) for j in range(i + 1, n + 1)]


def cyclic_intervals(n):
    return [frozenset((i + t) % n for t in range(k)) for i in range(n) for k in range(1, n + 1)]


def whole(n):
    return [frozenset(range(n))]
