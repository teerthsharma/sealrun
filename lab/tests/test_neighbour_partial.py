import json
import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anvil
import orderrun
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
CENTRE = (64, 64)
TICKET = "forceload add 1024 1024"
WAIT_SECS = 10
IST = timezone(timedelta(hours=5, minutes=30))
RESULT = Path(__file__).resolve().parents[1] / "results" / "neighbour_status.json"


class Lab(unittest.TestCase):
    def neighbour_of_full_chunk_is_not_yet_full(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            self.assertTrue(orderrun.wait_loaded(srv, CENTRE[0], CENTRE[1]))
            time.sleep(WAIT_SECS)
            srv.command("save-all flush")
            srv.stop()

            region = scratch["dir"] / "world" / "region"
            cx, cz = CENTRE
            paths = {
                "east": lambda d: (cx + d, cz),
                "north": lambda d: (cx, cz - d),
                "diagonal": lambda d: (cx + d, cz + d),
            }
            report = {}
            for label, at in paths.items():
                report[label] = {}
                for d in range(13):
                    x, z = at(d)
                    status = anvil.chunk_status(region, x, z)
                    report[label][str(d)] = status
                    print(f"{label} d={d} cx={x} cz={z} status={status!r}")

            payload = {
                "centre": list(CENTRE),
                "ticket": TICKET,
                "wait_secs": WAIT_SECS,
                "when": datetime.now(IST).isoformat(timespec="seconds"),
                "east": report["east"],
                "north": report["north"],
                "diagonal": report["diagonal"],
            }
            with open(RESULT, "w") as f:
                json.dump(payload, f, indent=1)

            self.assertEqual(report["east"]["0"], "full")
            self.assertNotEqual(report["east"]["1"], "full")
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
