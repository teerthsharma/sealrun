"""Equality classes, pairwise matrix and raw diff counts for one experiment's world jsons.

python lab/research/quotient.py <name> <predictions_sha|none> <out.json> <world.json> [<world.json> ...]

A control is a pair of worlds with the same order. A chunk agrees when every control pair has
the same sha256 there. Classes are computed on agreeing chunks only; noisy chunks are listed with
their control diff counts; order_dependent_chunks are agreeing chunks whose hashes differ across orders.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))


def group(labels, keys, worlds):
    groups = {}
    for lb in labels:
        sig = tuple(worlds[lb]["chunks"][k]["sha256"] for k in keys)
        groups.setdefault(sig, []).append(lb)
    return list(groups.values())


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    name, pred, out, *files = argv
    worlds = {}
    for f in files:
        worlds[Path(f).stem] = json.loads(Path(f).read_text(encoding="utf-8"))
    labels = sorted(worlds)
    chunk_keys = list(worlds[labels[0]]["chunks"])
    for lb in labels:
        if list(worlds[lb]["chunks"]) != chunk_keys:
            sys.exit(f"{lb} covers different chunks")
    orders = {lb: [tuple(c) for c in worlds[lb]["order"]] for lb in labels}
    pairs = list(combinations(labels, 2))
    controls = [(a, b) for a, b in pairs if orders[a] == orders[b]]
    diffs = compare.diff_pairs(worlds, pairs, full=controls)

    def sha(lb, k):
        return worlds[lb]["chunks"][k]["sha256"]

    status, noisy = {}, {}
    for k in chunk_keys:
        agree = None if not controls else all(sha(a, k) == sha(b, k) for a, b in controls)
        status[k] = {"repeat_agree": agree, "distinct_hashes": len({sha(lb, k) for lb in labels})}
        if agree is False:
            noisy[k] = {f"{a}|{b}": diffs[(a, b)]["by_chunk"].get(k, 0)
                        for a, b in controls if sha(a, k) != sha(b, k)}
    agreeing = [k for k in chunk_keys if status[k]["repeat_agree"] is True]
    order_dep = [k for k in agreeing if status[k]["distinct_hashes"] > 1]
    cls_ag = group(labels, agreeing, worlds) if agreeing else []
    cls_all = group(labels, chunk_keys, worlds)
    per_chunk = {k: group(labels, [k], worlds) for k in chunk_keys}
    pair_rows = []
    for a, b in pairs:
        flags = "".join("1" if sha(a, k) == sha(b, k) else "0" for k in chunk_keys)
        d = diffs[(a, b)]
        pair_rows.append({"a": a, "b": b, "control": (a, b) in controls, "equal_chunks": flags,
                          "diff_total": d["total"], "diff_by_chunk": d["by_chunk"]})

    def orders_of(group_labels):
        return [[list(t) for t in orders[lb]] for lb in group_labels]

    report = {
        "experiment": name,
        "predictions_sha": None if pred == "none" else pred,
        "chunks": chunk_keys,
        "skipped_far": worlds[labels[0]].get("skipped_far", []),
        "worlds": [{"label": lb, "order": worlds[lb]["order"], "boot_secs": worlds[lb]["boot_secs"],
                    "settle_s": worlds[lb]["settle_s"],
                    "not_full_cells": sum(worlds[lb]["chunks"][k]["none"] for k in chunk_keys),
                    "servers": worlds[lb].get("servers")}
                   for lb in labels],
        "repeat_controls": [{"a": a, "b": b, "diff_total": diffs[(a, b)]["total"],
                             "diff_by_chunk": diffs[(a, b)]["by_chunk"]} for a, b in controls],
        "controls_max_diff": max((diffs[p]["total"] for p in controls), default=None),
        "agreeing_chunks": agreeing,
        "noisy_chunks": noisy,
        "order_dependent_chunks": order_dep,
        "classes_agreeing_chunks": [{"class": i, "worlds": g, "orders": orders_of(g)}
                                    for i, g in enumerate(cls_ag)],
        "class_count_agreeing_chunks": len(cls_ag),
        "class_count_all_chunks_hash": len(cls_all),
        "chunk_status": status,
        "per_chunk_partition": per_chunk,
        "pairs": pair_rows,
        "when": datetime.now(IST).isoformat(),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: worlds {len(labels)} agreeing_chunks {len(agreeing)}/{len(chunk_keys)} "
          f"classes_agreeing {len(cls_ag)} classes_all_hash {len(cls_all)} "
          f"noisy_chunks {len(noisy)} controls_max_diff {report['controls_max_diff']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
