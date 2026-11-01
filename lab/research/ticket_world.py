"""One fresh world from a ticket order; saves the window chunk by chunk.

python lab/research/ticket_world.py <out.json> <x0,z0,x1,z1> <cx,cz> [<cx,cz> ...] [--skip-far]

Flow as lab/tests/test_order_collapse.py run_fresh and lab/orderrun.py run_order: boot, forceload
each ticket in order, then settle every window chunk (bedrock test, save-all flush, 10 s), stop, read.
Raw chunk dumps go to ~/sealrun-lab/raw/<stem>/ (outside the repo); only hashes go to out.json.
"""
import argparse
import json
import os
import sys
import time
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))

import orderrun  # noqa: E402
import ores  # noqa: E402
import server  # noqa: E402
import serverdir  # noqa: E402
import window  # noqa: E402

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RAW = ROOT / "raw"
REACH = 2
RAM_MB = 1500
SETTLE_S = 10.0
NONE = "\x00none"
IST = timezone(timedelta(hours=5, minutes=30))


def key(c):
    return f"{c[0]},{c[1]}"


def parse_chunk(text):
    cx, cz = (int(v) for v in text.split(","))
    return cx, cz


def parse_window(text):
    x0, z0, x1, z1 = (int(v) for v in text.split(","))
    if x0 > x1 or z0 > z1:
        raise ValueError(f"empty window {text}")
    return [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]


def reach(chunks, tickets):
    near, far = [], []
    for c in chunks:
        d = min(max(abs(c[0] - t[0]), abs(c[1] - t[1])) for t in tickets)
        (near if d <= REACH else far).append(c)
    return near, far


def dump(blocks):
    return "\n".join(NONE if v is None else v for _, v in sorted(blocks.items(), key=lambda kv: kv[0]))


def wait_ram():
    while server.free_mb() < RAM_MB:
        time.sleep(60)


def settle(srv, chunks, timeout=120.0):
    t0 = time.monotonic()
    for cx, cz in chunks:
        while True:
            reply = srv.command(f"execute if block {cx * 16} 0 {cz * 16} minecraft:bedrock")
            if "Test passed" in reply:
                break
            if time.monotonic() - t0 > timeout:
                raise RuntimeError(f"chunk ({cx}, {cz}) not loaded after {timeout} s: {reply!r}")
            time.sleep(0.5)
    srv.command("save-all flush")
    time.sleep(SETTLE_S)
    return round(time.monotonic() - t0, 2)


def build(stem, tickets, chunks):
    ROOT.mkdir(parents=True, exist_ok=True)
    wait_ram()
    scratch = serverdir.make_scratch(SRC, ROOT)
    srv = None
    try:
        srv = server.boot(scratch)
        boot_secs = round(srv.boot_secs, 2)
        for cx, cz in tickets:
            if not orderrun.wait_loaded(srv, cx, cz):
                raise RuntimeError(f"ticket ({cx}, {cz}) did not load")
            srv.command("save-all flush")
        settle_s = settle(srv, chunks)
        srv.stop()
        region = Path(scratch["dir"]) / "world" / "region"
        per_chunk = {}
        raw_dir = RAW / stem
        raw_dir.mkdir(parents=True, exist_ok=True)
        for cx, cz in chunks:
            lo = (cx * 16, 0, cz * 16)
            hi = (cx * 16 + 15, 255, cz * 16 + 15)
            blocks = window.box(region, lo, hi)
            (raw_dir / f"{cx}_{cz}.z").write_bytes(zlib.compress(dump(blocks).encode(), 6))
            per_chunk[key((cx, cz))] = {
                "sha256": window.fingerprint(blocks),
                "none": sum(v is None for v in blocks.values()),
                "ores": ores.tally(blocks).get((cx, cz), {o: 0 for o in ores.ORES}),
            }
            blocks.clear()
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    return {
        "boot_secs": boot_secs,
        "settle_s": settle_s,
        "chunks": per_chunk,
        "raw": str(raw_dir),
        "when": datetime.now(IST).isoformat(),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("window")
    p.add_argument("tickets", nargs="+")
    p.add_argument("--skip-far", action="store_true")
    a = p.parse_args(argv)
    tickets = [parse_chunk(t) for t in a.tickets]
    chunks = parse_window(a.window)
    chunks, far = reach(chunks, tickets)
    if far and not a.skip_far:
        sys.exit(f"refused: {len(far)} window chunks farther than {REACH} from every ticket: {far[:5]}")
    out = Path(a.out)
    stem = out.stem
    res = build(stem, tickets, chunks)
    res.update({
        "order": [list(t) for t in tickets],
        "window": a.window,
        "window_chunks": len(chunks),
        "skipped_far": [list(c) for c in far],
    })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(f"{stem} boot {res['boot_secs']} s settle {res['settle_s']} s chunks {len(chunks)} far {len(far)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
