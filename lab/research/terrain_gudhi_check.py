"""Independent cross-check of terrain_ph.py with gudhi's CubicalComplex (sublevel filtration).

Obstacles (tree, iron) get value OBST, larger than any T, so they are absent at every
threshold T <= T_MAX. Finite bars with death < OBST_CUT are compared exactly with the plain
barcode; Betti numbers at each integer T are read from the diagram.
Writes lab/results/research/terrain_gudhi_check.json.
"""
import json
import sys
from pathlib import Path

import gudhi
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import terrain_ph as tp  # noqa: E402

OBST = 1000.0
OBST_CUT = 500.0


def cubical_image(G, s, d):
    c = G.costs(s, d)
    img = np.array([OBST if v == float("inf") else float(v) for v in c], dtype=float)
    return img.reshape(G.h, G.w)


def betti_from_diagram(diag, T):
    b = [0, 0]
    for dim, (b_, d_) in diag:
        if dim > 1:
            continue
        if b_ <= T < d_:
            b[dim] += 1
    return b


def run_system(G, name, s, d, plain):
    img = cubical_image(G, s, d)
    cc = gudhi.CubicalComplex(vertices=img)
    diag = cc.persistence(homology_coeff_field=2, min_persistence=0)
    fin = sorted((dim, round(b_, 9), round(d_, 9)) for dim, (b_, d_) in diag
                 if dim <= 1 and b_ < OBST_CUT and d_ < OBST_CUT and d_ > b_)
    plain_pairs = sorted((0, b_, d_) for b_, d_ in plain["barcode_H0"]["finite_positive"])
    h0_fin = [p for p in fin if p[0] == 0]
    rows = []
    for T in range(tp.T_MAX + 1):
        g_b0, g_b1 = betti_from_diagram(diag, T)
        p = plain["table"][T]
        rows.append({"T": T, "gudhi_b0": g_b0, "gudhi_b1": g_b1,
                     "plain_b0": p["b0"], "plain_b1": p["b1"],
                     "agree": g_b0 == p["b0"] and g_b1 == p["b1"]})
    h0_match = sorted((b_, d_) for _, b_, d_ in h0_fin) == sorted((b_, d_) for _, b_, d_ in plain_pairs)
    return {
        "s": s, "d": d,
        "betti_rows": rows,
        "all_T_agree": all(r["agree"] for r in rows),
        "H0_finite_pairs_gudhi": len(h0_fin),
        "H0_finite_pairs_plain": len(plain_pairs),
        "H0_finite_pairs_multiset_equal": h0_match,
        "H1_finite_pairs_gudhi": sum(1 for p in fin if p[0] == 1),
    }


def main():
    G = tp.Grid(tp.GRID)
    pers = json.loads((tp.RES / "terrain_persistence.json").read_text())
    out = {"method": "gudhi.CubicalComplex sublevel, persistence(field 2)",
           "gudhi_version": gudhi.__version__, "OBST": OBST, "OBST_CUT": OBST_CUT, "systems": {}}
    for key, (s, d) in (("a_swim10_dig23", (10, 23)), ("b_equal_cost23", (23, 23))):
        out["systems"][key] = run_system(G, key, s, d, pers["systems"][key])
        r = out["systems"][key]
        print(key, "all_T_agree", r["all_T_agree"], "H0 finite gudhi/plain",
              r["H0_finite_pairs_gudhi"], r["H0_finite_pairs_plain"],
              "multiset_equal", r["H0_finite_pairs_multiset_equal"], "H1 finite gudhi", r["H1_finite_pairs_gudhi"])
    (tp.RES / "terrain_gudhi_check.json").write_text(json.dumps(out, indent=1))
    pers["gudhi_cross_check"] = out
    (tp.RES / "terrain_persistence.json").write_text(json.dumps(pers, indent=1))


if __name__ == "__main__":
    main()
