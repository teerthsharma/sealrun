"""Noise lane analysis: read the per-world JSON and chunk dumps written by noise_world.py.

Usage: python lab/research/noise_analyze.py
Reads only the scratchpad dumps (NOISE_RAW); no server is started. Writes lab/results/research/noise.json.
Per condition: per-chunk distinct sha256 across boots, pairwise differing blocks, y range and block names
of differing positions, distance of each differing block to the nearest chunk edge (0 = outermost block
row of its chunk), and concurrent-server counts at boot and at save.
"""
import gzip
import itertools
import json
from collections import Counter

import det_common as dc
import noise_world as nw

CHUNK_BLOCKS = 16 * 256 * 16
CONDS = ("a", "b", "c")
OUT = dc.REPO / "lab" / "results" / "research" / "noise.json"
Q1 = dc.REPO / "lab" / "results" / "research" / "determinism.json"


def pos_of(cx, cz, i):
    return (cx * 16 + i // 4096, (i // 16) % 256, cz * 16 + i % 16)


def edge(x, z):
    lx, lz = x % 16, z % 16
    sides = {"x-": lx, "x+": 15 - lx, "z-": lz, "z+": 15 - lz}
    side = min(sides, key=sides.get)
    return sides[side], side


def load(cond, tag, cx, cz):
    with gzip.open(nw.RAW / f"noise_{cond}_{tag}_{cx}_{cz}.txt.gz", "rb") as f:
        lines = f.read().decode("utf-8").split("\n")
    assert len(lines) == CHUNK_BLOCKS, (cond, tag, cx, cz, len(lines))
    return lines


def conc(w, key):
    c = w[key]
    return {"slot_dirs_live": c["slot_dirs_live"], "slot_dirs": c["slot_dirs"],
            "java_total": c["java_total"], "java_cmdline_lab": c["java_cmdline_lab"],
            "java_cwd_lab": c["java_cwd_lab"]}


def summarize(cond):
    paths = sorted(nw.RAW.glob(f"noise_{cond}_*.json"))
    if not paths:
        return None
    worlds = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    tags = [w["tag"] for w in worlds]
    per_chunk_distinct, per_chunk_states, pair_totals, per_chunk_pairs = {}, {}, Counter(), {}
    names, ys, edges, positions, union = Counter(), [], Counter(), [], set()
    for cx, cz in dc.TILE:
        key = f"{cx},{cz}"
        shas = {t: w["chunks"][key]["sha256"] for t, w in zip(tags, worlds)}
        per_chunk_distinct[key] = len(set(shas.values()))
        groups = {}
        for t, h in shas.items():
            groups.setdefault(h, []).append(t)
        per_chunk_states[key] = sorted(groups.values())
        if per_chunk_distinct[key] == 1:
            continue
        arrs = {t: load(cond, t, cx, cz) for t in tags}
        row = {}
        for a, b in itertools.combinations(tags, 2):
            diffs = [i for i in range(CHUNK_BLOCKS) if arrs[a][i] != arrs[b][i]]
            pair_totals[f"{a}-{b}"] += len(diffs)
            if diffs:
                row[f"{a}-{b}"] = len(diffs)
            for i in diffs:
                x, y, z = pos_of(cx, cz, i)
                d, side = edge(x, z)
                names[(arrs[a][i], arrs[b][i])] += 1
                ys.append(y)
                edges[d] += 1
                union.add((x, y, z))
                positions.append({"pair": f"{a}-{b}", "chunk": [cx, cz], "pos": [x, y, z],
                                  "a": arrs[a][i], "b": arrs[b][i], "edge": d, "side": side})
        per_chunk_pairs[key] = row
        del arrs
    return {
        "tags": tags,
        "worlds": [{
            "tag": w["tag"], "pre_flush_wait_s": w["pre_flush_wait_s"], "ring_ticket": w["ring_ticket"],
            "free_mb_before_boot": w["free_mb_before_boot"], "boot_s": w["boot_s"],
            "java_pid": w["java_pid"], "tile_load_s": w["tile_load_s"], "ring_load_s": w.get("ring_load_s"),
            "stop_code": w["stop_code"], "not_full": sum(c["not_full"] for c in w["chunks"].values()),
            "conc_boot": conc(w, "conc_boot"), "conc_save": conc(w, "conc_save"),
        } for w in worlds],
        "per_chunk_distinct_sha": per_chunk_distinct,
        "per_chunk_states": {k: v for k, v in per_chunk_states.items() if len(v) > 1},
        "pair_diffs_total": {k: pair_totals[k] for k in sorted(pair_totals)},
        "pair_diffs_per_chunk": per_chunk_pairs,
        "union_differing_blocks": len(union),
        "y_range": [min(ys), max(ys)] if ys else None,
        "block_name_pairs": [[a, b, n] for (a, b), n in names.most_common(12)],
        "edge_distance_histogram": {str(d): edges[d] for d in sorted(edges)},
        "positions": positions,
    }


def main():
    q1 = json.loads(Q1.read_text(encoding="utf-8"))
    out = {
        "lane": "noise",
        "run": "n3",
        "branch": "research/noise",
        "question": "the same build order does not always give the same world: where does the disagreement live, what drives it",
        "tile": "62..66 x 62..66 chunks, read per chunk; one ticket at (64, 64) unless condition c",
        "conditions": {
            "a": "settle 10 s (det_q1 protocol: load, flush, 10 s, flush, 10 s, stop)",
            "b": "settle 60 s: 60 s after the tile loads, before the first flush; then the a tail",
            "c": "settle 10 s plus a ticket on the 24 chunks of the distance-3 ring; then the a tail; only the 5x5 is read",
        },
        "reference_determinism_q1": {"boots": 3, "differing_blocks_total": q1["q1"]["differing_blocks_total"],
                                     "note": "determinism.json q1, same protocol as condition a, 3 boots"},
        "blocks_per_chunk": CHUNK_BLOCKS,
        "results": {},
    }
    for cond in CONDS:
        s = summarize(cond)
        if s is not None:
            out["results"][cond] = s
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for cond, s in out["results"].items():
        split = sum(v > 1 for v in s["per_chunk_distinct_sha"].values())
        print(cond, "worlds", s["tags"], "chunks_with_disagreement", split, "pairs", s["pair_diffs_total"],
              "union", s["union_differing_blocks"], "y", s["y_range"])


if __name__ == "__main__":
    main()
