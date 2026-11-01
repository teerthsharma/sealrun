# SOURCE: https://arxiv.org/abs/0707.2360 "exactly 104 of the 256 Wolfram rules give rise to a pi-independent ACA"
from itertools import permutations, product


def step(rule, state, i):
    l, c, r = state[i - 1], state[i], state[(i + 1) % len(state)]
    return state[:i] + ((rule >> (4 * l + 2 * c + r)) & 1,) + state[i + 1:]


def compose(rule, order, n):
    def run(x):
        for i in order:
            x = step(rule, x, i)
        return x
    return {x: run(x) for x in product((0, 1), repeat=n)}


def periodic(f):
    current = set(f)
    while (image := {f[x] for x in current}) != current:
        current = image
    return current


def independent_rules(n=5):
    orders = list(permutations(range(n)))
    return [r for r in range(256) if len({frozenset(periodic(compose(r, o, n))) for o in orders}) == 1]
