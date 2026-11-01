import itertools
import json
import math
import os
from datetime import datetime

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull


def rect(x0, z0, x1, z1):
    return {(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def stamp_set(tickets, c, R):
    return frozenset(i for i, t in enumerate(tickets) if cheb(t, c) <= R)


def family(tickets, window, R):
    out = set()
    for c in window:
        S = stamp_set(tickets, c, R)
        if S:
            out.add(S)
    return out


def overlap_hits(c, d, W):
    return any(
        (x, z) in W
        for x in range(max(c[0], d[0]) - 1, min(c[0], d[0]) + 2)
        for z in range(max(c[1], d[1]) - 1, min(c[1], d[1]) + 2)
    )


def family_prime(tickets, window, R):
    W = set(window)
    F = family(tickets, W, R)
    near = {(x + dx, z + dz) for x, z in W for dx in range(-3, 4) for dz in range(-3, 4)}
    stamp = {c: stamp_set(tickets, c, R) for c in near}
    dom = [c for c in near if stamp[c]]
    extra = set()
    for c in dom:
        for d in dom:
            if c == d or cheb(c, d) > 2:
                continue
            if not (c in W or d in W or overlap_hits(c, d, W)):
                continue
            for t in stamp[c]:
                for u in stamp[d]:
                    if t != u:
                        extra.add(frozenset((t, u)))
    return F | extra


def classes_by_min(tickets, F):
    k = len(tickets)
    Fl = sorted(F, key=lambda S: sorted(S))
    groups = {}
    for sigma in itertools.permutations(range(k)):
        pos = {t: i for i, t in enumerate(sigma)}
        key = tuple(min(S, key=pos.__getitem__) for S in Fl)
        groups.setdefault(key, []).append(list(sigma))
    return groups


def vertex_points(F, k):
    pts = set()
    for sigma in itertools.permutations(range(k)):
        pos = {t: i for i, t in enumerate(sigma)}
        v = [0] * k
        for S in F:
            v[min(S, key=pos.__getitem__)] += 1
        pts.add(tuple(v))
    return pts


def hull_vertex_count(points):
    P = np.array(sorted(points), dtype=float)
    if len(P) == 1:
        return 1
    C = P - P.mean(axis=0)
    _, s, vt = np.linalg.svd(C)
    d = int((s > 1e-9).sum())
    if d == 0:
        return 1
    if d == 1:
        return 2
    Q = C @ vt[:d].T
    return len(ConvexHull(Q).vertices)


def lp_vertex_count(points):
    P = [np.array(p, dtype=float) for p in sorted(points)]
    if len(P) == 1:
        return 1
    k = len(P[0])
    n = 0
    for i, p in enumerate(P):
        A = [np.concatenate([-(p - q), [1.0]]) for j, q in enumerate(P) if j != i]
        c = np.zeros(k + 1)
        c[-1] = -1.0
        res = linprog(c, A_ub=np.array(A), b_ub=np.zeros(len(A)),
                      bounds=[(-1, 1)] * k + [(None, None)], method="highs")
        if res.status == 0 and -res.fun > 1e-9:
            n += 1
    return n


def vertices(F, k):
    return hull_vertex_count(vertex_points(F, k))


LAYOUTS = {
    "E0": ([(64, 64), (65, 64), (64, 65), (65, 65)], rect(64, 64, 65, 65), None),
    "E1": ([(64, 64), (69, 64), (74, 64)], rect(62, 62, 76, 66), None),
    "E2": ([(64, 64), (65, 64), (64, 65), (65, 65)], rect(62, 62, 67, 67), 0),
    "E3": ([(64, 64), (67, 64), (64, 67)],
           {c for c in rect(62, 62, 69, 69) if min(cheb(c, t) for t in [(64, 64), (67, 64), (64, 67)]) <= 2},
           None),
    "E4": ([(64, 64), (69, 64), (74, 64), (79, 64)], rect(62, 62, 81, 66), None),
}


def square_sweep():
    out = {}
    for s in range(1, 8):
        tickets = [(64, 64), (64 + s, 64), (64, 64 + s), (64 + s, 64 + s)]
        box = rect(62, 62, 66 + s, 66 + s)
        window = {c for c in box if min(cheb(c, t) for t in tickets) <= 2}
        out[f"S{s}"] = (tickets, window, None)
    return out


def record(name, tickets, window, R, variant, first=None):
    k = len(tickets)
    F = family(tickets, window, R) if variant == "F" else family_prime(tickets, window, R)
    groups = classes_by_min(tickets, F)
    orders = math.factorial(k)
    pts = vertex_points(F, k)
    hull = hull_vertex_count(pts)
    lp = lp_vertex_count(pts)
    n_classes = len(groups)
    rec = {
        "layout": name,
        "R": R,
        "variant": variant,
        "tickets": [list(t) for t in tickets],
        "window_size": len(window),
        "family": sorted(sorted(S) for S in F),
        "classes": n_classes,
        "distinct_points": len(pts),
        "hull_vertices": hull,
        "lp_vertices": lp,
        "bits_lost": round(math.log2(orders / n_classes), 4) if n_classes else None,
        "classes_eq_hull": n_classes == hull,
        "points_eq_hull": len(pts) == hull,
        "hull_eq_lp": hull == lp,
        "when": datetime.now().isoformat(timespec="seconds"),
        "class_orders": [g for g in groups.values()],
    }
    if first is not None:
        hit = sorted({i for i, g in enumerate(groups.values()) for o in g if o[0] == first})
        sub_orders = [o for g in groups.values() for o in g if o[0] == first]
        rec["first_ticket_subset"] = {
            "first": first,
            "orders": len(sub_orders),
            "classes_hit": len(hit),
            "bits_lost": round(math.log2(len(sub_orders) / len(hit)), 4),
        }
    return rec


def check_predictions(pred, results):
    rows = []
    for r in results:
        if r["layout"] == "E0":
            exp = pred["E0_square"]["F" if r["variant"] == "F" else "F_prime"]
        elif r["layout"] == "E1":
            exp = pred["E1_line"][f"R{r['R']}"]["F" if r["variant"] == "F" else "F_prime"]
        else:
            continue
        held = (exp["classes"] == r["classes"] and exp["vertices"] == r["hull_vertices"]
                and abs(exp["bits_lost"] - r["bits_lost"]) < 0.001)
        rows.append({"layout": r["layout"], "R": r["R"], "variant": r["variant"],
                     "predicted": [exp["classes"], exp["vertices"], exp["bits_lost"]],
                     "computed": [r["classes"], r["hull_vertices"], r["bits_lost"]], "held": held})
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "results", "research", "quotient_polytope.json")
    with open(path) as f:
        doc = json.load(f)
    results = []
    for name, (tickets, window, first) in LAYOUTS.items():
        for R in (2, 3, 4):
            for variant in ("F", "F_prime"):
                results.append(record(name, tickets, window, R, variant, first))
    for name, (tickets, window, first) in square_sweep().items():
        for R in (2, 3, 4):
            results.append(record(name, tickets, window, R, "F"))
            results.append(record(name, tickets, window, R, "F_prime"))
    mismatches = [r for r in results if not (r["classes_eq_hull"] and r["points_eq_hull"] and r["hull_eq_lp"])]
    doc["status"] = "results computed; see results"
    doc["vertex_method"] = ("hull_vertices: scipy.spatial.ConvexHull on the affine-reduced distinct "
                            "count-vectors v(sigma) (SVD to affine dimension); lp_vertices: scipy linprog "
                            "(highs) per point, vertex iff the max separating margin is > 0")
    doc["results"] = results
    doc["predictions_check"] = check_predictions(doc["predictions"], results)
    doc["mismatches"] = [{"layout": r["layout"], "R": r["R"], "variant": r["variant"],
                          "classes": r["classes"], "distinct_points": r["distinct_points"],
                          "hull_vertices": r["hull_vertices"], "lp_vertices": r["lp_vertices"]}
                         for r in mismatches]
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    for r in results:
        print(r["layout"], r["R"], r["variant"], r["classes"], r["hull_vertices"], r["bits_lost"],
              r["distinct_points"], r["lp_vertices"], r.get("first_ticket_subset", ""))


if __name__ == "__main__":
    main()
