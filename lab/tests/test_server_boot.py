import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import procs
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))


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
            serverdir.remove(scratch["dir"])

    def interrupt_during_boot_stops_the_process(self):
        real_popen = subprocess.Popen
        children = []

        def fake_popen(argv, **kwargs):
            if argv[0] != server.JAVA:
                return real_popen(argv, **kwargs)
            kept = {k: kwargs[k] for k in ("cwd", "stdout", "stderr", "creationflags")}
            child = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kept)
            children.append(child)
            return child

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        def stop_child():
            for child in children:
                if child.poll() is None:
                    procs.stop(child, grace=0)

        self.addCleanup(stop_child)
        scratch = {"dir": Path(tmp.name), "rcon_port": 1, "rcon_password": "unused"}
        with mock.patch.object(server.subprocess, "Popen", side_effect=fake_popen), \
                mock.patch.object(server, "start_allowed", return_value=True), \
                mock.patch.object(server, "_text", side_effect=[KeyboardInterrupt()]):
            with self.assertRaises(KeyboardInterrupt):
                server.boot(scratch)
        self.assertEqual(len(children), 1)
        end = time.monotonic() + 10
        while children[0].poll() is None and time.monotonic() < end:
            time.sleep(0.1)
        self.assertIsNotNone(children[0].poll(), "boot left the started process running")


if __name__ == "__main__":
    unittest.main()
