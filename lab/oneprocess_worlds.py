import json
from pathlib import Path

import fabric_probe

OUT = Path(__file__).resolve().parent / "results" / "worlds_one_process.json"


def result(mc_dir: Path) -> dict:
    probe = fabric_probe.probe(mc_dir)
    loader, mods = probe["fabric_loader"], probe["mods"]
    status = "not run" if loader and mods else "blocked"
    return {
        "status": status,
        "reason": (
            "file list not approved by the owner (house/permissions-6h.md row 15); "
            f"fabric_loader: {loader}, mods: {mods}"
        ),
        "worlds_per_minute": None,
        "mb_per_world": None,
    }


if __name__ == "__main__":
    data = result(fabric_probe.REAL)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))
