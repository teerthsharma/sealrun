import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "lab"))
sys.path.insert(0, str(REPO / "lab" / "tests"))

import server  # noqa: E402
import serverdir  # noqa: E402

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
ROOT = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
RAW = Path(os.environ.get(
    "DET_RAW",
    "C:/Users/seal/AppData/Local/Temp/claude/C--Users-seal-Documents-GitHub-sealrun/f708d1ce-97b8-4985-b4ab-75b219fa060b/scratchpad/det",
))
TILE = [(cx, cz) for cx in range(62, 67) for cz in range(62, 67)]


def wait_ram(need: int = 1500) -> None:
    while server.free_mb() < need:
        print(f"free RAM {server.free_mb()} MB below {need}, waiting 60 s", flush=True)
        time.sleep(60)


def fresh_scratch() -> dict:
    ROOT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    wait_ram()
    return serverdir.make_scratch(SRC, ROOT)


def gametime(srv) -> dict:
    reply = srv.command("time query gametime")
    nums = re.findall(r"\d+", reply)
    return {"reply": reply, "ticks": int(nums[-1]) if nums else None}
