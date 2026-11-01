import itertools


def signature(order, family):
    """For each set in family, the ticket of that set that comes first in order."""
    sets = sorted({frozenset(s) for s in family}, key=sorted)
    rank = {t: i for i, t in enumerate(order)}
    return tuple(min(s, key=rank.__getitem__) for s in sets)


def count_classes(k, family):
    """Number of distinct first-ticket signatures over all k! orders."""
    return len({signature(order, family) for order in itertools.permutations(range(k))})


def ball_family(tickets, chunks, R):
    """Nonempty sets of ticket indices within Chebyshev distance R of each chunk."""
    out = set()
    for cx, cz in chunks:
        s = frozenset(i for i, (x, z) in enumerate(tickets) if max(abs(x - cx), abs(z - cz)) <= R)
        if s:
            out.add(s)
    return out
