"""Topology of the map from build orders to saved worlds, as partitions of S_k.

Vertices are orders (tuples of ticket indices). Edges join orders differing by one adjacent
transposition (positions p, p+1). 2-cells: squares from commuting swaps (p, q), |p-q| >= 2,
and hexagons from braid moves (p, p+1) on three consecutive positions.

Per class C: b0, b1, b2 of the induced subcomplex, computed twice (gudhi SimplexTree on a
triangulation with no new vertices, and cellular ranks with Euler arithmetic), plus convexity
by BFS in the full permutohedron graph and the boundary swaps.
"""
import argparse
import itertools
import json
import subprocess
import sys
from collections import deque
from fractions import Fraction
from pathlib import Path

import gudhi

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "lab" / "results" / "research" / "fibers.json"


def swap(order, p):
    o = list(order)
    o[p], o[p + 1] = o[p + 1], o[p]
    return tuple(o)


class Permutohedron:
    def __init__(self, k):
        if not 1 <= k <= 6:
            raise ValueError("k must be between 1 and 6")
        self.k = k
        self.verts = list(itertools.permutations(range(k)))
        self.idx = {v: i for i, v in enumerate(self.verts)}
        n = len(self.verts)
        self.adj = [[] for _ in range(n)]
        self.edges = {}
        for a, v in enumerate(self.verts):
            for p in range(k - 1):
                b = self.idx[swap(v, p)]
                self.adj[a].append(b)
                if a < b:
                    self.edges[(a, b)] = p
        self.squares = []
        seen = set()
        for i in range(k - 1):
            for j in range(i + 2, k - 1):
                for a, v in enumerate(self.verts):
                    ai = self.idx[swap(v, i)]
                    aj = self.idx[swap(v, j)]
                    aij = self.idx[swap(swap(v, i), j)]
                    cyc = [a, ai, aij, aj]
                    key = frozenset(cyc)
                    if key not in seen:
                        seen.add(key)
                        self.squares.append(cyc)
        self.hexagons = []
        seen = set()
        for i in range(k - 2):
            for a in range(n):
                seq = [a]
                cur = a
                for step in range(6):
                    cur = self.idx[swap(self.verts[cur], i + 1 if step % 2 == 0 else i)]
                    seq.append(cur)
                if seq[6] != a or len(set(seq[:6])) != 6:
                    raise AssertionError("braid hexagon did not close")
                key = frozenset(seq[:6])
                if key not in seen:
                    seen.add(key)
                    self.hexagons.append(seq[:6])
        self.cells = self.squares + self.hexagons
        self.dist = []
        for s in range(n):
            d = [-1] * n
            d[s] = 0
            q = deque([s])
            while q:
                x = q.popleft()
                for y in self.adj[x]:
                    if d[y] < 0:
                        d[y] = d[x] + 1
                        q.append(y)
            self.dist.append(d)


def triangulation(cyc):
    if len(cyc) == 4:
        v0, v1, v2, v3 = cyc
        return [(v0, v2)], [(v0, v1, v2), (v0, v2, v3)]
    h0, h1, h2, h3, h4, h5 = cyc
    return [(h0, h2), (h0, h3), (h0, h4)], [(h0, h1, h2), (h0, h2, h3), (h0, h3, h4), (h0, h4, h5)]


def _rank(nrows, ncols, entries):
    M = [[Fraction(0)] * ncols for _ in range(nrows)]
    for (r, c), x in entries.items():
        M[r][c] += x
    rank = 0
    for c in range(ncols):
        piv = next((r for r in range(rank, nrows) if M[r][c] != 0), None)
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        pv = M[rank][c]
        for r in range(nrows):
            if r != rank and M[r][c] != 0:
                f = M[r][c] / pv
                M[r] = [x - f * y for x, y in zip(M[r], M[rank])]
        rank += 1
    return rank


def cellular_betti(P, C):
    inC = set(C)
    V = sorted(inC)
    E = [e for e in P.edges if e[0] in inC and e[1] in inC]
    eidx = {e: i for i, e in enumerate(E)}
    F = [cyc for cyc in P.cells if all(v in inC for v in cyc)]
    d1 = {}
    for j, (a, b) in enumerate(E):
        d1[(a, j)] = Fraction(-1)
        d1[(b, j)] = Fraction(1)
    vidx = {v: i for i, v in enumerate(V)}
    d1 = {(vidx[r], c): x for (r, c), x in d1.items()}
    r1 = _rank(len(V), len(E), d1)
    d2 = {}
    for j, cyc in enumerate(F):
        m = len(cyc)
        for t in range(m):
            x, y = cyc[t], cyc[(t + 1) % m]
            e = (min(x, y), max(x, y))
            sign = 1 if x < y else -1
            key = (eidx[e], j)
            d2[key] = d2.get(key, 0) + sign
    r2 = _rank(len(E), len(F), d2)
    parent = {v: v for v in V}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for a, b in E:
        parent[find(a)] = find(b)
    b0_uf = len({find(v) for v in V})
    b0 = len(V) - r1
    b1 = (len(E) - r1) - r2
    b2 = len(F) - r2
    chi = len(V) - len(E) + len(F)
    return {"b0": b0, "b1": b1, "b2": b2, "b0_uf": b0_uf, "chi": chi, "b1_euler": b0 + b2 - chi,
            "V": len(V), "E": len(E), "F": len(F)}


def gudhi_betti(P, C):
    inC = set(C)
    V = sorted(inC)
    loc = {v: i for i, v in enumerate(V)}
    st = gudhi.SimplexTree()
    for v in V:
        st.insert([loc[v]])
    for a, b in P.edges:
        if a in inC and b in inC:
            st.insert([loc[a], loc[b]])
    for cyc in P.cells:
        if all(v in inC for v in cyc):
            chords, tris = triangulation(cyc)
            for x, y in chords:
                st.insert([loc[x], loc[y]])
            for t in tris:
                st.insert([loc[x] for x in t])
    st.compute_persistence(homology_coeff_field=2, persistence_dim_max=True)
    b = list(st.betti_numbers()) + [0, 0, 0]
    return b[0], b[1], b[2]


def is_convex(P, C):
    inC = set(C)
    n = len(P.verts)
    for u in C:
        for v in C:
            if v <= u:
                continue
            duv = P.dist[u][v]
            for w in range(n):
                if w not in inC and P.dist[u][w] + P.dist[w][v] == duv:
                    return False, (P.verts[u], P.verts[v], P.verts[w])
    return True, None


def analyse_class(P, orders, listed=None, classes_of=None):
    C = [P.idx[tuple(o)] for o in orders]
    if len(set(C)) != len(C):
        raise ValueError("duplicate order in class")
    inC = set(C)
    cb = cellular_betti(P, C)
    gb = gudhi_betti(P, C)
    convex, witness = is_convex(P, C)
    boundary_edges = 0
    to_listed_other = 0
    to_unlisted = 0
    swaps = set()
    for a in C:
        for b in P.adj[a]:
            if b in inC:
                continue
            boundary_edges += 1
            swaps.add(P.edges[(min(a, b), max(a, b))])
            if listed is not None and b in listed:
                to_listed_other += 1
            elif listed is not None:
                to_unlisted += 1
    out = {
        "size": len(C),
        "b0": cb["b0"], "b1": cb["b1"], "b2": cb["b2"],
        "b0_uf": cb["b0_uf"], "chi": cb["chi"], "b1_euler": cb["b1_euler"],
        "V": cb["V"], "E": cb["E"], "F": cb["F"],
        "b0_gudhi": gb[0], "b1_gudhi": gb[1], "b2_gudhi": gb[2],
        "agree": gb == (cb["b0"], cb["b1"], cb["b2"]) and cb["b0_uf"] == cb["b0"]
        and cb["b1_euler"] == cb["b1"],
        "convex": convex,
        "witness": None if witness is None else [list(x) for x in witness],
        "boundary_edges": boundary_edges,
        "boundary_swaps": sorted(swaps),
        "boundary_swap_labels": [f"({p},{p + 1})" for p in sorted(swaps)],
    }
    if listed is not None:
        out["cross_listed_edges"] = to_listed_other
        out["to_unlisted_edges"] = to_unlisted
    return out


def analyse_partition(P, classes):
    seen = {}
    for ci, cls in enumerate(classes):
        for o in cls:
            o = tuple(o)
            if o in seen:
                raise ValueError(f"order {o} in classes {seen[o]} and {ci}")
            seen[o] = ci
    listed = {P.idx[o] for o in seen}
    label = {P.idx[o]: ci for o, ci in seen.items()}
    res = []
    for ci, cls in enumerate(classes):
        r = analyse_class(P, cls, listed=listed)
        r["index"] = ci
        r["orders"] = [list(tuple(o)) for o in cls]
        res.append(r)
    cross = 0
    unlisted = 0
    for (a, b) in P.edges:
        if a in listed and b in listed:
            if label[a] != label[b]:
                cross += 1
        elif a in listed or b in listed:
            unlisted += 1
    return {"classes": res, "domain_size": len(listed), "domain_complete": len(listed) == len(P.verts),
            "cross_class_edges": cross, "listed_to_unlisted_edges": unlisted}


def load_partition(rec):
    tickets = rec["tickets"]
    k = rec.get("k", len(tickets))
    if len(tickets) != k:
        raise ValueError("tickets length differs from k")
    classes = []
    for cls in rec["classes"]:
        classes.append([tuple(tickets.index(t) for t in order) for order in cls])
    return k, classes


def git_show(ref, path):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{path}"], check=True,
                          capture_output=True, text=True).stdout


def git_rev(ref):
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", ref], check=True,
                          capture_output=True, text=True).stdout.strip()


def git_file_commit(ref, path):
    return subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%H", ref, "--", path],
                          check=True, capture_output=True, text=True).stdout.strip()


def run_source(ref, path):
    data = json.loads(git_show(ref, path))
    records = data["records"] if "records" in data else [data]
    commit = git_rev(ref)
    file_commit = git_file_commit(ref, path)
    runs = []
    for rec in records:
        if "classes" not in rec or "tickets" not in rec:
            continue
        k, classes = load_partition(rec)
        P = Permutohedron(k)
        res = analyse_partition(P, classes)
        run = {
            "source": {"ref": ref, "path": path, "commit": commit, "file_last_commit": file_commit},
            "layout": rec.get("layout"),
            "r_dec": rec.get("r_dec"),
            "k": k,
            "tickets": rec["tickets"],
            "predicted_classes": rec.get("predicted_classes"),
            "found_classes": len(classes),
        }
        run.update(res)
        runs.append(run)
    return runs


def append_runs(runs, out=OUT):
    if out.exists():
        doc = json.loads(out.read_text())
    else:
        doc = {"lane": "fibers", "round": 3, "run": "n3", "version": 1, "runs": []}
    new_keys = {(n["source"]["path"], n["source"]["commit"], n["layout"], n["r_dec"]) for n in runs}
    keep = [r for r in doc["runs"]
            if (r["source"]["path"], r["source"]["commit"], r["layout"], r["r_dec"]) not in new_keys]
    doc["runs"] = keep + runs
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n")
    return len(doc["runs"])


def summary_lines(run):
    lines = [f"layout {run['layout']} r_dec {run['r_dec']} k {run['k']} "
             f"domain {run['domain_size']}/{len(Permutohedron(run['k']).verts)} "
             f"cross_edges {run['cross_class_edges']} to_unlisted {run['listed_to_unlisted_edges']}"]
    lines.append("  cls size b0 b1 b2 agree convex boundary_edges swaps")
    for c in run["classes"]:
        lines.append(f"  {c['index']:>3} {c['size']:>4} {c['b0']:>2} {c['b1']:>2} {c['b2']:>2} "
                     f"{str(c['agree']):>5} {str(c['convex']):>6} {c['boundary_edges']:>14} "
                     f"{c['boundary_swap_labels']}")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    runs = run_source(args.ref, args.path)
    for run in runs:
        print("\n".join(summary_lines(run)))
    n = append_runs(runs, Path(args.out))
    print(f"appended {len(runs)} runs from {args.ref}:{args.path}; file now has {n} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
