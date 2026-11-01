import json
from pathlib import Path

NAMES = (
    "order_control.json", "order_pair.json", "order_square.json", "order_edit.json",
    "aim.json", "aim_replay.json", "aim_heldout.json", "verdict_goal1.json",
    "race_seed7.json", "race_starts_seed7.json", "fractal_seed7.json",
)


def numbers(results_dir: Path) -> dict[str, dict | str]:
    out = {}
    for name in NAMES:
        path = results_dir / name
        out[name] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else "not run"
    return out
