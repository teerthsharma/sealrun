import hashlib
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results" / "research" / "partitions.json"
PREDICTIONS = HERE.parent / "results" / "research" / "quotient_predictions.json"


def okey(order):
    return ";".join(f"{int(x)},{int(z)}" for x, z in order)


def signature(world):
    return tuple(sorted((k, c["sha"]) for k, c in world["chunks"].items()))


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
                o, sha = okey(w["order"]), w["chunks"][k]["sha"]
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


def transitivity(orders, d, class_of=None):
    n = len(d)
    sym = sum(1 for a, b in itertools.combinations(range(n), 2) if d[a][b] != d[b][a])
    diag = sum(1 for a in range(n) if d[a][a] != 0)
    viol = sum(1 for a, b, c in itertools.product(range(n), repeat=3)
               if d[a][b] == 0 and d[b][c] == 0 and d[a][c] != 0)
    out = {"orders": len(orders), "triples": n ** 3, "violating_triples": viol,
           "symmetry_violations": sym, "diagonal_violations": diag}
    if class_of is not None:
        out["zero_vs_class_disagreements"] = sum(
            1 for a, b in itertools.combinations(range(n), 2)
            if class_of[a] is not None and class_of[b] is not None
            and (d[a][b] == 0) != (class_of[a] == class_of[b]))
    return out


def compare_predictions(layout, n_classes, per, path):
    path = Path(path)
    if not path.exists():
        return {"status": "predictions_missing", "file": str(path), "match": None}
    doc = json.loads(path.read_text())
    table = doc.get("layouts", doc) if isinstance(doc, dict) else {e["layout"]: e for e in doc}
    if layout not in table:
        return {"status": "no_prediction", "layout": layout, "match": None}
    pred = table[layout]
    out = {"status": "compared", "layout": layout, "predicted_classes": pred.get("classes"),
           "measured_classes": n_classes, "match": pred.get("classes") == n_classes}
    if per and "per_chunk" in pred:
        out["per_chunk_match"] = {k: pred["per_chunk"].get(k) == per[k]["n_classes"]
                                  for k in per if k in pred["per_chunk"]}
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
            chunks = {k: {"sha": _proxy(v)} for k, v in r["ores"].items()}
            chunks["world"] = {"sha": _proxy(r["differing_blocks"])}
            worlds.append({"order": r["order"], "chunks": chunks})
        return worlds, {"excluded_inferred": excluded,
                        "hash_source": "PROXY: sha256 of per-chunk ore counts plus differing_blocks vs reference; not a block hash"}
    fps = doc["fingerprints"]
    n = len(doc["orders"])
    worlds = [{"order": o, "chunks": {"world": {"sha": fps[i]}}} for i, o in enumerate(doc["orders"])]
    return worlds, {"unmapped_fingerprints": max(0, len(fps) - n),
                    "hash_source": "whole-world fingerprint, positional order mapping (assumed)",
                    "per_chunk_available": False}


def load_input(path):
    doc = json.loads(Path(path).read_text())
    if isinstance(doc, list):
        return doc, {}, None
    if "worlds" in doc:
        return doc["worlds"], {"layout": doc.get("layout"), "hash_source": doc.get("hash_source")}, doc.get("diff")
    worlds, meta = from_round2(doc, Path(path).name)
    return worlds, dict(meta, layout=Path(path).stem), None


def analyse(worlds, *, experiment, source, meta, diff=None, predictions=None):
    whole = partition(worlds)
    per = per_chunk(worlds)
    if diff:
        cls = {o: j for j, cl in enumerate(whole["classes"]) for o in cl["members"]}
        class_of = [cls.get(okey(o)) for o in diff["orders"]]
        tr = transitivity(diff["orders"], diff["matrix"], class_of)
    else:
        tr = {"status": "not_run", "reason": "no pairwise matrix in input"}
    pred = compare_predictions(meta.get("layout"), whole["n_classes"], per, predictions or PREDICTIONS)
    return {"experiment": experiment, "source": str(source), "layout": meta.get("layout"),
            "hash_source": meta.get("hash_source"), "meta": {k: v for k, v in meta.items()
                                                             if k not in ("layout", "hash_source")},
            **whole, "per_chunk": per,
            "per_chunk_refinement_violations": refinement_violations(whole, per),
            "transitivity": tr, "predictions": pred,
            "when": datetime.now(timezone.utc).isoformat()}


def append_result(path, entry):
    path = Path(path)
    doc = json.loads(path.read_text()) if path.exists() else {"runs": []}
    key = (entry.get("experiment"), entry.get("layout"))
    doc["runs"] = [r for r in doc["runs"] if (r.get("experiment"), r.get("layout")) != key] + [entry]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--predictions", default=str(PREDICTIONS))
    ap.add_argument("--out", default=str(RESULTS))
    a = ap.parse_args(argv)
    worlds, meta, diff = load_input(a.input)
    entry = analyse(worlds, experiment=a.experiment, source=a.input, meta=meta, diff=diff,
                    predictions=Path(a.predictions))
    append_result(a.out, entry)
    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
