"""Round 3 page numbers read from result files; a missing file or entry is "not run", never 0."""
import json
from pathlib import Path

NOT_RUN = "not run"
LAYOUTS = ["E0", "E1", "E2", "E3", "E4"]
R_DECS = [2, 3]
EXPERIMENTS = ["E1", "E2", "cal_square_O12", "round2_order_square", "round2_order_collapse", "round2_order_pair"]
LEVELS = [10000, 100000, 1000000]
ARMS = ["plan", "bfs"]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def numbers(results_dir):
    folder = Path(results_dir)
    quotient = _load(folder / "quotient_predictions.json") or {}
    partitions = _load(folder / "partitions.json") or {}
    race = _load(folder / "race_realmodel.json") or {}

    predicted = {(r["layout"], r["r_dec"]): r["predicted_classes"] for r in quotient.get("records", [])}
    classes = {run["experiment"]: run["n_classes"] for run in partitions.get("runs", [])}
    routed = {(row["level"], arm): row[arm]["routed"] for row in race.get("summary", []) for arm in ARMS}

    out = {}
    for layout in LAYOUTS:
        for r_dec in R_DECS:
            out[f"quotient/{layout}/r{r_dec}/predicted_classes"] = predicted.get((layout, r_dec), NOT_RUN)
    for exp in EXPERIMENTS:
        out[f"partitions/{exp}/n_classes"] = classes.get(exp, NOT_RUN)
    for level in LEVELS:
        for arm in ARMS:
            out[f"race/{arm}/{level}/routed"] = routed.get((level, arm), NOT_RUN)
    return out
