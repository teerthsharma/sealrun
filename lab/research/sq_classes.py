"""Equality classes, repeat noise and differing chunks for one spacing.

python lab/research/sq_classes.py <s>

Two repeat pairs per spacing: (ABCD, ABCD_rep) and (DCBA, DCBA_rep). A chunk is noisy when either
pair differs in its per-chunk sha256. Classes are grouped on the clean chunks only (where both pairs
agree); the class count on all chunks is reported for reference. Noisy chunks are listed apart with
the raw differing block count per pair. Between-class differences are reported on clean chunks only.
Writes the results block of lab/results/research/squares_s<s>.json, keeping predictions and amendments.
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


def lab_stats(worlds, labels):
    rows = {lab: worlds[lab].get("lab_servers") for lab in labels}
    have = {k: v for k, v in rows.items() if v}
    if not have:
        return {"per_world": rows}
    f = lambda key: [v[key] for v in have.values() if v.get(key) is not None]
    return {
        "per_world": {lab: {k: v[k] for k in ("at_launch", "at_boot", "at_last_sample", "max_during")}
                      for lab, v in have.items()},
        "at_boot": {"min": min(f("at_boot")), "max": max(f("at_boot"))},
        "at_last_sample": {"min": min(f("at_last_sample")), "max": max(f("at_last_sample"))},
        "max_during": {"min": min(f("max_during")), "max": max(f("max_during"))},
    }


def main():
    s = int(sys.argv[1])
    plan = sq_plan.plan(s)
    labels = [w["label"] for w in plan["worlds"]]
    controls = sq_plan.CONTROLS
    orders = [lab for lab in labels if lab not in controls]
    worlds = load(s, labels)
    chunk_keys = list(worlds[orders[0]]["chunks"])
    vec = {lab: tuple(worlds[lab]["chunks"][ck]["sha256"] for ck in chunk_keys) for lab in labels}

    pairs = [(base, ctrl) for ctrl, base in controls.items()]
    hash_diff = {ctrl: {ck for ck, a, b in zip(chunk_keys, vec[base], vec[ctrl]) if a != b}
                 for base, ctrl in pairs}
    noisy = sorted(set().union(*hash_diff.values()), key=chunk_keys.index)
    clean_idx = [i for i, ck in enumerate(chunk_keys) if ck not in set(noisy)]
    clean = [chunk_keys[i] for i in clean_idx]

    raw = compare.diff_pairs(worlds, pairs, full=tuple(pairs))
    noise_rows = []
    for ck in noisy:
        noise_rows.append({
            "chunk": ck,
            "blocks_by_pair": {f"{b}|{c}": raw[(b, c)]["by_chunk"].get(ck, 0) for b, c in pairs},
            "pairs_hash_differs": [f"{b}|{c}" for b, c in pairs if ck in hash_diff[c]],
        })

    def classes_over(keys_idx, labs):
        groups = {}
        for lab in labs:
            key = tuple(vec[lab][i] for i in keys_idx)
            groups.setdefault(key, []).append(lab)
        return list(groups.values())

    all_idx = list(range(len(chunk_keys)))
    classes_all = classes_over(all_idx, orders)
    classes = classes_over(clean_idx, orders)
    reps = [members[0] for members in classes]

    between = []
    if len(reps) > 1:
        bpairs = [(reps[0], r) for r in reps[1:]]
        braw = compare.diff_pairs(worlds, bpairs)
        for (a, b), members in zip(bpairs, classes[1:]):
            clean_set = set(clean)
            diff_clean = [ck for ck in clean if vec[a][chunk_keys.index(ck)] != vec[b][chunk_keys.index(ck)]]
            between.append({
                "class_reps": [a, b],
                "members": members,
                "differing_clean_chunks": diff_clean,
                "differing_blocks_clean": sum(v for k, v in braw[(a, b)]["by_chunk"].items() if k in clean_set),
            })

    boots = [worlds[lab]["boot_secs"] for lab in labels]
    settles = [worlds[lab]["settle_s"] for lab in labels]
    path = sq_plan.RES / f"squares_s{s}.json"
    base = json.loads(path.read_text(encoding="utf-8"))
    pred = base["predictions"]["predictions"]["cameron_8a3707c"]["classes_expected"]
    base["results"] = {
        "worlds_run": labels,
        "window_chunks": len(chunk_keys),
        "clean_chunks": len(clean),
        "noisy_chunks": len(noisy),
        "class_count_clean": len(classes),
        "classes_clean": [{"members": m, "size": len(m)} for m in classes],
        "class_count_all_chunks_reference": len(classes_all),
        "noisy_chunk_list": noise_rows,
        "repeat_pairs": {f"{b}|{c}": {"differing_chunks_by_hash": len(hash_diff[c]),
                                      "differing_blocks_raw": raw[(b, c)]["total"]} for b, c in pairs},
        "between_classes": between,
        "boot_secs": {"min": min(boots), "max": max(boots), "per_world": {lab: worlds[lab]["boot_secs"] for lab in labels}},
        "settle_s": {"min": min(settles), "max": max(settles)},
        "lab_servers": lab_stats(worlds, labels),
        "cameron_8a3707c_expected": pred,
        "cameron_match_clean": len(classes) == pred,
        "polytope": "lab/results/research/quotient_polytope.json at research/polytope head 43faa40 (last file commit b04b482) has no squares-at-spacing-s rows",
    }
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    summary = {k: base["results"][k] for k in ("class_count_clean", "class_count_all_chunks_reference",
                                               "noisy_chunks", "clean_chunks", "cameron_match_clean")}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
