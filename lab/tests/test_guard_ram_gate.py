import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def _spawn_forbidden(*args, **kwargs):
    raise AssertionError("spawned")


class Lab(unittest.TestCase):
    def test_guard_ram_gate(self):
        self.assertFalse(server.start_allowed(1499, 0))
        self.assertTrue(server.start_allowed(1500, 0))
        self.assertTrue(server.start_allowed(9000, 2))
        self.assertFalse(server.start_allowed(9000, 3))
        self.assertFalse(server.start_allowed(9000, 4))

        saved = (server.free_mb, server.running_count, subprocess.Popen)
        try:
            subprocess.Popen = _spawn_forbidden
            with tempfile.TemporaryDirectory() as d:
                scratch = {"dir": d, "port": 1, "rcon_port": 2, "rcon_password": "x"}

                server.running_count = lambda: 0
                server.free_mb = lambda: 100
                with self.assertRaises(RuntimeError):
                    server.boot(scratch)

                server.free_mb = lambda: 9000
                server.running_count = lambda: 3
                with self.assertRaises(RuntimeError):
                    server.boot(scratch)
        finally:
            server.free_mb, server.running_count, subprocess.Popen = saved


if __name__ == "__main__":
    unittest.main()
