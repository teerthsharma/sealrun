"""Run every squares world for one spacing, one at a time, each through slot.py.

python lab/research/sq_run.py <s>

Before each boot resmon.py --free must print >= 2500, else wait 60 s. A world that fails is
rerun once and both attempts are logged; a second failure stops the spacing. Finished worlds
(an existing per-world json) are skipped, so a stopped run resumes.

Concurrent lab servers (java with sealrun-lab in its command line, the resmon definition) are
sampled once a second while each world runs. Recorded per world: at_launch (before the slot call),
at_boot (the first sample that sees a java started after launch), at_last_sample (last sample before
exit; the in-world save-all flush happens about 10 s before exit and is not seen directly), max_during.
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

import sq_plan

WT = Path("C:/Users/seal/Documents/GitHub/sealrun-wt")
LAB_LOG = Path.home() / "sealrun-lab" / "squares_run.log"
ROOT = Path(__file__).resolve().parents[2]


def log(msg):
    line = f"{datetime.now():%H:%M:%S} {msg}"
    print(line, flush=True)
    LAB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LAB_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def free_mb():
    r = subprocess.run([sys.executable, str(WT / "resmon.py"), "--free"], capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


def wait_ram():
    while True:
        f = free_mb()
        if f >= 2500:
            return f
        log(f"free {f} MB below 2500, wait 60 s")
        time.sleep(60)


LAB_DIR = str(Path.home() / "sealrun-lab").lower()


def lab_java():
    out = []
    for p in psutil.process_iter(["name", "create_time"]):
        try:
            if not (p.info["name"] or "").lower().startswith("java"):
                continue
            if p.cwd().lower().startswith(LAB_DIR):
                out.append(p.info["create_time"])
        except (psutil.Error, OSError):
            continue
    return out


def watch(proc, t_launch):
    n_launch = len(lab_java())
    samples, at_boot = [], None
    t0 = time.monotonic()
    while proc.poll() is None:
        starts = lab_java()
        n = len(starts)
        t = round(time.monotonic() - t0, 1)
        samples.append([t, n])
        if at_boot is None and any(c >= t_launch for c in starts):
            at_boot = n
        time.sleep(1)
    starts = lab_java()
    samples.append([round(time.monotonic() - t0, 1), len(starts)])
    return {
        "at_launch": n_launch,
        "at_boot": at_boot,
        "at_last_sample": samples[-1][1],
        "max_during": max(n for _, n in samples),
        "samples": samples,
    }


def run_world(s, window, w):
    out = sq_plan.RES / f"squares_s{s}_{w['label']}.json"
    if out.exists():
        log(f"s{s} {w['label']} exists, skip")
        return
    tickets = [f"{x},{z}" for x, z in w["tickets"]]
    cmd = [sys.executable, str(WT / "slot.py"), sys.executable, "lab/research/ticket_world.py",
           str(out), window, *tickets, "--skip-far"]
    for attempt in (1, 2):
        free = wait_ram()
        log(f"s{s} {w['label']} attempt {attempt} start, free {free} MB")
        t_launch = time.time()
        proc = subprocess.Popen(cmd, cwd=str(ROOT))
        counts = watch(proc, t_launch)
        rc = proc.returncode
        if rc == 0 and out.exists():
            break
        log(f"s{s} {w['label']} attempt {attempt} failed rc={rc}")
        out.unlink(missing_ok=True)
    else:
        raise SystemExit(f"s{s} {w['label']} failed twice; stopped")
    d = json.loads(out.read_text(encoding="utf-8"))
    d.update({
        "spacing": s,
        "label": w["label"],
        "order_named": w["order"],
        "pre_registered": "lab/results/research/squares_s%d.json predictions block" % s,
        "lab_servers": counts,
    })
    out.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    log(f"s{s} {w['label']} done boot {d['boot_secs']} s settle {d['settle_s']} s "
        f"servers launch {counts['at_launch']} boot {counts['at_boot']} last {counts['at_last_sample']} max {counts['max_during']}")


def main():
    s = int(sys.argv[1])
    sq_plan.write_predictions(s, amend=True)
    plan = sq_plan.plan(s)
    for w in plan["worlds"]:
        run_world(s, plan["window"], w)
    log(f"s{s} all worlds done")


if __name__ == "__main__":
    main()
