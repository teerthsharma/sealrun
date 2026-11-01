import time
from pathlib import Path

import server
import window


def wait_loaded(client, cx, cz, timeout=30.0, poll=0.5, sleep=time.sleep):
    x, z = cx * 16, cz * 16
    client.command(f"forceload add {x} {z}")
    waited = 0.0
    while True:
        if "Test passed" in client.command(f"execute if block {x} 0 {z} minecraft:bedrock"):
            return True
        if waited >= timeout:
            return False
        sleep(poll)
        waited += poll


def run_order(scratch, order):
    srv = server.boot(scratch)
    try:
        for cx, cz in order:
            if not wait_loaded(srv, cx, cz):
                raise RuntimeError(f"chunk ({cx}, {cz}) did not load")
            srv.command("save-all flush")
    finally:
        srv.stop()
    xs = [cx for cx, _ in order]
    zs = [cz for _, cz in order]
    lo = (min(xs) * 16, 0, min(zs) * 16)
    hi = (max(xs) * 16 + 15, 255, max(zs) * 16 + 15)
    return window.box(Path(scratch["dir"]) / "world" / "region", lo, hi)
