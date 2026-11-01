"""Compare the raw dumps of det_q1 / det_q2 / det_q3 and write lab/results/research/determinism.json.

Usage: python lab/research/det_analyze.py
Reads only the scratchpad dumps (DET_RAW); no server is started. Chunk dumps are compared
block by block (sorted (x, y, z) index, 16 x 256 x 16 per chunk).
"""
import gzip
import json
from collections import Counter

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


def load_chunk(prefix, tag, cx, cz):
    with gzip.open(dc.RAW / f"{prefix}_{tag}_{cx}_{cz}.txt.gz", "rb") as f:
        lines = f.read().decode("utf-8").split("\n")
    assert len(lines) == CHUNK_BLOCKS, (prefix, tag, cx, cz, len(lines))
    return lines


def compare_chunks(prefix, tags, chunks, examples, limit=20):
    per_chunk = {}
    for cx, cz in chunks:
        arrs = {t: load_chunk(prefix, t, cx, cz) for t in tags}
        row = {}
        for a, b in PAIRS:
            if a not in arrs or b not in arrs:
                continue
            A, B = arrs[a], arrs[b]
            diffs = [i for i in range(CHUNK_BLOCKS) if A[i] != B[i]]
            row[f"{a}-{b}"] = len(diffs)
            names = Counter((A[i], B[i]) for i in diffs)
            row.setdefault("name_pairs", {})[f"{a}-{b}"] = [[x, y, n] for (x, y), n in names.most_common(5)]
            for i in diffs[:3]:
                if len(examples) < limit:
                    examples.append({"prefix": prefix, "pair": f"{a}-{b}", "chunk": [cx, cz],
                                     "pos": list(chunk_index_to_pos(cx, cz, i)), "a": A[i], "b": B[i]})
        per_chunk[f"{cx},{cz}"] = row
    return per_chunk


def q1():
    raw = {t: json.loads((dc.RAW / f"q1_{t}.json").read_text()) for t in ("1", "2", "3")}
    examples = []
    per_chunk = compare_chunks("q1", list(raw), dc.TILE, examples)
    totals = {f"{a}-{b}": sum(r.get(f"{a}-{b}", 0) for r in per_chunk.values()) for a, b in PAIRS}
    return {
        "tile": "62..66 x 62..66, one forceload at (64, 64)",
        "blocks_per_chunk": CHUNK_BLOCKS,
        "runs": {t: {"boot_s": v["boot_s"], "settle_s": v["settle_s"], "stop_code": v["stop_code"],
                     "java_pid": v.get("java_pid"),
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
        base[t] = {
            "cells": len(d["cells"]),
            "water_tile_cells": sum(v == WATER for v in tiles[t].values()),
            "adj_water4": sum(near(tiles[t], x, z, four) for (x, z) in tiles[t]),
            "adj_water8": sum(near(tiles[t], x, z, eight) for (x, z) in tiles[t]),
        }
    pair_counts = {f"{a}-{b}": sum(tiles[a][k] != tiles[b][k] for k in tiles[a]) for a, b in PAIRS}
    differing = sorted(k for k in tiles["1"] if len({tiles[t][k] for t in tiles}) > 1)
    ground_only = sum(
        1 for k in tiles["1"]
        if len({tiles[t][k] for t in tiles}) == 1 and len({grounds[t][k] for t in grounds}) > 1
    )
    cells = []
    for k in differing:
        cells.append({
            "xz": list(k),
            "tile": {t: tiles[t][k] for t in tiles},
            "ground": {t: {"block": grounds[t][k][0], "y": grounds[t][k][1]} for t in grounds},
            "water_adj4": {t: near(tiles[t], k[0], k[1], four) for t in tiles},
            "water_adj8": {t: near(tiles[t], k[0], k[1], eight) for t in tiles},
        })
    return {
        "grid": "64x64 from per-chunk reads, window spawn -32..+31 (x0 = spawn_x - 32, z0 = spawn_z - 32)",
        "runs": {t: {"spawn": data[t]["spawn"], "java_pid": data[t].get("java_pid"),
                     "chunk_reads": data[t].get("chunk_reads"), "not_full_blocks": data[t].get("not_full_blocks"),
                     "tile_counts": data[t]["tile_counts"]} for t in data},
        "base_rate_per_boot": base,
        "differing_cells_per_pair": pair_counts,
        "differing_cells_union": len(differing),
        "ground_only_differences": ground_only,
        "differing_cells_next_to_water": {
            "any_4_neighbour_water": sum(any(c["water_adj4"].values()) for c in cells),
            "any_8_neighbour_water": sum(any(c["water_adj8"].values()) for c in cells),
            "any_cell_is_water_tile": sum(any(v == WATER for v in c["tile"].values()) for c in cells),
        },
        "cells": cells,
    }


def q3():
    raw = {t: json.loads((dc.RAW / f"q3_{t}.json").read_text()) for t in ("1", "2")}
    chunks = sorted({tuple(int(v) for v in k.split(",")) for k in raw["1"]["chunks"]})
    examples = []
    per_chunk = compare_chunks("q3", list(raw), chunks, examples)
    try:
        r2 = json.loads(ORDER_EDIT.read_text())
        round2 = {"noise_union_count": r2["noise"]["count"], "by_chunk": r2["noise"]["by_chunk"],
                  "note": "union of (p1 != p2) or (e1 != e2) in round 2; pure p1-vs-p2 count not recorded"}
    except FileNotFoundError:
        round2 = None
    return {
        "flow": "lab/tests/test_order_edit.py run_fresh(False), gametime read at each phase",
        "chunks": [list(c) for c in chunks],
        "not_full": {t: raw[t]["not_full"] for t in raw},
        "java_pid": {t: raw[t]["java_pid"] for t in raw},
        "settle_s": {t: raw[t]["settle_s"] for t in raw},
        "boot_s": {t: raw[t]["boot_s"] for t in raw},
        "gametime_phases": {t: [{"phase": x["phase"], "ticks": x["ticks"], "t_s": x["t_s"]}
                                for x in raw[t]["phases"]] for t in raw},
        "differing_blocks_per_chunk": per_chunk,
        "differing_blocks_total": {"1-2": sum(r.get("1-2", 0) for r in per_chunk.values())},
        "examples": examples,
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
                      "q3_total": results["q3"]["differing_blocks_total"]}))


if __name__ == "__main__":
    main()
