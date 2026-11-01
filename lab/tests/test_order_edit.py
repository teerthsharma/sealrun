import json
import os
import sys
import time
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockdiff
import edits
import orderrun
import server
import serverdir
import window

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
A = (64, 64)
B = (68, 64)
A_TILE = [(cx, cz) for cx in range(62, 67) for cz in range(62, 67)]
LO = (1024, 0, 1024)
HI = (1103, 255, 1039)
EDIT_LO = (1068, 30, 1024)
EDIT_HI = (1071, 33, 1027)
EDIT = [("break", x, y, z, None)
        for x in range(1068, 1072) for y in range(30, 34) for z in range(1024, 1028)]
EDIT_CELLS = {(x, y, z) for _, x, y, z, _ in EDIT}
RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = RESULTS / "order_edit.json"
B_TILE = [(cx, cz) for cx in range(66, 71) for cz in range(62, 67)]
SETTLE_S = 10.0


def chunk_key(c):
    return f"{c[0]},{c[1]}"


def settle(srv, tile, timeout=120.0):
    t0 = time.monotonic()
    for cx, cz in tile:
        while True:
            reply = srv.command(f"execute if block {cx * 16} 0 {cz * 16} minecraft:bedrock")
            if "Test passed" in reply:
                break
            if time.monotonic() - t0 > timeout:
                raise RuntimeError(f"chunk ({cx}, {cz}) not loaded after {timeout} s: {reply!r}")
            time.sleep(0.5)
    loaded_s = time.monotonic() - t0
    srv.command("save-all flush")
    time.sleep(SETTLE_S)
    return round(loaded_s, 2)


def run_fresh(edited):
    scratch = serverdir.make_scratch(SRC, ROOT)
    srv = None
    landed = 0
    secs = []
    try:
        srv = server.boot(scratch)
        if not orderrun.wait_loaded(srv, *A):
            raise RuntimeError(f"chunk {A} did not load")
        secs.append(settle(srv, A_TILE))
        if edited:
            for line in edits.commands(EDIT, A_TILE):
                reply = srv.command(line)
                print(f"{line} -> {reply!r}")
                landed += "Changed the block" in reply
        secs.append(settle(srv, A_TILE))
        if not orderrun.wait_loaded(srv, *B):
            raise RuntimeError(f"chunk {B} did not load")
        secs.append(settle(srv, B_TILE))
        srv.command("save-all flush")
        srv.stop()
        return window.box(Path(scratch["dir"]) / "world" / "region", LO, HI), landed, secs
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])


class Lab(unittest.TestCase):
    def edits_before_neighbour_change_cells_outside_edit(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        p1, _, s_p1 = run_fresh(False)
        p2, _, s_p2 = run_fresh(False)
        e1, landed, s_e1 = run_fresh(True)
        e2, _, s_e2 = run_fresh(True)
        print("setblock Changed the block replies", landed, "of", len(EDIT))
        d = blockdiff.diff(p1, e1)
        inside = [c for c in d["changed"] if c[0] in EDIT_CELLS]
        outside = [c for c in d["changed"] if c[0] not in EDIT_CELLS]
        by_chunk = Counter(chunk_key((x >> 4, z >> 4)) for (x, _, z), _, _ in outside)
        edit_before = Counter(p1[p] for p in EDIT_CELLS)
        rest = [p for p in p1 if p not in EDIT_CELLS]
        noise = [p for p in rest if p1[p] != p2[p] or e1[p] != e2[p]]
        attributed = [p for p in rest if p1[p] == p2[p] and e1[p] == e2[p] and p1[p] != e1[p]]
        noise_by_chunk = Counter(chunk_key((x >> 4, z >> 4)) for x, _, z in noise)
        attributed_by_chunk = Counter(chunk_key((x >> 4, z >> 4)) for x, _, z in attributed)
        not_full = [sum(v is None for v in w.values()) for w in (p1, p2, e1, e2)]
        fps = {k: window.fingerprint(w) for k, w in (("p1", p1), ("p2", p2), ("e1", e1), ("e2", e2))}
        counts = {
            "positions": len(p1),
            "inside_changed": len(inside),
            "outside_changed": len(outside),
            "added": len(d["added"]),
            "removed": len(d["missing"]),
        }
        examples = [[list(p), a, b] for p, a, b in outside[:20]]
        attr_examples = [[list(p), p1[p], e1[p]] for p in attributed[:20]]
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "A": list(A),
            "B": list(B),
            "edit": {"lo": list(EDIT_LO), "hi": list(EDIT_HI), "op": "break"},
            "positions": counts["positions"],
            "inside_changed": counts["inside_changed"],
            "outside_changed": counts["outside_changed"],
            "added": counts["added"],
            "removed": counts["removed"],
            "by_chunk_outside": dict(sorted(by_chunk.items())),
            "examples_outside": examples,
            "edit_before": dict(edit_before),
            "not_full": not_full,
            "fingerprints": fps,
            "noise": {"count": len(noise), "by_chunk": dict(sorted(noise_by_chunk.items()))},
            "edit_attributed": {"count": len(attributed), "by_chunk": dict(sorted(attributed_by_chunk.items())), "examples": attr_examples},
            "settle_s": {"p1": s_p1, "p2": s_p2, "e1": s_e1, "e2": s_e2},
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print("counts", json.dumps(counts))
        print("by_chunk_outside", json.dumps(dict(sorted(by_chunk.items()))))
        print("edit_before", json.dumps(dict(edit_before)))
        print("not_full", json.dumps(not_full))
        print("examples_outside", json.dumps(examples))
        for k, v in fps.items():
            print("fingerprint", k, v)
        print("noise", json.dumps({"count": len(noise), "by_chunk": dict(sorted(noise_by_chunk.items()))}))
        print("edit_attributed", json.dumps({"count": len(attributed), "by_chunk": dict(sorted(attributed_by_chunk.items()))}))
        print("settle_s", json.dumps({"p1": s_p1, "p2": s_p2, "e1": s_e1, "e2": s_e2}))
        self.assertEqual(not_full, [0, 0, 0, 0])
        self.assertTrue(all(e1[p] == "minecraft:air" for p in EDIT_CELLS))
        self.assertTrue(all(e2[p] == "minecraft:air" for p in EDIT_CELLS))
        self.assertTrue(OUT.is_file())


if __name__ == "__main__":
    unittest.main()
