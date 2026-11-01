import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockdiff
import orders
import orderrun
import serverdir
import window

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = RESULTS / "order_collapse.json"


def chunk_key(c):
    return f"{c[0]},{c[1]}"


def run_fresh(order):
    scratch = serverdir.make_scratch(SRC, ROOT)
    try:
        return orderrun.run_order(scratch, order)
    finally:
        serverdir.remove(scratch["dir"])


class Lab(unittest.TestCase):
    def same_first_chunk_orders_give_zero_diff(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        o1 = list(orders.square_orders(64, 64)[0])
        o2 = [o1[0]] + list(o1[:0:-1])
        w1 = run_fresh(o1)
        w2 = run_fresh(o2)
        wc = run_fresh(o1)
        control_d = blockdiff.diff(w1, wc)
        pair_d = blockdiff.diff(w1, w2)
        nones = [sum(1 for v in w.values() if v is None) for w in (w1, w2, wc)]
        fps = [window.fingerprint(w) for w in (w1, w2, wc)]
        by_chunk = {chunk_key(c): 0 for c in o1}
        for (x, _, z), _, _ in pair_d["changed"]:
            k = chunk_key((x >> 4, z >> 4))
            by_chunk[k] = by_chunk.get(k, 0) + 1
        examples = [[list(p), a, b] for p, a, b in pair_d["changed"][:20]]
        control_changed = len(control_d["changed"])
        pair_changed = len(pair_d["changed"])
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "orders": [[list(c) for c in o1], [list(c) for c in o2]],
            "positions": len(w1),
            "control_changed": control_changed,
            "pair_changed": pair_changed,
            "by_chunk_pair": by_chunk,
            "examples": examples,
            "fingerprints": fps,
            "not_full": nones,
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print("fingerprint O1", fps[0])
        print("fingerprint O2", fps[1])
        print("fingerprint control", fps[2])
        print("not_full", json.dumps(nones))
        print("control_changed", control_changed)
        print("pair_changed", pair_changed)
        print("by_chunk_pair", json.dumps(by_chunk))
        self.assertEqual(nones, [0, 0, 0])
        self.assertEqual(control_changed, 0)
        self.assertEqual(pair_changed, 0)


if __name__ == "__main__":
    unittest.main()
