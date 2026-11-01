import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockdiff
import ores
import orderrun
import serverdir
import window

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
AB_ORDER = [(64, 64), (65, 64)]
BA_ORDER = [(65, 64), (64, 64)]
RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = RESULTS / "order_pair.json"
CONTROL = RESULTS / "order_control.json"


def chunk_key(c):
    return f"{c[0]},{c[1]}"


def run_fresh(order):
    scratch = serverdir.make_scratch(SRC, ROOT)
    try:
        return orderrun.run_order(scratch, order)
    finally:
        serverdir.remove(scratch["dir"])


class Lab(unittest.TestCase):
    def pair_ab_vs_ba_counts_differing_blocks(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        ab = run_fresh(AB_ORDER)
        ba = run_fresh(BA_ORDER)
        d = blockdiff.diff(ab, ba)
        by_chunk = {chunk_key(c): 0 for c in AB_ORDER}
        for (x, _, z), _, _ in d["changed"]:
            by_chunk[chunk_key((x >> 4, z >> 4))] += 1
        examples = [[list(p), a, b] for p, a, b in d["changed"][:20]]
        ores_ab = {chunk_key(c): v for c, v in ores.tally(ab).items()}
        ores_ba = {chunk_key(c): v for c, v in ores.tally(ba).items()}
        control = json.loads(CONTROL.read_text(encoding="utf-8"))
        control_fp = control["fingerprints"][0]
        fp_ab = window.fingerprint(ab)
        fp_ba = window.fingerprint(ba)
        counts = {
            "positions": len(ab),
            "changed": len(d["changed"]),
            "added": len(d["added"]),
            "removed": len(d["missing"]),
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "orders": [[list(c) for c in AB_ORDER], [list(c) for c in BA_ORDER]],
            "positions": counts["positions"],
            "changed": counts["changed"],
            "added": counts["added"],
            "removed": counts["removed"],
            "examples": examples,
            "by_chunk": by_chunk,
            "ores": {"AB": ores_ab, "BA": ores_ba},
            "fingerprints": [fp_ab, fp_ba],
            "control_fingerprint": control_fp,
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print("counts", json.dumps(counts))
        print("by_chunk", json.dumps(by_chunk))
        print("ores AB", json.dumps(ores_ab))
        print("ores BA", json.dumps(ores_ba))
        print("examples", json.dumps(examples))
        print("fingerprint AB", fp_ab)
        print("fingerprint BA", fp_ba)
        print("control fingerprint", control_fp)
        self.assertEqual(fp_ab, control_fp)
        self.assertTrue(OUT.is_file())


if __name__ == "__main__":
    unittest.main()
