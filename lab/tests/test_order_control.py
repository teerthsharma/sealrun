import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockdiff
import orderrun
import serverdir
import window

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
ORDER = [(64, 64), (65, 64)]
OUT = Path(__file__).resolve().parents[1] / "results" / "order_control.json"


class Lab(unittest.TestCase):
    def same_order_twice_gives_zero_diff(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        try:
            a = orderrun.run_order(scratch, ORDER)
        finally:
            serverdir.remove(scratch["dir"])
        scratch = serverdir.make_scratch(SRC, ROOT)
        try:
            b = orderrun.run_order(scratch, ORDER)
        finally:
            serverdir.remove(scratch["dir"])
        d = blockdiff.diff(a, b)
        counts = {
            "changed": len(d["changed"]),
            "added": len(d["added"]),
            "removed": len(d["missing"]),
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "order": [list(c) for c in ORDER],
            "runs": 2,
            "positions": len(a),
            "changed": counts["changed"],
            "added": counts["added"],
            "removed": counts["removed"],
            "fingerprints": [window.fingerprint(a), window.fingerprint(b)],
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(counts["changed"], 0)
        self.assertEqual(counts["added"], 0)
        self.assertEqual(counts["removed"], 0)


if __name__ == "__main__":
    unittest.main()
