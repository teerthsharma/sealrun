"""Equality classes, repeat control and differing chunks for one spacing.

python lab/research/sq_classes.py <s>

Classes group orders whose per-chunk sha256 vectors are equal. The repeat control must differ in
0 chunks (hash and raw block count), else the class count for that spacing is void. Between classes
the representative of each class is compared with class 0 on raw dumps (compare.py).
Writes lab/results/research/squares_s<s>.json, keeping the predictions block.
"""
import json
import sys

import compare
import sq_plan


def load(s, labels):
    worlds = {}
    for lab in labels:
        path = sq_plan.RES / f"squares_s{s}_{lab}.json"
        worlds[lab] = json.loads(path.read_text(encoding="utf-8"))
    return worlds


def main():
    s = int(sys.argv[1])
    plan = sq_plan.plan(s)
    labels = [w["label"] for w in plan["worlds"]]
    orders = [lab for lab in labels if lab != sq_plan.CONTROL]
    worlds = load(s, labels)
    chunk_keys = list(worlds[orders[0]]["chunks"])
    vec = {lab: tuple(worlds[lab]["chunks"][ck]["sha256"] for ck in chunk_keys) for lab in labels}

    groups = {}
    for lab in orders:
        groups.setdefault(vec[lab], []).append(lab)
    classes = list(groups.values())
    reps = [members[0] for members in classes]

    ctrl_hash_diff = [ck for ck, a, b in zip(chunk_keys, vec[sq_plan.CONTROL], vec["ABCD"]) if a != b]
    ctrl = compare.diff_pairs(worlds, [("ABCD", sq_plan.CONTROL)], full=(("ABCD", sq_plan.CONTROL),))[("ABCD", sq_plan.CONTROL)]
    control_ok = not ctrl_hash_diff and ctrl["total"] == 0

    between = []
    if len(reps) > 1:
        pairs = [(reps[0], r) for r in reps[1:]]
        raw = compare.diff_pairs(worlds, pairs)
        for (a, b), members in zip(pairs, classes[1:]):
            hash_diff = [ck for ck, x, y in zip(chunk_keys, vec[a], vec[b]) if x != y]
            between.append({
                "class_reps": [a, b],
                "members": members,
                "differing_chunks": sorted(hash_diff),
                "differing_chunk_count": len(hash_diff),
                "differing_blocks": raw[(a, b)]["total"],
                "blocks_by_chunk": raw[(a, b)]["by_chunk"],
            })

    boots = [worlds[lab]["boot_secs"] for lab in labels]
    settles = [worlds[lab]["settle_s"] for lab in labels]
    pred = sq_plan.predictions(s)["predictions"]["cameron_8a3707c"]["classes_expected"]
    path = sq_plan.RES / f"squares_s{s}.json"
    base = json.loads(path.read_text(encoding="utf-8"))
    base["results"] = {
        "worlds_run": labels,
        "window_chunks": len(chunk_keys),
        "skipped_far": worlds[orders[0]]["skipped_far"],
        "class_count": len(classes),
        "void": not control_ok,
        "classes": [{"members": m, "size": len(m)} for m in classes],
        "repeat_control": {
            "pair": ["ABCD", sq_plan.CONTROL],
            "differing_chunks_by_hash": len(ctrl_hash_diff),
            "differing_blocks_raw": ctrl["total"],
            "passed": control_ok,
        },
        "between_classes": between,
        "boot_secs": {"min": min(boots), "max": max(boots), "per_world": {lab: worlds[lab]["boot_secs"] for lab in labels}},
        "settle_s": {"min": min(settles), "max": max(settles)},
        "commit_predictions": "see git log for squares_s%d.json pre-registration commit" % s,
        "cameron_8a3707c_expected": pred,
        "cameron_match": len(classes) == pred if control_ok else None,
        "polytope": "lab/results/research/quotient_polytope.json at research/polytope head 43faa40 (last file commit b04b482) has no squares-at-spacing-s rows",
    }
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: base["results"][k] for k in ("class_count", "void", "repeat_control", "cameron_match")}, indent=2))


if __name__ == "__main__":
    main()
