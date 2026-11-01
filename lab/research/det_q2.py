"""Q2: one fresh boot, spawn position from level.dat, 64x64 tile grid from per-chunk reads.

Usage: python lab/research/det_q2.py <tag>
Window = spawn -32 .. spawn +31 on x and z. Chunks are read one 16x256x16 window.box at a time.
Each column keeps only its ground block and its iron ore blocks (the only inputs flatten reads
besides the ground map), so flatten.grid and flatten._ground run on a sparse dict with the same answer.
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import det_common as dc
import flatten
import nbt
import server
import serverdir
import window

W = 64
IRON = "minecraft:iron_ore"


def column_keep(chunk, x0, z0, sparse, not_full):
    cols = {}
    for (x, y, z), name in chunk.items():
        if not (x0 <= x < x0 + W and z0 <= z < z0 + W):
            continue
        if name is None:
            not_full[0] += 1
            continue
        if name == IRON:
            sparse[(x, y, z)] = name
        if name in flatten.PASS or name.endswith("_leaves"):
            continue
        if (x, z) not in cols or y > cols[(x, z)][0]:
            cols[(x, z)] = (y, name)
    for (x, z), (y, name) in cols.items():
        sparse[(x, y, z)] = name


def main(tag: str) -> dict:
    scratch = dc.fresh_scratch()
    srv = None
    out = {"tag": tag}
    try:
        srv = server.boot(scratch)
        out["java_pid"] = srv.proc.pid
        srv.command("save-all flush")
        srv.stop()
        root = Path(scratch["dir"]) / "world"
        level = nbt.read(gzip.decompress((root / "level.dat").read_bytes()))[1]["Data"]
        sx, sz = level["SpawnX"], level["SpawnZ"]
        x0, z0 = sx - 32, sz - 32
        sparse, not_full, reads = {}, [0], 0
        for cx in range(x0 >> 4, ((x0 + W - 1) >> 4) + 1):
            for cz in range(z0 >> 4, ((z0 + W - 1) >> 4) + 1):
                chunk = window.box(root / "region", (cx * 16, 0, cz * 16), (cx * 16 + 15, 255, cz * 16 + 15))
                column_keep(chunk, x0, z0, sparse, not_full)
                reads += 1
                del chunk
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    grid = flatten.grid(sparse, x0, z0, W, W)
    ground = flatten._ground(sparse)
    cells = []
    for z in range(z0, z0 + W):
        for x in range(x0, x0 + W):
            gy, gname = ground[(x, z)]
            cells.append([x, z, grid[z - z0][x - x0], gy, gname])
    out.update({
        "spawn": [sx, sz],
        "x0": x0,
        "z0": z0,
        "chunk_reads": reads,
        "not_full_blocks": not_full[0],
        "tile_counts": {str(k): v for k, v in sorted(Counter(t for row in grid for t in row).items())},
        "cells": cells,
    })
    (dc.RAW / f"q2_{tag}.json").write_text(json.dumps(out) + "\n", encoding="utf-8")
    print(json.dumps({"tag": tag, "spawn": [sx, sz], "java_pid": out["java_pid"],
                      "chunk_reads": reads, "not_full_blocks": not_full[0],
                      "tile_counts": out["tile_counts"]}))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
