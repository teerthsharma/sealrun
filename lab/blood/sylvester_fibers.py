# SOURCE: https://arxiv.org/abs/math/0401089 "the Robinson-Schensted insertion being replaced by the binary search tree insertion."
from itertools import permutations


def insert(tree, x):
    if tree is None:
        return (None, x, None)
    left, root, right = tree
    if x < root:
        return (insert(left, x), root, right)
    return (left, root, insert(right, x))


def shape(word):
    tree = None
    for x in word:
        tree = insert(tree, x)
    return tree


def classes(n):
    groups = {}
    for p in permutations(range(n)):
        groups.setdefault(shape(p), []).append(p)
    return list(groups.values())
