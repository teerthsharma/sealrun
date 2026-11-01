"""Ticket field and decoration-conflict model (research lane sim, round 3).

Chunk coordinates are (x, z). A forceload ticket at chunk t gives level 31 spreading
as min over tickets of 31 + Chebyshev distance; chunks at level <= 33 (distance <= 2)
end FULL.

Decoration model: when ticket t fires, its batch performs the decoration step of every
chunk within r_dec of t that no earlier ticket in the order already covered. A step at
chunk c writes the 3x3 block around c. Two steps conflict when their write blocks overlap
(Chebyshev distance <= 2). The signature of an order on window W lists, for every
conflicting pair whose two steps both write into W, which step came first, or
'same batch' when one ticket owns both steps.
"""

import json
import os
from itertools import permutations
from math import factorial, log2

BASE_LEVEL = 31
FULL_LEVEL = 33
W_WRITE = 1


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def ball(center, r):
    x, z = center
    return {(x + dx, z + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1)}


def rect(x0, x1, z0, z1):
    return frozenset((x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1))


def level(c, tickets):
    if not tickets:
        return None
    return BASE_LEVEL + min(cheb(c, t) for t in tickets)


def full_set(tickets):
    out = set()
    for t in tickets:
        out |= ball(t, FULL_LEVEL - BASE_LEVEL)
    return out


def owners(order, r_dec):
    own = {}
    for t in order:
        for c in ball(t, r_dec):
            own.setdefault(c, t)
    return own


def writes_into(c, W):
    return any(p in W for p in ball(c, W_WRITE))


def steps_in(order, W, r_dec):
    own = owners(order, r_dec)
    return own, sorted(c for c in own if writes_into(c, W))


def conflicting_pairs(steps):
    for i, a in enumerate(steps):
        for b in steps[i + 1:]:
            if cheb(a, b) <= 2 * W_WRITE:
                yield a, b


def signature(order, W, r_dec):
    own, steps = steps_in(order, W, r_dec)
    rank = {t: i for i, t in enumerate(order)}
    sig = []
    for a, b in conflicting_pairs(steps):
        ta, tb = own[a], own[b]
        if ta == tb:
            label = ("same batch of", ta)
        else:
            label = ("first", ta if rank[ta] < rank[tb] else tb)
        sig.append(((a, b), label))
    return tuple(sig)


def classes(tickets, W, r_dec, orders=None):
    if orders is None:
        orders = list(permutations(tickets))
    out = {}
    for o in orders:
        out.setdefault(signature(o, W, r_dec), []).append(tuple(o))
    return out


def conflict_edges(orders, W, r_dec):
    edges = set()
    for o in orders:
        own, steps = steps_in(o, W, r_dec)
        for a, b in conflicting_pairs(steps):
            if own[a] != own[b]:
                edges.add(frozenset((own[a], own[b])))
    return edges


def _chi(V, E):
    if not E:
        return (-1) ** len(V)
    e = min(E, key=lambda f: sorted(f))
    a, b = sorted(e)
    deleted = E - {e}
    contracted = frozenset(frozenset(a if x == b else x for x in f) for f in deleted)
    return _chi(V, frozenset(deleted)) - _chi(V - {b}, contracted)


def chi_at_minus_one(vertices, edges):
    """|chi_G(-1)| by deletion-contraction; equals the number of acyclic orientations."""
    E = frozenset(frozenset(e) for e in edges)
    return abs(_chi(frozenset(vertices), E))


TRIANGLE = [(64, 64), (67, 64), (64, 67)]

LAYOUTS = {
    "E0": dict(
        tickets=[(64, 64), (65, 64), (64, 65), (65, 65)],
        window=rect(64, 65, 64, 65),
        first=None,
    ),
    "E1": dict(
        tickets=[(64, 64), (69, 64), (74, 64)],
        window=rect(62, 76, 62, 66),
        first=None,
    ),
    "E2": dict(
        tickets=[(64, 64), (65, 64), (64, 65), (65, 65)],
        window=rect(62, 67, 62, 67),
        first=(64, 64),
    ),
    "E3": dict(
        tickets=TRIANGLE,
        window=frozenset(
            c for c in rect(62, 69, 62, 69)
            if any(cheb(c, t) <= FULL_LEVEL - BASE_LEVEL for t in TRIANGLE)
        ),
        first=None,
    ),
    "E4": dict(
        tickets=[(64, 64), (69, 64), (74, 64), (79, 64)],
        window=rect(62, 81, 62, 66),
        first=None,
    ),
}

R_DEC_SET = (2, 3)

MODEL_TEXT = (
    "Ticket level 31 + Chebyshev distance (min over tickets); FULL iff distance <= 2. "
    "Ticket t's batch decorates every chunk within r_dec of t not already covered by an earlier "
    "ticket in the order. A step at c writes its 3x3 block; two steps conflict when their blocks "
    "overlap (Chebyshev <= 2). Signature on window W = for each conflicting pair with both steps "
    "writing into W: the earlier step's ticket, or 'same batch' if one ticket owns both. Classes = "
    "distinct signatures over the enumerated orders. G = ticket graph with an edge t-u when some "
    "order gives a cross-owner conflict inside W; |chi_G(-1)| is its acyclic-orientation count "
    "(the classes if the signature were only the edge orientations)."
)

WHEN_TEXT = (
    "Round 3 (run n3), written before the campaign lane runs E1-E3. Check against measured "
    "classes; a refined prediction goes to quotient_predictions_v2.json, never an edit of this file."
)


def predict_layout(name, spec, r_dec):
    tickets = spec["tickets"]
    W = spec["window"]
    orders = [o for o in permutations(tickets) if spec["first"] is None or o[0] == spec["first"]]
    cls = classes(tickets, W, r_dec, orders)
    n = len(cls)
    chi = chi_at_minus_one(tickets, conflict_edges(orders, W, r_dec))
    class_lists = sorted(
        ([[list(t) for t in o] for o in v] for v in cls.values()),
        key=lambda v: v[0],
    )
    return {
        "layout": name,
        "r_dec": r_dec,
        "w": W_WRITE,
        "k": len(tickets),
        "tickets": [list(t) for t in tickets],
        "window_chunks": len(W),
        "orders_considered": len(orders),
        "predicted_classes": n,
        "classes": class_lists,
        "chi_abs_at_minus_one": chi,
        "bits_lost": round(log2(len(orders) / n), 6),
        "when": WHEN_TEXT,
        "model": MODEL_TEXT,
    }


def predictions():
    records = [predict_layout(name, spec, r) for name, spec in LAYOUTS.items() for r in R_DEC_SET]
    return {
        "lane": "sim",
        "round": 3,
        "run": "n3",
        "version": 1,
        "parameters_swept": {"r_dec": list(R_DEC_SET), "w": W_WRITE,
                             "base_level": BASE_LEVEL, "full_level": FULL_LEVEL},
        "records": records,
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "results", "research", "quotient_predictions.json")
    data = predictions()
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    for r in data["records"]:
        print(r["layout"], r["r_dec"], r["orders_considered"], r["predicted_classes"],
              r["chi_abs_at_minus_one"], r["bits_lost"])


if __name__ == "__main__":
    main()
