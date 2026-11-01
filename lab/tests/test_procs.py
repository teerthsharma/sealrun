import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import procs


def alive(pid, secs=5.0):
    end = time.monotonic() + secs
    while True:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        if re.search(rf"\b{pid}\b", out) is None:
            return False
        if time.monotonic() > end:
            return True
        time.sleep(0.2)


class Lab(unittest.TestCase):
    def stop_process_kills_stubborn_child(self):
        child = (
            "import subprocess, sys, time\n"
            "g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
            "print(g.pid, flush=True)\n"
            "time.sleep(120)\n"
        )
        proc = subprocess.Popen([sys.executable, "-c", child], stdout=subprocess.PIPE, text=True)
        grandchild = None
        try:
            grandchild = int(proc.stdout.readline())
            calls = []
            started = time.monotonic()
            code = procs.stop(proc, ask=lambda: calls.append(1), grace=0.5)
            elapsed = time.monotonic() - started
            self.assertEqual(calls, [1])
            self.assertIsInstance(code, int)
            self.assertLess(elapsed, 10)
            self.assertIsNotNone(proc.poll())
            self.assertFalse(alive(grandchild))
        finally:
            if proc.poll() is None:
                proc.kill()
            if grandchild is not None and alive(grandchild, secs=0):
                subprocess.run(["taskkill", "/PID", str(grandchild), "/T", "/F"], capture_output=True)
            proc.stdout.close()

    def stop_returns_polite_exit_code(self):
        proc = subprocess.Popen([sys.executable, "-c", "import sys, time; time.sleep(0.3); sys.exit(3)"])
        calls = []
        started = time.monotonic()
        code = procs.stop(proc, ask=lambda: calls.append(1), grace=5)
        elapsed = time.monotonic() - started
        self.assertEqual(calls, [1])
        self.assertEqual(code, 3)
        self.assertLess(elapsed, 4)


if __name__ == "__main__":
    unittest.main()
