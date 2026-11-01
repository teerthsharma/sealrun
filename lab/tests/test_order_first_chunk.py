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
import ores
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = RESULTS / "order_square.json"


def chunk_key(c):
    return f"{c[0]},{c[1]}"


def run_fresh(order):
    scratch = serverdir.make_scratch(SRC, ROOT)
    try:
        return orderrun.run_order(scratch, order)
    finally:
        serverdir.remove(scratch["dir"])


class Lab(unittest.TestCase):
    def four_first_chunk_classes_tallied(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        all_orders = orders.square_orders(64, 64)
        corners = orders.square(64, 64)
        built = [next(o for o in all_orders if o[0] == c) for c in corners]
        chunks = [chunk_key(c) for c in corners]
        worlds = [run_fresh(o) for o in built]
        classes = []
        for corner, order, world in zip(corners, built, worlds):
            changed = blockdiff.diff(worlds[0], world)["changed"]
            by_chunk = {k: 0 for k in chunks}
            for (x, _, z), _, _ in changed:
                k = chunk_key((x >> 4, z >> 4))
                by_chunk[k] = by_chunk.get(k, 0) + 1
            classes.append({
                "first_chunk": list(corner),
                "order": [list(p) for p in order],
                "differing_blocks": len(changed),
                "by_chunk": by_chunk,
                "none_cells": sum(1 for v in world.values() if v is None),
                "ores": {chunk_key(k): v for k, v in ores.tally(world).items()},
            })
        rows = []
        for order in all_orders:
            ci = corners.index(order[0])
            cls = classes[ci]
            measured = order == built[ci]
            rows.append({
                "order": [list(p) for p in order],
                "first_chunk": list(order[0]),
                "class_index": ci,
                "measured": measured,
                "differing_blocks": cls["differing_blocks"],
                "ores": cls["ores"],
                "inferred_from": None if measured else "n2-F6",
            })
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "classes": classes,
            "rows": rows,
            "when": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        for i, c in enumerate(classes):
            print(f"class {i} first_chunk {c['first_chunk']} differing_blocks {c['differing_blocks']}")
            print(f"class {i} by_chunk {json.dumps(c['by_chunk'])} None cells {c['none_cells']}")
            print(f"class {i} ores_64_64 {json.dumps(c['ores'].get('64,64'))}")
        self.assertEqual([c["none_cells"] for c in classes], [0, 0, 0, 0])
        self.assertEqual(classes[0]["differing_blocks"], 0)
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(1 for r in rows if r["measured"]), 4)
        for ci in range(4):
            self.assertEqual(sum(1 for r in rows if r["class_index"] == ci), 6)
        self.assertTrue(OUT.is_file())


if __name__ == "__main__":
    unittest.main()
