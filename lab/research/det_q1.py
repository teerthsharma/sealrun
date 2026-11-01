"""Q1: one fresh world, one forceload at chunk (64, 64), 5x5 tile dumped chunk by chunk.

Usage: python lab/research/det_q1.py <tag>
Writes raw per-chunk block dumps and a summary under DET_RAW (scratchpad, outside the repo).
"""
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import det_common as dc
import orderrun
import server
import serverdir
import test_order_edit as toe
import window


def chunk_names(blocks):
    return ["None" if blocks[p] is None else blocks[p] for p in sorted(blocks)]


def main(tag: str) -> dict:
    scratch = dc.fresh_scratch()
    srv = None
    out = {"tag": tag, "chunks": {}}
    try:
        srv = server.boot(scratch)
        out["boot_s"] = round(srv.boot_secs, 2)
        out["java_pid"] = srv.proc.pid
        if not orderrun.wait_loaded(srv, 64, 64):
            raise RuntimeError("chunk (64, 64) did not load")
        out["settle_s"] = toe.settle(srv, dc.TILE)
        srv.command("save-all flush")
        time.sleep(toe.SETTLE_S)
        out["stop_code"] = srv.stop()
        region = Path(scratch["dir"]) / "world" / "region"
        for cx, cz in dc.TILE:
            blocks = window.box(region, (cx * 16, 0, cz * 16), (cx * 16 + 15, 255, cz * 16 + 15))
            names = ["None" if blocks[p] is None else blocks[p] for p in sorted(blocks)]
            data = "\n".join(names).encode("utf-8")
            with gzip.open(dc.RAW / f"q1_{tag}_{cx}_{cz}.txt.gz", "wb") as f:
                f.write(data)
            out["chunks"][f"{cx},{cz}"] = {
                "n": len(names),
                "not_full": sum(n == "None" for n in names),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            del blocks, names, data
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    (dc.RAW / f"q1_{tag}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "chunks"}))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
