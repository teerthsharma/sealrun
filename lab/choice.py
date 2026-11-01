import json
from datetime import datetime
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def per_gb(run):
    return run["worlds_per_minute"] / (run["peak_mb_total"] / 1024)


def pick(vanilla_runs, other):
    best = max(vanilla_runs, key=per_gb)
    vanilla = {"route": "vanilla", "worlds_per_minute_per_gb": per_gb(best), "vanilla_best_n": best["n"]}
    if other is None:
        return {**vanilla, "why": "missing"}
    if "blocked" in other:
        return {**vanilla, "why": other["blocked"]}
    if per_gb(other) > per_gb(best):
        return {"route": "in_process", "worlds_per_minute_per_gb": per_gb(other), "vanilla_best_n": best["n"],
                "why": "in_process has more worlds per GB"}
    return {**vanilla, "why": "in_process not more worlds per GB"}


def main():
    runs = json.loads((RESULTS / "worlds_vanilla.json").read_text())["runs"]
    out = pick(runs, {"route": "in_process", "blocked": "Fabric/mod download needs the owner's approval of the file list (permissions ledger row 15)"})
    out["when"] = datetime.now().astimezone().isoformat(timespec="seconds")
    (RESULTS / "world_route.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
