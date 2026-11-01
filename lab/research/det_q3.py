"""Q3: the order_edit p1 flow (run_fresh(edited=False)), with gametime read at each phase.

Usage: python lab/research/det_q3.py <tag>
Same calls as lab/tests/test_order_edit.py run_fresh(False): A ticket, settle A, settle A again,
B ticket, settle B, save-all flush, stop. Extra reads: `time query gametime`.
The test window LO..HI is read one chunk at a time and each chunk is dumped like det_q1.
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
from det_q1 import chunk_names


def main(tag: str) -> dict:
    scratch = dc.fresh_scratch()
    srv = None
    phases = []
    settle_s = {}
    chunks = {}
    t0 = time.monotonic()

    def mark(name):
        phases.append({"phase": name, "t_s": round(time.monotonic() - t0, 2), **dc.gametime(srv)})

    try:
        srv = server.boot(scratch)
        java_pid = srv.proc.pid
        mark("boot")
        if not orderrun.wait_loaded(srv, *toe.A):
            raise RuntimeError("A did not load")
        mark("A ticket loaded")
        settle_s["A"] = toe.settle(srv, toe.A_TILE)
        mark("settle A")
        settle_s["A2"] = toe.settle(srv, toe.A_TILE)
        mark("settle A again")
        if not orderrun.wait_loaded(srv, *toe.B):
            raise RuntimeError("B did not load")
        mark("B ticket loaded")
        settle_s["B"] = toe.settle(srv, toe.B_TILE)
        mark("settle B")
        srv.command("save-all flush")
        srv.stop()
        region = Path(scratch["dir"]) / "world" / "region"
        for cx in range(toe.LO[0] >> 4, (toe.HI[0] >> 4) + 1):
            for cz in range(toe.LO[2] >> 4, (toe.HI[2] >> 4) + 1):
                blocks = window.box(region, (cx * 16, toe.LO[1], cz * 16), (cx * 16 + 15, toe.HI[1], cz * 16 + 15))
                names = chunk_names(blocks)
                data = "\n".join(names).encode("utf-8")
                with gzip.open(dc.RAW / f"q3_{tag}_{cx}_{cz}.txt.gz", "wb") as f:
                    f.write(data)
                chunks[f"{cx},{cz}"] = {"n": len(names), "not_full": sum(n == "None" for n in names),
                                        "sha256": hashlib.sha256(data).hexdigest()}
                del blocks, names, data
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    out = {
        "tag": tag,
        "chunks": chunks,
        "not_full": sum(c["not_full"] for c in chunks.values()),
        "boot_s": round(srv.boot_secs, 2),
        "java_pid": java_pid,
        "settle_s": settle_s,
        "phases": phases,
    }
    (dc.RAW / f"q3_{tag}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("phases", "chunks")}))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
