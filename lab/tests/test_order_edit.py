import json
import os
import sys
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


def chunk_key(c):
    return f"{c[0]},{c[1]}"


def run_fresh(edited):
    scratch = serverdir.make_scratch(SRC, ROOT)
    srv = None
    landed = 0
    try:
        srv = server.boot(scratch)
        if not orderrun.wait_loaded(srv, *A):
            raise RuntimeError(f"chunk {A} did not load")
        if edited:
            for line in edits.commands(EDIT, A_TILE):
                reply = srv.command(line)
                print(f"{line} -> {reply!r}")
                landed += "Changed the block" in reply
        if not orderrun.wait_loaded(srv, *B):
            raise RuntimeError(f"chunk {B} did not load")
        srv.command("save-all flush")
        srv.stop()
        return window.box(Path(scratch["dir"]) / "world" / "region", LO, HI), landed
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])


class Lab(unittest.TestCase):
    def edits_before_neighbour_change_cells_outside_edit(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        plain, _ = run_fresh(False)
        edited, landed = run_fresh(True)
        print("setblock Changed the block replies", landed, "of", len(EDIT))
        d = blockdiff.diff(plain, edited)
        inside = [c for c in d["changed"] if c[0] in EDIT_CELLS]
        outside = [c for c in d["changed"] if c[0] not in EDIT_CELLS]
        by_chunk = Counter(chunk_key((x >> 4, z >> 4)) for (x, _, z), _, _ in outside)
        edit_before = Counter(plain[p] for p in EDIT_CELLS)
        not_full = [sum(v is None for v in plain.values()), sum(v is None for v in edited.values())]
        fp_plain = window.fingerprint(plain)
        fp_edited = window.fingerprint(edited)
        counts = {
            "positions": len(plain),
            "inside_changed": len(inside),
            "outside_changed": len(outside),
            "added": len(d["added"]),
            "removed": len(d["missing"]),
        }
        examples = [[list(p), a, b] for p, a, b in outside[:20]]
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
            "fingerprints": [fp_plain, fp_edited],
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print("counts", json.dumps(counts))
        print("by_chunk_outside", json.dumps(dict(sorted(by_chunk.items()))))
        print("edit_before", json.dumps(dict(edit_before)))
        print("not_full", json.dumps(not_full))
        print("examples_outside", json.dumps(examples))
        print("fingerprint plain", fp_plain)
        print("fingerprint edited", fp_edited)
        self.assertEqual(not_full, [0, 0])
        self.assertTrue(all(edited[p] == "minecraft:air" for p in EDIT_CELLS))
        self.assertTrue(OUT.is_file())


if __name__ == "__main__":
    unittest.main()
