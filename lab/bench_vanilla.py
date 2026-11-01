import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import bench
import server
import serverdir

RESULT = Path(__file__).resolve().parent / "results" / "worlds_vanilla.json"
CAP = (1, 2)


def _lane(root: Path, secs: float, out: list, errs: list, i: int) -> None:
    scratch = None
    srv = None
    try:
        scratch = serverdir.make_scratch(bench.SRC, root)
        srv = server.boot(scratch)
        peak = bench.peak_mb(srv.proc.pid)
        start = time.monotonic()
        worlds = 0
        while time.monotonic() - start < secs:
            peak = max(peak, bench.peak_mb(srv.proc.pid))
            srv = server.reset(srv, root)
            worlds += 1
            peak = max(peak, bench.peak_mb(srv.proc.pid))
        out[i] = {"worlds": worlds, "peak": peak, "elapsed": time.monotonic() - start}
    except BaseException as e:
        errs.append(e)
    finally:
        try:
            if srv is not None:
                srv.stop()
        finally:
            if scratch is not None:
                serverdir.remove(scratch["dir"])


def measure(n: int, secs: float, root: Path) -> dict:
    if n not in CAP:
        raise ValueError(f"n must be 1 or 2 (owner cap of 2 real servers), got {n}")
    tasks = subprocess.run(["tasklist", "/FI", "IMAGENAME eq java.exe", "/NH", "/FO", "CSV"], capture_output=True, text=True).stdout
    other_java = sum(1 for line in tasks.splitlines() if line.startswith('"java.exe"'))
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    out = [None] * n
    errs: list = []
    threads = [threading.Thread(target=_lane, args=(root, secs, out, errs, i)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errs:
        raise errs[0]
    worlds = sum(o["worlds"] for o in out)
    per_minute = sum(o["worlds"] / o["elapsed"] for o in out) * 60
    peak_total = sum(o["peak"] for o in out)
    return {
        "n": n,
        "secs": secs,
        "worlds": worlds,
        "worlds_per_minute": round(per_minute, 2),
        "peak_mb_total": round(peak_total, 1),
        "mb_per_world": round(peak_total / n, 1),
        "other_java": other_java,
        "when": when,
    }


def main() -> None:
    root = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
    root.mkdir(parents=True, exist_ok=True)
    runs = [measure(1, 180, root), measure(2, 180, root)]
    result = {"runs": runs, "not_run": {"n": 3, "why": "owner cap of 2 real servers"}}
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(RESULT.read_text(), end="")


if __name__ == "__main__":
    main()
