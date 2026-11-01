import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SERVE = Path(__file__).resolve().parents[1] / "serve.py"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def site_serves_on_7740():
    port = free_port()
    proc = subprocess.Popen([sys.executable, str(SERVE), "--port", str(port)])
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 5
        while True:
            if proc.poll() is not None:
                raise AssertionError(f"server exited early with {proc.returncode}")
            try:
                get(base + "/")
                break
            except OSError:
                if time.time() > deadline:
                    raise AssertionError("server did not answer within 5 s")
                time.sleep(0.1)

        status, headers, body = get(base + "/")
        assert status == 200 and b"sealrun" in body, f"GET / gave {status}"
        assert headers.get("Cache-Control") == "no-store", "GET / lacks no-store"

        status, headers, body = get(base + "/goals.json")
        assert status == 200, f"GET /goals.json gave {status}"
        assert isinstance(json.loads(body)["goals"], list), "goals.json has no goals list"
        assert headers.get("Cache-Control") == "no-store", "goals.json lacks no-store"
    finally:
        proc.kill()
        proc.wait()


if __name__ == "__main__":
    site_serves_on_7740()
    print("site_serves_on_7740: PASS")
