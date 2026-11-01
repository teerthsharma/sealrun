"""Q2: one fresh boot, spawn_area.read(half=32), flatten.grid to a 64x64 tile grid.

Usage: python lab/research/det_q2.py <tag>
Per cell: x, z, tile, ground y, ground block name. Raw summary goes under DET_RAW.
"""
import json
import sys
from collections import Counter

import det_common as dc
import flatten
import serverdir
import spawn_area


def main(tag: str) -> dict:
    scratch = dc.fresh_scratch()
    try:
        blocks, (sx, sz) = spawn_area.read(scratch, half=32)
    finally:
        serverdir.remove(scratch["dir"])
    java_pid = server._servers[-1].proc.pid
    x0, z0 = sx - 32, sz - 32
    grid = flatten.grid(blocks, x0, z0, 64, 64)
    ground = flatten._ground(blocks)
    cells = []
    for z in range(z0, z0 + 64):
        for x in range(x0, x0 + 64):
            gy, gname = ground[(x, z)]
            cells.append([x, z, grid[z - z0][x - x0], gy, gname])
    out = {
        "tag": tag,
        "spawn": [sx, sz],
        "x0": x0,
        "z0": z0,
        "tile_counts": {str(k): v for k, v in sorted(Counter(t for row in grid for t in row).items())},
        "cells": cells,
    }
    (dc.RAW / f"q2_{tag}.json").write_text(json.dumps(out) + "\n", encoding="utf-8")
    print(json.dumps({"tag": tag, "spawn": [sx, sz], "tile_counts": out["tile_counts"]}))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
