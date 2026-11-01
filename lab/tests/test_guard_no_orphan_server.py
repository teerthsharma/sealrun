import os
import shutil
import socket
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
LAB = Path(os.environ.get("SEALRUN_LAB", str(Path.home() / "sealrun-lab")))


def port_refused(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(5)
        try:
            s.connect(("127.0.0.1", port))
        except ConnectionRefusedError:
            return True
    return False


def rmtree_within(path: Path, secs: float = 10.0) -> bool:
    end = time.monotonic() + secs
    while True:
        try:
            shutil.rmtree(path)
            return True
        except OSError:
            if time.monotonic() >= end:
                return False
            time.sleep(0.5)


def drop_scratch(path: Path) -> None:
    if (path / serverdir.MARKER).exists():
        serverdir.remove(path)


class Lab(unittest.TestCase):
    def scratch(self) -> dict:
        scratch = serverdir.make_scratch(SRC, LAB)
        self.addCleanup(drop_scratch, scratch["dir"])
        return scratch

    def assert_no_orphan(self, scratch: dict) -> None:
        self.assertEqual(server.running_count(), 0, "running_count is not zero")
        self.assertTrue(port_refused(scratch["port"]), "game port still listening")
        self.assertTrue(port_refused(scratch["rcon_port"]), "rcon port still listening")
        self.assertTrue(rmtree_within(scratch["dir"]), "scratch folder locked: server still running")

    def test_guard_no_orphan_server(self):
        LAB.mkdir(parents=True, exist_ok=True)

        crash = self.scratch()
        srv = None
        with self.assertRaises(RuntimeError):
            with server.boot(crash) as srv:
                raise RuntimeError("crash on purpose")
        self.assertIsNotNone(srv, "boot did not start a server")
        self.assertIsNotNone(srv.proc.poll(), "crashed run left java running")
        self.assert_no_orphan(crash)

        stuck = self.scratch()
        with self.assertRaises(RuntimeError):
            server.boot(stuck, timeout=0.5)
        self.assert_no_orphan(stuck)


if __name__ == "__main__":
    unittest.main()
