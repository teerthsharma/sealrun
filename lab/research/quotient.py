"""Equality classes, pairwise matrix and raw diff counts for one experiment's world jsons.

python lab/research/quotient.py <name> <predictions_sha|none> <out.json> <world.json> [<world.json> ...]

Pairs with the same order are repeat controls and always compared raw; their diff must be 0.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))


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
    sig = {lb: tuple(worlds[lb]["chunks"][k]["sha256"] for k in chunk_keys) for lb in labels}
    classes = []
    for lb in labels:
        for c in classes:
            if c["_sig"] == sig[lb]:
                c["worlds"].append(lb)
                break
        else:
            classes.append({"_sig": sig[lb], "worlds": [lb]})
    for i, c in enumerate(classes):
        c["class"] = i
        c["orders"] = [[list(t) for t in orders[lb]] for lb in c["worlds"]]
        del c["_sig"]
    per_chunk = {}
    for k in chunk_keys:
        groups = {}
        for lb in labels:
            groups.setdefault(worlds[lb]["chunks"][k]["sha256"], []).append(lb)
        per_chunk[k] = list(groups.values())
    pairs = list(combinations(labels, 2))
    controls = [(a, b) for a, b in pairs if orders[a] == orders[b]]
    diffs = compare.diff_pairs(worlds, pairs, full=controls)
    pair_rows = []
    for a, b in pairs:
        flags = "".join(
            "1" if worlds[a]["chunks"][k]["sha256"] == worlds[b]["chunks"][k]["sha256"] else "0"
            for k in chunk_keys
        )
        d = diffs[(a, b)]
        pair_rows.append({"a": a, "b": b, "control": (a, b) in controls, "equal_chunks": flags,
                          "diff_total": d["total"], "diff_by_chunk": d["by_chunk"]})
    report = {
        "experiment": name,
        "predictions_sha": None if pred == "none" else pred,
        "chunks": chunk_keys,
        "skipped_far": worlds[labels[0]].get("skipped_far", []),
        "worlds": [{"label": lb, "order": worlds[lb]["order"], "boot_secs": worlds[lb]["boot_secs"],
                    "settle_s": worlds[lb]["settle_s"],
                    "not_full_cells": sum(worlds[lb]["chunks"][k]["none"] for k in chunk_keys)}
                   for lb in labels],
        "classes": [{"class": c["class"], "worlds": c["worlds"], "orders": c["orders"]} for c in classes],
        "class_count": len(classes),
        "per_chunk_partition": per_chunk,
        "pairs": pair_rows,
        "controls_max_diff": max((r["diff_total"] for r in pair_rows if r["control"]), default=None),
        "when": datetime.now(IST).isoformat(),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: worlds {len(labels)} classes {len(classes)} controls_max_diff {report['controls_max_diff']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
