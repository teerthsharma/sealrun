"""Q3: the order_edit p1 flow (run_fresh(edited=False)), with gametime read at each phase.

Usage: python lab/research/det_q3.py <tag>
Same calls as lab/tests/test_order_edit.py run_fresh(False): A ticket, settle A, settle A again,
B ticket, settle B, save-all flush, stop, window.box over LO..HI. Extra reads: `time query gametime`.
"""
import json
import pickle
import sys
import time
from pathlib import Path

import det_common as dc
import orderrun
import server
import serverdir
import test_order_edit as toe
import window


def main(tag: str) -> dict:
    scratch = dc.fresh_scratch()
    srv = None
    phases = []
    settle_s = {}
    blocks = None
    t0 = time.monotonic()

    def mark(name):
        phases.append({"phase": name, "t_s": round(time.monotonic() - t0, 2), **dc.gametime(srv)})

    try:
        srv = server.boot(scratch)
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
        blocks = window.box(Path(scratch["dir"]) / "world" / "region", toe.LO, toe.HI)
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    # pickle: written and read only by this lane from its own scratch dumps, never untrusted input
    with open(dc.RAW / f"q3_{tag}.pkl", "wb") as f:
        pickle.dump(blocks, f, protocol=4)
    out = {
        "tag": tag,
        "positions": len(blocks),
        "not_full": sum(v is None for v in blocks.values()),
        "boot_s": round(srv.boot_secs, 2),
        "java_pid": srv.proc.pid,
        "settle_s": settle_s,
        "phases": phases,
    }
    (dc.RAW / f"q3_{tag}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "phases"}))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
