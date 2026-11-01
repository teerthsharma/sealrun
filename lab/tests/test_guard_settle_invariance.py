import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blockdiff
import orderrun
import server
import serverdir
import window

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
LO = (1024, 0, 1024)
HI = (1039, 255, 1039)


class Lab(unittest.TestCase):
    def _world(self, wait_s):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        srv = None
        try:
            srv = server.boot(scratch)
            self.assertTrue(orderrun.wait_loaded(srv, 64, 64))
            if wait_s:
                time.sleep(wait_s)
            srv.command("save-all flush")
            srv.stop()
            region = scratch["dir"] / "world" / "region"
            return window.box(region, LO, HI)
        finally:
            if srv is not None:
                srv.stop()
            serverdir.remove(scratch["dir"])

    def test_settle_does_not_change_blocks(self):
        a = self._world(0)
        b = self._world(60)
        fp_a = window.fingerprint(a)
        fp_b = window.fingerprint(b)
        print(f"fingerprint A (saved at once) {fp_a} positions {len(a)} not_full {sum(v is None for v in a.values())}")
        print(f"fingerprint B (saved after 60 s) {fp_b} positions {len(b)} not_full {sum(v is None for v in b.values())}")
        if fp_a != fp_b:
            d = blockdiff.diff(a, b)
            n = len(d["changed"]) + len(d["added"]) + len(d["missing"])
            print(f"differing positions {n} changed {len(d['changed'])} added {len(d['added'])} missing {len(d['missing'])}")
            for pos, va, vb in d["changed"][:10]:
                print(f"  pos {pos} A {va!r} B {vb!r}")
        self.assertEqual(fp_a, fp_b)


if __name__ == "__main__":
    unittest.main()
