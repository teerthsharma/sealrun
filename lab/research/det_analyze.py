"""Compare the raw dumps of det_q1 / det_q2 / det_q3 and write lab/results/research/determinism.json.

Usage: python lab/research/det_analyze.py
Reads only the scratchpad dumps (DET_RAW); no server is started.
"""
import gzip
import json
import pickle
from collections import Counter

import blockdiff
import det_common as dc
import flatten

PAIRS = [("1", "2"), ("1", "3"), ("2", "3")]
WATER = flatten.TILES["water"]
OUT = dc.REPO / "lab" / "results" / "research" / "determinism.json"
ORDER_EDIT = dc.REPO / "lab" / "results" / "order_edit.json"
CHUNK_BLOCKS = 16 * 256 * 16


def chunk_index_to_pos(cx, cz, i):
    return (cx * 16 + i // 4096, (i // 16) % 256, cz * 16 + i % 16)


def self_check():
    assert chunk_index_to_pos(0, 0, 0) == (0, 0, 0)
    assert chunk_index_to_pos(1, 1, 1) == (16, 0, 17)
    assert chunk_index_to_pos(0, 0, 16) == (0, 1, 0)
    assert chunk_index_to_pos(0, 0, 4096) == (1, 0, 0)
    assert chunk_index_to_pos(0, 0, CHUNK_BLOCKS - 1) == (15, 255, 15)


def load_chunk(tag, cx, cz):
    with gzip.open(dc.RAW / f"q1_{tag}_{cx}_{cz}.txt.gz", "rb") as f:
        lines = f.read().decode("utf-8").split("\n")
    assert len(lines) == CHUNK_BLOCKS, (tag, cx, cz, len(lines))
    return lines


def q1():
    raw = {t: json.loads((dc.RAW / f"q1_{t}.json").read_text()) for t in ("1", "2", "3")}
    per_chunk = {}
    examples = []
    for cx, cz in dc.TILE:
        arrs = {t: load_chunk(t, cx, cz) for t in raw}
        row = {}
        for a, b in PAIRS:
            A, B = arrs[a], arrs[b]
            diffs = [i for i in range(CHUNK_BLOCKS) if A[i] != B[i]]
            row[f"{a}-{b}"] = len(diffs)
            for i in diffs[:3]:
                if len(examples) < 20:
                    examples.append({"pair": f"{a}-{b}", "chunk": [cx, cz],
                                     "pos": list(chunk_index_to_pos(cx, cz, i)),
                                     "a": A[i], "b": B[i]})
        per_chunk[f"{cx},{cz}"] = row
    totals = {p: sum(r[p] for r in per_chunk.values()) for p in ("1-2", "1-3", "2-3")}
    return {
        "tile": "62..66 x 62..66, one forceload at (64, 64)",
        "blocks_per_chunk": CHUNK_BLOCKS,
        "runs": {t: {"boot_s": v["boot_s"], "settle_s": v["settle_s"], "stop_code": v["stop_code"],
                     "not_full_chunks": sum(c["not_full"] for c in v["chunks"].values())}
                 for t, v in raw.items()},
        "differing_blocks_per_chunk": per_chunk,
        "differing_blocks_total": totals,
        "examples": examples,
    }


def near(tiles, x, z, offs):
    return any(tiles.get((x + dx, z + dz)) == WATER for dx, dz in offs)


def q2():
    data = {t: json.loads((dc.RAW / f"q2_{t}.json").read_text()) for t in ("1", "2", "3")}
    four = ((1, 0), (-1, 0), (0, 1), (0, -1))
    eight = four + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    tiles, grounds, base = {}, {}, {}
    for t, d in data.items():
        tiles[t] = {(x, z): tile for x, z, tile, _, _ in d["cells"]}
        grounds[t] = {(x, z): (gname, gy) for x, z, _, gy, gname in d["cells"]}
        n = len(d["cells"])
        base[t] = {
            "cells": n,
            "water_tile_cells": sum(v == WATER for v in tiles[t].values()),
            "adj_water4": sum(near(tiles[t], x, z, four) for (x, z) in tiles[t]),
            "adj_water8": sum(near(tiles[t], x, z, eight) for (x, z) in tiles[t]),
        }
    pair_counts = {}
    for a, b in PAIRS:
        pair_counts[f"{a}-{b}"] = sum(tiles[a][k] != tiles[b][k] for k in tiles[a])
    ground_only = sum(
        1 for k in tiles["1"]
        if len({tiles[t][k] for t in tiles}) == 1 and len({grounds[t][k] for t in grounds}) > 1
    )
    differing = sorted(k for k in tiles["1"] if len({tiles[t][k] for t in tiles}) > 1)
    cells = []
    for k in differing:
        cells.append({
            "xz": list(k),
            "tile": {t: tiles[t][k] for t in tiles},
            "ground": {t: {"block": grounds[t][k][0], "y": grounds[t][k][1]} for t in grounds},
            "water_adj4": {t: near(tiles[t], k[0], k[1], four) for t in tiles},
            "water_adj8": {t: near(tiles[t], k[0], k[1], eight) for t in tiles},
            "water_tile": {t: tiles[t][k] == WATER for t in tiles},
        })
    n_adj4 = sum(any(c["water_adj4"].values()) for c in cells)
    n_adj8 = sum(any(c["water_adj8"].values()) for c in cells)
    n_water = sum(any(c["water_tile"].values()) for c in cells)
    return {
        "grid": "spawn_area.read(half=32) then flatten.grid 64x64 (x0 = spawn_x - 32, z0 = spawn_z - 32)",
        "spawn": {t: data[t]["spawn"] for t in data},
        "tile_counts": {t: data[t]["tile_counts"] for t in data},
        "base_rate_per_boot": base,
        "differing_cells_per_pair": pair_counts,
        "differing_cells_union": len(differing),
        "ground_only_differences": ground_only,
        "differing_cells_next_to_water": {
            "4-neighbour": n_adj4,
            "8-neighbour": n_adj8,
            "cell_is_water_tile": n_water,
        },
        "cells": cells,
    }


def q3():
    runs = {}
    for t in ("1", "2"):
        # pickle: local dumps written by det_q3.py in this lane, not untrusted input
        with open(dc.RAW / f"q3_{t}.pkl", "rb") as f:
            blocks = pickle.load(f)
        meta = json.loads((dc.RAW / f"q3_{t}.json").read_text())
        runs[t] = (blocks, meta)
    d = blockdiff.diff(runs["1"][0], runs["2"][0])
    by_chunk = Counter((p[0] >> 4, p[2] >> 4) for p, _, _ in d["changed"])
    names = Counter((a, b) for _, a, b in d["changed"])
    ticks = {}
    for t, (_, meta) in runs.items():
        ph = meta["phases"]
        ticks[t] = [{"phase": x["phase"], "ticks": x["ticks"], "t_s": x["t_s"]} for x in ph]
    try:
        r2 = json.loads(ORDER_EDIT.read_text())
        round2 = {"noise_union_count": r2["noise"]["count"], "by_chunk": r2["noise"]["by_chunk"],
                  "note": "union of (p1 != p2) or (e1 != e2) in round 2; the pure p1-vs-p2 count was not recorded"}
    except FileNotFoundError:
        round2 = None
    return {
        "flow": "lab/tests/test_order_edit.py run_fresh(False), gametime read at each phase",
        "positions": len(runs["1"][0]),
        "not_full": {t: m["not_full"] for t, (_, m) in runs.items()},
        "settle_s": {t: m["settle_s"] for t, (_, m) in runs.items()},
        "boot_s": {t: m["boot_s"] for t, (_, m) in runs.items()},
        "gametime_phases": ticks,
        "changed_blocks": len(d["changed"]),
        "added": len(d["added"]),
        "missing": len(d["missing"]),
        "changed_by_chunk": {f"{cx},{cz}": n for (cx, cz), n in sorted(by_chunk.items())},
        "changed_name_pairs": [[a, b, n] for (a, b), n in names.most_common(10)],
        "examples": [[list(p), a, b] for p, a, b in d["changed"][:20]],
        "round2_reference": round2,
    }


def main():
    self_check()
    results = {
        "lane": "determinism",
        "run": "n3",
        "branch": "research/determinism",
        "q1": q1(),
        "q2": q2(),
        "q3": q3(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"q1_totals": results["q1"]["differing_blocks_total"],
                      "q2_pairs": results["q2"]["differing_cells_per_pair"],
                      "q2_union": results["q2"]["differing_cells_union"],
                      "q3_changed": results["q3"]["changed_blocks"]}))


if __name__ == "__main__":
    main()
