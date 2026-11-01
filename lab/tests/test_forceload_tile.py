import json
import os
import sys
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
IST = timezone(timedelta(hours=5, minutes=30))
RESULT = Path(__file__).resolve().parents[1] / "results" / "forceload_tile.json"
RAYS = {
    "east": (1, 0),
    "west": (-1, 0),
    "south": (0, 1),
    "north": (0, -1),
    "southeast": (1, 1),
    "southwest": (-1, 1),
    "northeast": (1, -1),
    "northwest": (-1, -1),
}
DISTANCES = range(4)


class Lab(unittest.TestCase):
    def forceload_tile_full_at_0_to_2_and_not_saved_at_3(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            self.assertTrue(orderrun.wait_loaded(srv, CENTRE[0], CENTRE[1]))
            srv.command("save-all flush")
            srv.stop()

            region = scratch["dir"] / "world" / "region"
            cx, cz = CENTRE
            rays = {
                name: {
                    str(d): anvil.chunk_status(region, cx + ux * d, cz + uz * d)
                    for d in DISTANCES
                }
                for name, (ux, uz) in RAYS.items()
            }
            payload = {
                "centre": list(CENTRE),
                "ticket": TICKET,
                "ticket_held_at_stop": True,
                "when": datetime.now(IST).isoformat(timespec="seconds"),
                "rays": rays,
            }
            with open(RESULT, "w") as f:
                json.dump(payload, f, indent=1)

            for name, by_d in rays.items():
                for d in DISTANCES:
                    want = "full" if d <= 2 else None
                    self.assertEqual(by_d[str(d)], want, f"{name} d={d}")
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
