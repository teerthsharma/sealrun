import os
import shutil
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))


def remove_scratch(d: Path) -> None:
    if not (d / serverdir.MARKER).is_file():
        return
    deadline = time.monotonic() + 10
    while True:
        try:
            shutil.rmtree(d)
            return
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.5)


class Lab(unittest.TestCase):
    def server_boots_to_done_and_answers_list(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        scratch = serverdir.make_scratch(SRC, ROOT)
        try:
            with server.boot(scratch) as srv:
                reply = srv.command("list")
                self.assertIn("There are 0", reply)
                self.assertGreater(srv.boot_secs, 0)
            self.assertIsNotNone(srv.proc.poll())
            self.assertEqual(server.running_count(), 0)
            print(f"boot_secs={srv.boot_secs:.2f} list={reply!r}")
        finally:
            remove_scratch(scratch["dir"])


if __name__ == "__main__":
    unittest.main()
