"""Noise lane: one world per call, one ticket at (64, 64), 5x5 tile dumped chunk by chunk.

Usage: python lab/research/noise_world.py <cond> <tag>
  a  settle 10 s: load the tile, flush, wait 10 s, flush, wait 10 s, stop (the det_q1 protocol)
  b  settle 60 s: as a, but 60 s pass after the tile loads, before the first flush
  c  settle 10 s plus a ticket on each chunk of the distance-3 ring (24 chunks), same tail as a
  s  as a, after the cwd-based exclusive wait (other lab JVMs under sealrun-lab)
  bx as b, after the cwd-based exclusive wait
  t  as a, after a gate that requires zero java processes of any cwd before boot; a sampler
     records every foreign java once a second from before boot to after stop; a world with any
     foreign java sample is marked solo=false
Run one world per call, inside slot.py. Chunk dumps and the per-world JSON go to NOISE_RAW (scratchpad).
"""
import gzip
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

import psutil

import det_common as dc
import orderrun
import server
import serverdir
import window

RAW = Path(os.environ.get(
    "NOISE_RAW",
    "C:/Users/seal/AppData/Local/Temp/claude/C--Users-seal-Documents-GitHub-sealrun/"
    "f708d1ce-97b8-4985-b4ab-75b219fa060b/scratchpad/noise",
))
LAB = Path.home() / "sealrun-lab"
CENTRE = (64, 64)
RING3 = [(cx, cz) for cx in range(61, 68) for cz in range(61, 68) if max(abs(cx - 64), abs(cz - 64)) == 3]
SETTLE_S = 10.0
PRE_FLUSH_S = {"a": 0.0, "b": 60.0, "c": 0.0, "s": 0.0, "bx": 60.0, "t": 0.0}
EXCLUSIVE = {"s", "bx"}
GATED = {"t"}
EXCLUSIVE_POLL_S = 15.0
EXCLUSIVE_TIMEOUT_S = 1200.0
GATE_TIMEOUT_S = 1200.0
SAMPLE_S = 1.0


def load_wait(srv, tile, timeout: float = 120.0) -> float:
    t0 = time.monotonic()
    for cx, cz in tile:
        while "Test passed" not in srv.command(f"execute if block {cx * 16} 0 {cz * 16} minecraft:bedrock"):
            if time.monotonic() - t0 > timeout:
                raise RuntimeError(f"chunk ({cx}, {cz}) not loaded after {timeout} s")
            time.sleep(0.5)
    return round(time.monotonic() - t0, 2)


def concurrent() -> dict:
    slots = []
    for d in sorted(LAB.glob(".slot*")):
        try:
            pid = int((d / "pid").read_text().strip() or 0)
        except (OSError, ValueError):
            continue
        slots.append({"dir": d.name, "pid": pid, "live": psutil.pid_exists(pid)})
    java_total, cmd_lab, cwd_lab = 0, [], []
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if not (p.info["name"] or "").lower().startswith("java"):
                continue
            java_total += 1
            if "sealrun-lab" in " ".join(p.info["cmdline"] or []):
                cmd_lab.append(p.pid)
            if "sealrun-lab" in (p.cwd() or ""):
                cwd_lab.append(p.pid)
        except (psutil.Error, OSError):
            continue
    return {
        "slot_dirs": len(slots),
        "slot_dirs_live": sum(s["live"] for s in slots),
        "slots": slots,
        "java_total": java_total,
        "java_cmdline_lab": len(cmd_lab),
        "java_cwd_lab": len(cwd_lab),
        "java_cwd_lab_pids": cwd_lab,
    }


def other_jvms() -> list:
    pids = []
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower().startswith("java") and "sealrun-lab" in (p.cwd() or ""):
                pids.append(p.pid)
        except (psutil.Error, OSError):
            continue
    return pids


def wait_exclusive() -> dict:
    t0 = time.monotonic()
    polls, first = 0, None
    while True:
        pids = other_jvms()
        polls += 1
        if first is None:
            first = len(pids)
        if not pids:
            return {"polls": polls, "waited_s": round(time.monotonic() - t0, 1),
                    "other_jvms_at_first_poll": first}
        if time.monotonic() - t0 > EXCLUSIVE_TIMEOUT_S:
            raise RuntimeError(f"other lab JVMs still running after {EXCLUSIVE_TIMEOUT_S} s: {pids}")
        time.sleep(EXCLUSIVE_POLL_S)


def java_procs() -> list:
    out = []
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower().startswith("java"):
                out.append(p)
        except psutil.Error:
            continue
    return out


def describe(p) -> dict:
    try:
        cwd = p.cwd()
    except psutil.Error:
        cwd = None
    try:
        ppid = p.ppid()
        parent = psutil.Process(ppid).name() if ppid else None
    except psutil.Error:
        ppid, parent = None, None
    try:
        name = p.name()
    except psutil.Error:
        name = None
    try:
        start = p.create_time()
    except psutil.Error:
        start = None
    return {"name": name, "pid": p.pid, "cwd": cwd, "ppid": ppid, "parent": parent, "start_time": start}


def wait_no_java() -> dict:
    t0 = time.monotonic()
    found, seen = [], set()
    while True:
        procs = java_procs()
        if not procs:
            return {"waited_s": round(time.monotonic() - t0, 1), "found": found}
        for p in procs:
            if p.pid not in seen:
                seen.add(p.pid)
                found.append({**describe(p), "found_at_s": round(time.monotonic() - t0, 1)})
        if time.monotonic() - t0 > GATE_TIMEOUT_S:
            raise RuntimeError(f"java still running after {GATE_TIMEOUT_S} s: {sorted(seen)}")
        try:
            procs[0].wait(timeout=EXCLUSIVE_POLL_S)
        except psutil.TimeoutExpired:
            pass
        except psutil.Error:
            pass


def _same_dir(a: str, b: str) -> bool:
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


class Sampler(threading.Thread):
    def __init__(self, own_dir: str):
        super().__init__(daemon=True)
        self.own_dir = own_dir
        self.samples = 0
        self.foreign_samples = 0
        self.seen = {}
        self._halt = threading.Event()

    def run(self):
        while not self._halt.is_set():
            self.samples += 1
            foreign = False
            for p in java_procs():
                try:
                    cwd = p.cwd()
                except psutil.Error:
                    cwd = None
                if cwd is not None and _same_dir(cwd, self.own_dir):
                    continue
                foreign = True
                d = describe(p)
                self.seen.setdefault(d["pid"], d)
            if foreign:
                self.foreign_samples += 1
            self._halt.wait(SAMPLE_S)

    def finish(self) -> dict:
        self._halt.set()
        self.join(timeout=10)
        return {"samples": self.samples, "foreign_samples": self.foreign_samples,
                "foreign_seen": list(self.seen.values())}


def world(cond: str, tag: str) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    out = {"cond": cond, "tag": tag, "pre_flush_wait_s": PRE_FLUSH_S[cond],
           "ring_ticket": cond == "c", "exclusive": cond in EXCLUSIVE, "gated": cond in GATED}
    if cond in EXCLUSIVE:
        out["exclusive_wait"] = wait_exclusive()
    if cond in GATED:
        out["java_gate"] = wait_no_java()
    free_before = server.free_mb()
    out["free_mb_before_boot"] = free_before
    scratch = dc.fresh_scratch()
    srv = None
    sampler = None
    try:
        if cond in GATED:
            sampler = Sampler(str(scratch["dir"]))
            sampler.start()
        srv = server.boot(scratch)
        out.update(boot_s=round(srv.boot_secs, 2), java_pid=srv.proc.pid, conc_boot=concurrent())
        if not orderrun.wait_loaded(srv, *CENTRE):
            raise RuntimeError("centre (64, 64) did not load")
        if cond == "c":
            t0 = time.monotonic()
            for cx, cz in RING3:
                if not orderrun.wait_loaded(srv, cx, cz):
                    raise RuntimeError(f"ring chunk ({cx}, {cz}) did not load")
            out["ring_load_s"] = round(time.monotonic() - t0, 2)
        out["tile_load_s"] = load_wait(srv, dc.TILE)
        time.sleep(PRE_FLUSH_S[cond])
        out["conc_save"] = concurrent()
        srv.command("save-all flush")
        time.sleep(SETTLE_S)
        srv.command("save-all flush")
        time.sleep(SETTLE_S)
        out["stop_code"] = srv.stop()
        if sampler is not None:
            out["sampling"] = sampler.finish()
            sampler = None
        region = Path(scratch["dir"]) / "world" / "region"
        chunks = {}
        for cx, cz in dc.TILE:
            blocks = window.box(region, (cx * 16, 0, cz * 16), (cx * 16 + 15, 255, cz * 16 + 15))
            names = ["None" if blocks[p] is None else blocks[p] for p in sorted(blocks)]
            data = "\n".join(names).encode("utf-8")
            with gzip.open(RAW / f"noise_{cond}_{tag}_{cx}_{cz}.txt.gz", "wb") as f:
                f.write(data)
            chunks[f"{cx},{cz}"] = {
                "n": len(names),
                "not_full": sum(n == "None" for n in names),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            del blocks, names, data
    finally:
        if sampler is not None:
            out["sampling"] = sampler.finish()
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    if cond in GATED:
        out["solo"] = out["sampling"]["foreign_samples"] == 0
    out["chunks"] = chunks
    (RAW / f"noise_{cond}_{tag}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("chunks", "conc_boot", "conc_save", "sampling", "java_gate")}))
    if cond in GATED:
        print(json.dumps({"samples": out["sampling"]["samples"], "foreign_samples": out["sampling"]["foreign_samples"],
                          "foreign_seen": out["sampling"]["foreign_seen"], "solo": out["solo"]}))
    return out


if __name__ == "__main__":
    if sys.argv[1] not in PRE_FLUSH_S:
        sys.exit(f"unknown condition {sys.argv[1]!r}")
    world(sys.argv[1], sys.argv[2])
