"""Traversal-cost sublevel filtration of the seed-7 spawn grid, plain Python.

Tile cost: air 0, water s, stone d; tree and iron are never walkable.
Walkable at threshold T: cost <= T. Complex: pixel centres as vertices,
4-neighbour edges, full 2x2 blocks as faces (cubical complex).
Writes lab/results/research/terrain_persistence.json and terrain_sweep.json,
and the masks / point clouds consumed by the mlm tools.
"""
import json
import struct
from collections import deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "lab" / "results" / "research"
GRID = RES / "seed7_spawn.grid"
AIR, STONE, WATER, TREE, IRON, GOAL = range(6)
NAMES = {AIR: "air", STONE: "stone", WATER: "water", TREE: "tree", IRON: "iron", GOAL: "goal"}
START = (32, 32)
T_MAX = 30
INF = float("inf")


class Grid:
    def __init__(self, path):
        b = path.read_bytes()
        self.w, self.h = struct.unpack("<II", b[:8])
        self.cells = list(b[8:])
        assert len(self.cells) == self.w * self.h
        self.n = self.w * self.h
        self.nb4 = [[] for _ in range(self.n)]
        self.nb8 = [[] for _ in range(self.n)]
        for y in range(self.h):
            for x in range(self.w):
                i = y * self.w + x
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == dy == 0:
                            continue
                        X, Y = x + dx, y + dy
                        if 0 <= X < self.w and 0 <= Y < self.h:
                            self.nb8[i].append(Y * self.w + X)
                            if dx == 0 or dy == 0:
                                self.nb4[i].append(Y * self.w + X)
        self.start = START[1] * self.w + START[0]

    def costs(self, s, d):
        table = {AIR: 0, WATER: s, STONE: d}
        return [table.get(t, INF) for t in self.cells]

    def mask(self, costs, T):
        return [c <= T for c in costs]


def components(G, mask):
    lab = [-1] * G.n
    sizes = []
    for s0 in range(G.n):
        if mask[s0] and lab[s0] < 0:
            k = len(sizes)
            lab[s0] = k
            q = deque([s0])
            sz = 0
            while q:
                i = q.popleft()
                sz += 1
                for j in G.nb4[i]:
                    if mask[j] and lab[j] < 0:
                        lab[j] = k
                        q.append(j)
            sizes.append(sz)
    return lab, sizes


def vef(G, mask):
    V = E = F = 0
    w, h = G.w, G.h
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if not mask[i]:
                continue
            V += 1
            if x + 1 < w and mask[i + 1]:
                E += 1
            if y + 1 < h and mask[i + w]:
                E += 1
            if x + 1 < w and y + 1 < h and mask[i + 1] and mask[i + w] and mask[i + w + 1]:
                F += 1
    return V, E, F


def bounded_holes(G, mask):
    """Bounded 8-connected components of the complement: the independent H1 count."""
    seen = [False] * G.n
    q = deque()
    for i in range(G.n):
        x, y = i % G.w, i // G.w
        if not mask[i] and (x in (0, G.w - 1) or y in (0, G.h - 1)):
            seen[i] = True
            q.append(i)
    while q:
        i = q.popleft()
        for j in G.nb8[i]:
            if not mask[j] and not seen[j]:
                seen[j] = True
                q.append(j)
    holes = 0
    for i0 in range(G.n):
        if not mask[i0] and not seen[i0]:
            holes += 1
            seen[i0] = True
            q = deque([i0])
            while q:
                i = q.popleft()
                for j in G.nb8[i]:
                    if not mask[j] and not seen[j]:
                        seen[j] = True
                        q.append(j)
    return holes


def h0_barcode(G, costs):
    order = sorted((c, i) for i, c in enumerate(costs) if c != INF)
    pos = {i: k for k, (_, i) in enumerate(order)}
    parent = list(range(G.n))
    birth = [0] * G.n
    active = [False] * G.n

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    pairs = []
    for c, i in order:
        active[i] = True
        birth[i] = c
        for j in G.nb4[i]:
            if not active[j]:
                continue
            ri, rj = find(i), find(j)
            if ri == rj:
                continue
            # elder rule: older component (smaller birth, then earlier position) survives
            if (birth[ri], pos[ri]) < (birth[rj], pos[rj]):
                keep, kill = ri, rj
            else:
                keep, kill = rj, ri
            pairs.append((birth[kill], c))
            parent[kill] = keep
    essential = sorted(birth[i] for i in range(G.n) if active[i] and find(i) == i)
    return pairs, essential


def start_component(G, mask):
    lab, _ = components(G, mask)
    k = lab[G.start]
    return {i for i, l in enumerate(lab) if l == k and k >= 0}


def touches(G, comp):
    """Tree/iron/stone tiles 4-adjacent to the start component, and stone tiles inside it.

    *_adj counts distinct tiles; *_edges counts boundary pairs (component cell, tile)."""
    adj = {TREE: set(), IRON: set(), STONE: set(), WATER: set()}
    edges = {TREE: 0, IRON: 0, STONE: 0, WATER: 0}
    for i in comp:
        for j in G.nb4[i]:
            if j not in comp and G.cells[j] in adj:
                adj[G.cells[j]].add(j)
                edges[G.cells[j]] += 1
    stone_in = sum(1 for i in comp if G.cells[i] == STONE)
    return {
        "tree_adj": len(adj[TREE]),
        "iron_adj": len(adj[IRON]),
        "stone_adj": len(adj[STONE]),
        "stone_in_start": stone_in,
        "tree_edges": edges[TREE],
        "iron_edges": edges[IRON],
        "stone_edges": edges[STONE],
        "water_edges": edges[WATER],
        "water_adj": len(adj[WATER]),
    }


def table_for(G, s, d):
    costs = G.costs(s, d)
    rows = []
    for T in range(T_MAX + 1):
        mask = G.mask(costs, T)
        _, sizes = components(G, mask)
        V, E, F = vef(G, mask)
        b0 = len(sizes)
        chi = V - E + F
        b1 = bounded_holes(G, mask)
        comp = start_component(G, mask)
        row = {"T": T, "b0": b0, "b1": b1, "chi_VEF": chi, "V": V, "E": E, "F": F,
               "euler_ok": chi == b0 - b1, "start_size": len(comp)}
        row.update(touches(G, comp))
        rows.append(row)
    return rows


def first_T(rows, key):
    for r in rows:
        if r[key] > 0:
            return r["T"]
    return None


def sweep(G):
    keys = ("tree_touch", "iron_touch", "stone_touch", "stone_enter", "b0_at_max")
    res = {k: [[None] * (T_MAX + 1) for _ in range(T_MAX + 1)] for k in keys}
    for s in range(T_MAX + 1):
        for d in range(T_MAX + 1):
            costs = G.costs(s, d)
            cands = sorted({0, s, d})
            hit = {k: None for k in keys[:4]}
            for T in cands:
                t = touches(G, start_component(G, G.mask(costs, T)))
                checks = (("tree_touch", t["tree_adj"]), ("iron_touch", t["iron_adj"]),
                          ("stone_touch", t["stone_adj"]), ("stone_enter", t["stone_in_start"]))
                for key, cnt in checks:
                    if cnt > 0 and hit[key] is None:
                        hit[key] = T
            for key in keys[:4]:
                res[key][s][d] = hit[key]
            _, sizes = components(G, G.mask(costs, max(cands)))
            res["b0_at_max"][s][d] = len(sizes)
    return res


def system_report(G, s, d):
    costs = G.costs(s, d)
    rows = table_for(G, s, d)
    pairs, essential = h0_barcode(G, costs)
    finite_pos = sorted(p for p in pairs if p[1] > p[0])
    return {
        "s": s, "d": d,
        "table": rows,
        "islands_T0": rows[0]["b0"],
        "start_island_T0": rows[0]["start_size"],
        "barcode_H0": {
            "finite_positive": [list(p) for p in finite_pos],
            "zero_persistence_pairs": len(pairs) - len(finite_pos),
            "essential_births": essential,
        },
        "bottleneck_T": {
            "tree_touch": first_T(rows, "tree_adj"),
            "iron_touch": first_T(rows, "iron_adj"),
            "stone_touch": first_T(rows, "stone_adj"),
            "stone_enter": first_T(rows, "stone_in_start"),
        },
        "euler_all_T_ok": all(r["euler_ok"] for r in rows),
    }


def write_mlm_inputs(G):
    masks = {"air_T0": G.mask(G.costs(10, 23), 0),
             "air_water_T10": G.mask(G.costs(10, 23), 10),
             "air_water_stone_T23": G.mask(G.costs(10, 23), 23)}
    mdir = RES / "mlm_inputs"
    mdir.mkdir(exist_ok=True)
    out = {}
    for k, m in masks.items():
        arr = np.array(m, dtype=bool).reshape(G.h, G.w)
        np.save(mdir / f"mask_{k}.npy", arr)
        xs = [i % G.w for i in range(G.n) if m[i]]
        ys = [i // G.w for i in range(G.n) if m[i]]
        np.save(mdir / f"points_{k}.npy", np.array([xs, ys], dtype=float).T)
        out[k] = {"mask": f"lab/results/research/mlm_inputs/mask_{k}.npy",
                  "points": f"lab/results/research/mlm_inputs/points_{k}.npy",
                  "n_walkable": int(arr.sum())}
    return out


def mlm_per_T(raw, key):
    """Map each T to the mlm result of its walkable set (T_to_mask in the raw file)."""
    spans = raw["T_to_mask"][key]
    out = {}
    for span, mk in spans.items():
        lo, hi = (int(v) for v in span.split("-"))
        for T in range(lo, hi + 1):
            e = raw["euler_characteristic"][mk]
            p = raw["ph_summary_thresh1_max_dim0"][mk]
            out[T] = {"mask": mk, "mlm_b0": e["b0"], "mlm_b1": e["b1"], "mlm_chi": e["chi"],
                      "mlm_ph_b0_thresh1": p["dim0_n_essential"]}
    return out


def attach_mlm(out, systems):
    raw = json.loads((RES / "terrain_mlm_raw.json").read_text())
    cross = {}
    for key, rep in systems.items():
        per = mlm_per_T(raw, key)
        rows = []
        for r in rep["table"]:
            m = per[r["T"]]
            rows.append({"T": r["T"], "plain_b0": r["b0"], "plain_b1": r["b1"], "mask": m["mask"],
                         "mlm_b0": m["mlm_b0"], "mlm_b1": m["mlm_b1"], "mlm_ph_b0_thresh1": m["mlm_ph_b0_thresh1"],
                         "b0_agree": r["b0"] == m["mlm_b0"] == m["mlm_ph_b0_thresh1"],
                         "b1_agree": r["b1"] == m["mlm_b1"]})
        cross[key] = {"rows": rows,
                      "all_T_b0_agree": all(x["b0_agree"] for x in rows),
                      "all_T_b1_agree": all(x["b1_agree"] for x in rows)}
    out["mlm_cross_check"] = {"raw": "lab/results/research/terrain_mlm_raw.json", "systems": cross}


def main():
    G = Grid(GRID)
    systems = {
        "a_swim10_dig23": system_report(G, 10, 23),
        "b_equal_cost23": system_report(G, 23, 23),
    }
    out = {
        "method": "plain_python_union_find",
        "grid": "lab/results/research/seed7_spawn.grid",
        "size": [G.w, G.h],
        "tile_counts": {NAMES[t]: G.cells.count(t) for t in NAMES},
        "start": list(START),
        "start_tile": NAMES[G.cells[G.start]],
        "convention": "vertices = walkable tile centres, 4-neighbour edges, 2x2 faces; "
                      "walkable iff cost<=T; tree/iron never walkable; touch = 4-adjacent to start component",
        "T_grid": list(range(T_MAX + 1)),
        "systems": systems,
        "mlm_inputs": write_mlm_inputs(G),
    }
    attach_mlm(out, systems)
    out["mlm_status"] = ("mlm MCP unavailable after 13:57 (failed to reconnect after the 13:53 freeze and reboot). "
                         "mlm_cross_check rows were produced by mlm calls made before that time and are "
                         "transcribed in lab/results/research/terrain_mlm_raw.json; they are not re-run.")
    (RES / "terrain_persistence.json").write_text(json.dumps(out, indent=1))
    (RES / "terrain_sweep.json").write_text(json.dumps(
        {"method": "plain_python_union_find", "axes": "matrices[s][d], s and d in 0..30",
         "matrices": sweep(G)}))
    for k, v in systems.items():
        print(k, "islands_T0", v["islands_T0"], "start", v["start_island_T0"],
              "bottleneck", v["bottleneck_T"], "euler_ok", v["euler_all_T_ok"])


if __name__ == "__main__":
    main()
