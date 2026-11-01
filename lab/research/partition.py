import argparse
import hashlib
import itertools
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "research" / "partitions.json"
ORES = ("diamond", "iron", "coal", "gold", "lapis", "redstone", "emerald")
ORE_KEYS = ORES + ("total",)
RESAMPLES = 10000
SEED = 20261101
POLY_R = 3
CAMERON_SQUARE = {1: 4, 2: 4, 3: 20, 4: 20, 5: 1, 6: 1, 7: 1}
CAMERON_LINE4 = {2: 12, 3: 8, 4: 4}
NOISE_RULE = ("a chunk is noisy when any same-order repeat pair differs in its hash; noisy chunks are "
              "removed before the classes, per-chunk partitions and ore comparison; diff counts come "
              "from the campaign diff report when given")


def okey(order):
    return ";".join(f"{int(x)},{int(z)}" for x, z in order)


def sha_of(chunk):
    return chunk["sha"] if "sha" in chunk else chunk["sha256"]


def signature(world):
    return tuple(sorted((k, sha_of(c)) for k, c in world["chunks"].items()))


def tickets_of(worlds):
    return sorted({tuple(t) for w in worlds for t in w["order"]})


def shape(tickets):
    pts = {tuple(t) for t in tickets}
    xs, zs = sorted({x for x, _ in pts}), sorted({z for _, z in pts})
    if len(pts) == 4 and len(xs) == 2 and len(zs) == 2:
        s = xs[1] - xs[0]
        if zs[1] - zs[0] == s and pts == {(x, z) for x in xs for z in zs}:
            return ("square", s)
    if len(pts) == 4 and len(xs) == 1:
        axis = zs
    elif len(pts) == 4 and len(zs) == 1:
        axis = xs
    else:
        return None
    gaps = {b - a for a, b in zip(axis, axis[1:])}
    return ("line4", gaps.pop()) if len(gaps) == 1 else None


def partition(worlds):
    sigs_of = {}
    for w in worlds:
        sigs_of.setdefault(okey(w["order"]), set()).add(signature(w))
    by_sig = {}
    for o, sigs in sigs_of.items():
        for s in sigs:
            by_sig.setdefault(s, []).append(o)
    classes = [{"members": sorted(m), "n_orders": len(m)} for s, m in by_sig.items()]
    conflicted = sorted(o for o, s in sigs_of.items() if len(s) > 1)
    n_orders, n_classes = len(sigs_of), len(by_sig)
    valid = not conflicted
    bits = math.log2(n_orders / n_classes) if valid and n_orders and n_classes else None
    return {"n_worlds": len(worlds), "n_orders": n_orders, "n_classes": n_classes,
            "bits_lost": bits, "valid_partition": valid, "conflicted_orders": len(conflicted),
            "conflicted": conflicted, "classes": classes}


def per_chunk(worlds):
    out = {}
    for k in sorted({k for w in worlds for k in w["chunks"]}):
        groups, shas_of = {}, {}
        for w in worlds:
            if k in w["chunks"]:
                o, sha = okey(w["order"]), sha_of(w["chunks"][k])
                groups.setdefault(sha, set()).add(o)
                shas_of.setdefault(o, set()).add(sha)
        out[k] = {"n_classes": len(groups), "classes": [sorted(g) for g in groups.values()],
                  "conflicted_orders": sum(1 for s in shas_of.values() if len(s) > 1)}
    return out


def refinement_violations(whole, per):
    v = 0
    for info in per.values():
        where = {o: i for i, cl in enumerate(info["classes"]) for o in cl}
        for cl in whole["classes"]:
            if len({where.get(o) for o in cl["members"]}) > 1:
                v += 1
    return v


def noise_split(worlds, report=None):
    diff = {}
    if report:
        for p in report["pairs"]:
            if p.get("control"):
                diff[frozenset((p["a"], p["b"]))] = p["diff_by_chunk"]
    by_order = {}
    for w in worlds:
        by_order.setdefault(okey(w["order"]), []).append(w)
    chunks = sorted({k for w in worlds for k in w["chunks"]})
    noisy, tested = {}, 0
    for ws in by_order.values():
        for a, b in itertools.combinations(ws, 2):
            tested += 1
            counts = diff.get(frozenset((a.get("label"), b.get("label"))))
            for k in chunks:
                if k not in a["chunks"] or k not in b["chunks"]:
                    continue
                differs = sha_of(a["chunks"][k]) != sha_of(b["chunks"][k])
                count = None if counts is None else counts.get(k, 0)
                if count is not None and differs != (count > 0):
                    raise ValueError(f"hash and raw diff disagree for {a.get('label')} vs {b.get('label')} chunk {k}")
                if differs:
                    noisy.setdefault(k, []).append({"a": a.get("label"), "b": b.get("label"),
                                                    "order": okey(a["order"]), "diff_blocks": count})
    listed = []
    for k in sorted(noisy):
        counts = [x["diff_blocks"] for x in noisy[k]]
        listed.append({"chunk": k, "repeat_pairs": noisy[k],
                       "max_diff_blocks": max(counts) if None not in counts else None})
    return {"rule": NOISE_RULE, "clean_chunks": [k for k in chunks if k not in noisy],
            "noisy_chunks": sorted(noisy), "noisy": listed, "repeat_pairs_tested": tested}


def restrict(worlds, keep):
    keep = set(keep)
    return [dict(w, chunks={k: c for k, c in w["chunks"].items() if k in keep}) for w in worlds]


def transitivity(items, d, class_of=None):
    n = len(d)
    sym = sum(1 for a, b in itertools.combinations(range(n), 2) if d[a][b] != d[b][a])
    diag = sum(1 for a in range(n) if d[a][a] != 0)
    trip = list(itertools.permutations(range(n), 3))
    viol = sum(1 for a, b, c in trip if d[a][b] == 0 and d[b][c] == 0 and d[a][c] != 0)
    out = {"items": len(items), "distinct_ordered_triples": len(trip), "violating_triples": viol,
           "symmetry_violations": sym, "diagonal_violations": diag}
    if class_of is not None:
        out["zero_vs_class_disagreements"] = sum(
            1 for a, b in itertools.combinations(range(n), 2)
            if (d[a][b] == 0) != (class_of[a] == class_of[b]))
    return out


def diff_matrix(report, labels):
    idx = {lb: i for i, lb in enumerate(labels)}
    d = [[0] * len(labels) for _ in labels]
    for p in report["pairs"]:
        a, b = idx[p["a"]], idx[p["b"]]
        d[a][b] = d[b][a] = p["diff_total"]
    return d


def verdict(source, measured, expected_orders, predicted, predicted_partition=None, basis="", excluded=False):
    base = {"source": source, "basis": basis, "n_orders": measured["n_orders"],
            "expected_orders": expected_orders, "predicted_classes": predicted,
            "measured_classes": measured["n_classes"]}
    if excluded or measured["n_orders"] != expected_orders:
        cause = "noisy_chunks_excluded" if excluded else "partial_coverage"
        if measured["n_classes"] > predicted:
            return base | {"status": "refuted_lower_bound", "cause": cause, "match": False,
                           "partition_match": None}
        return base | {"status": cause, "match": None, "partition_match": None}
    res = base | {"status": "compared", "match": predicted == measured["n_classes"],
                  "partition_match": None}
    if predicted_partition is not None:
        meas = {frozenset(c["members"]) for c in measured["classes"]}
        pred = {frozenset(okey(o) for o in cl) for cl in predicted_partition}
        res["partition_match"] = meas == pred
    return res


def sim_record(doc, pts, r_dec, n_window=None):
    for rec in doc["records"]:
        if rec["r_dec"] == r_dec and sorted(map(tuple, rec["tickets"])) == pts                 and (n_window is None or rec["window_chunks"] == n_window):
            return rec
    return None


def polytope_entry(doc, pts, R, n_window=None):
    for e in doc["results"]:
        if e["variant"] == "F" and e["R"] == R and sorted(map(tuple, e["tickets"])) == pts                 and (n_window is None or e["window_size"] == n_window):
            return e
    return None


def polytope_partition(e):
    t = [list(x) for x in e["tickets"]]
    return [[[t[i] for i in perm] for perm in cls] for cls in e["class_orders"]]


def predictions(measured, tickets, r_dec, sim_path, poly_path, poly_r=POLY_R, excluded=False, n_window=None):
    pts = sorted({tuple(t) for t in tickets})
    out = []
    if r_dec is None:
        out.append({"source": "sim", "status": "r_dec_required", "match": None})
    elif not sim_path or not Path(sim_path).exists():
        out.append({"source": "sim", "status": "file_missing", "match": None})
    else:
        rec = sim_record(json.loads(Path(sim_path).read_text(encoding="utf-8")), pts, r_dec, n_window)
        if rec is None:
            out.append({"source": "sim", "status": "no_entry", "match": None})
        else:
            out.append(verdict("sim", measured, rec["orders_considered"], rec["predicted_classes"],
                               rec["classes"], basis=f"{rec['layout']} r_dec={r_dec}", excluded=excluded))
    if poly_path and Path(poly_path).exists():
        e = polytope_entry(json.loads(Path(poly_path).read_text(encoding="utf-8")), pts, poly_r, n_window)
        if e is None:
            out.append({"source": "polytope", "status": "no_entry", "match": None, "R": poly_r})
        else:
            out.append(verdict("polytope", measured, sum(len(c) for c in e["class_orders"]), e["classes"],
                               polytope_partition(e), basis=f"stamp family F, R={poly_r}", excluded=excluded))
    else:
        out.append({"source": "polytope", "status": "absent", "match": None})
    sh = shape(pts)
    if sh is None:
        out.append({"source": "cameron", "status": "no_entry", "match": None})
        return out
    kind, s = sh
    if kind == "square":
        pred, basis = CAMERON_SQUARE.get(s), f"square spacing {s}; Cameron gives no R"
    elif r_dec is None:
        out.append({"source": "cameron", "status": "r_dec_required", "match": None})
        return out
    else:
        pred, basis = CAMERON_LINE4.get(r_dec), f"line of 4, R={r_dec}; Cameron gives no spacing"
    if pred is None:
        out.append({"source": "cameron", "status": "no_entry", "match": None, "basis": basis})
    else:
        out.append(verdict("cameron", measured, math.factorial(len(pts)), pred, None, basis, excluded=excluded))
    return out


def _proxy(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def from_round2(doc, name):
    if "rows" in doc:
        worlds, excluded = [], 0
        for r in doc["rows"]:
            if not r.get("measured"):
                excluded += 1
                continue
            chunks = {k: {"sha": _proxy(v), "ores": v} for k, v in r["ores"].items()}
            chunks["world"] = {"sha": _proxy(r["differing_blocks"])}
            worlds.append({"order": r["order"], "chunks": chunks})
        return worlds, {"excluded_inferred": excluded,
                        "hash_source": "PROXY: sha256 of per-chunk ore counts plus differing_blocks vs reference; not a block hash"}
    fps = doc["fingerprints"]
    n = len(doc["orders"])
    worlds = [{"order": o, "chunks": {"world": {"sha": fps[i]}}} for i, o in enumerate(doc["orders"])]
    return worlds, {"unmapped_fingerprints": max(0, len(fps) - n),
                    "hash_source": "whole-world fingerprint, positional order mapping (assumed)"}


def load_worlds(paths):
    worlds, metas = [], []
    for p in paths:
        p = Path(p)
        doc = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(doc, list):
            ws, meta = doc, {"hash_source": "per-chunk sha256 as written by ticket_world.py"}
        elif "worlds" in doc:
            ws, meta = doc["worlds"], {"hash_source": "per-chunk sha256 as written by ticket_world.py"}
        elif "order" in doc and "chunks" in doc:
            ws, meta = [doc], {"hash_source": "per-chunk sha256 as written by ticket_world.py"}
        else:
            ws, meta = from_round2(doc, p.name)
        for i, w in enumerate(ws):
            w.setdefault("label", p.stem if len(ws) == 1 else f"{p.stem}#{i}")
            worlds.append(w)
        metas.append({"file": str(p), **meta})
    return worlds, metas


def ore_value(w, key):
    vals = [c["ores"] for c in w["chunks"].values() if "ores" in c]
    if key == "total":
        return sum(sum(v.values()) for v in vals)
    return sum(v.get(key, 0) for v in vals)


def bootstrap_diff(a, b, n=RESAMPLES, seed=SEED):
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        ma = sum(rng.choices(a, k=len(a))) / len(a)
        mb = sum(rng.choices(b, k=len(b))) / len(b)
        diffs.append(ma - mb)
    diffs.sort()
    lo, hi = diffs[int(0.025 * n)], diffs[int(0.975 * n) - 1]
    return {"mean_diff": sum(a) / len(a) - sum(b) / len(b), "ci95": [lo, hi],
            "n_a": len(a), "n_b": len(b), "resamples": n, "seed": seed,
            "excludes_zero": lo > 0 or hi < 0}


def ore_comparison(worlds, whole):
    if not any("ores" in c for w in worlds for c in w["chunks"].values()):
        return {"status": "no_ore_counts"}
    if whole["valid_partition"]:
        grouping = "signature"
        reason = "classes: exact equality of all chunk hashes"
        key_of = signature
    else:
        grouping = "order"
        reason = "partition invalid: an order has two different worlds, so classes are undefined; compared by order"
        key_of = lambda w: okey(w["order"])
    groups = {}
    for w in worlds:
        groups.setdefault(key_of(w), []).append(w)
    rep, insufficient, spread = [], [], 0
    for g in groups.values():
        by_order = {}
        for w in g:
            by_order.setdefault(okey(w["order"]), []).append(w)
        if max(len(v) for v in by_order.values()) < 2:
            insufficient.append({"members": sorted(by_order), "worlds": len(g)})
            continue
        rep.append(g)
        for ws in by_order.values():
            if len(ws) >= 2:
                for key in ORE_KEYS:
                    vals = [ore_value(w, key) for w in ws]
                    spread = max(spread, max(vals) - min(vals))

    def members(g):
        return sorted({okey(w["order"]) for w in g})

    status = "compared" if len(rep) >= 2 else "fewer_than_two_repeat_classes"
    comps = []
    for i, j in itertools.combinations(range(len(rep)), 2):
        for key in ORE_KEYS:
            a = [ore_value(w, key) for w in rep[i]]
            b = [ore_value(w, key) for w in rep[j]]
            comps.append({"ore": key, "classes": [members(rep[i]), members(rep[j])],
                          **bootstrap_diff(a, b)})
    return {"status": status, "grouping": grouping, "grouping_reason": reason,
            "method": "plain-Python percentile bootstrap, random.choices, "
                      f"{RESAMPLES} resamples, seed {SEED}; not mlm runs_compare",
            "keys_tested": len(ORE_KEYS), "comparisons": comps,
            "insufficient_repeats": insufficient, "repeat_spread_max": spread}


def analyse(paths, *, experiment, r_dec, sim, sim_ref, poly, poly_ref, poly_r, diff_path):
    worlds, metas = load_worlds(paths)
    tickets = tickets_of(worlds)
    report = json.loads(Path(diff_path).read_text(encoding="utf-8")) if diff_path else None
    full = partition(worlds)
    noise = noise_split(worlds, report)
    if not noise["clean_chunks"]:
        raise ValueError("every chunk is noisy; nothing left to partition")
    clean = restrict(worlds, noise["clean_chunks"])
    whole = partition(clean)
    per = per_chunk(clean)
    excluded = bool(noise["noisy_chunks"])
    n_window = len({k for w in worlds for k in w["chunks"]} - {"world"})
    if report:
        labels = [w["label"] for w in worlds]
        d = diff_matrix(report, labels)
        index = {}
        class_of = [index.setdefault(signature(w), len(index)) for w in worlds]
        tr = transitivity(labels, d, class_of)
    else:
        tr = {"status": "not_run", "reason": "no pairwise diff report given"}
    pairs = [{"a": p["a"], "b": p["b"], "diff_total": p["diff_total"]} for p in report["pairs"]] if report else []
    n = len(worlds)
    return {"experiment": experiment, "inputs": metas, "n_worlds": n,
            "pairs": pairs, "pairs_complete": bool(report) and len(pairs) == n * (n - 1) // 2,
            "pairs_source": diff_path,
            "tickets": [list(t) for t in tickets], "shape": shape(tickets), "r_dec": r_dec,
            "noise": {k: noise[k] for k in ("rule", "clean_chunks", "noisy_chunks", "noisy", "repeat_pairs_tested")},
            **whole, "per_chunk": per,
            "per_chunk_refinement_violations": refinement_violations(whole, per),
            "all_chunks": {k: full[k] for k in ("n_orders", "n_classes", "valid_partition",
                                                  "conflicted_orders", "conflicted")},
            "transitivity": tr,
            "predictions": predictions(whole, tickets, r_dec, sim, poly, poly_r=poly_r, excluded=excluded,
                                       n_window=n_window),
            "predictions_refs": {"sim": sim_ref, "polytope": poly_ref, "polytope_R": poly_r},
            "ore_comparison": ore_comparison(clean, whole),
            "when": datetime.now(timezone.utc).isoformat()}


def append_result(path, entry):
    path = Path(path)
    doc = json.loads(path.read_text()) if path.exists() else {"runs": []}
    doc["runs"] = [r for r in doc["runs"] if r.get("experiment") != entry.get("experiment")] + [entry]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--r-dec", type=int, default=None)
    ap.add_argument("--sim", default=None, help="quotient_predictions.json from research/sim")
    ap.add_argument("--sim-ref", default=None)
    ap.add_argument("--poly", default=None, help="quotient_polytope.json from research/polytope")
    ap.add_argument("--poly-ref", default=None)
    ap.add_argument("--poly-r", type=int, default=POLY_R)
    ap.add_argument("--diff", default=None, help="campaign quotient.py report with pairs")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    entry = analyse(a.inputs, experiment=a.experiment, r_dec=a.r_dec, sim=a.sim, sim_ref=a.sim_ref,
                    poly=a.poly, poly_ref=a.poly_ref, poly_r=a.poly_r, diff_path=a.diff)
    append_result(a.out, entry)
    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
