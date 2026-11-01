"""Merge the round 2 fellow cards with each goal's status into site/r2.json.

    python site/build_r2.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
CHARTS = HERE / "charts" / "r2"
FELLOWS = ("foreman", "chase", "cameron")
ROUTE = {"played": False, "note": "planned on a map, not yet played in the real game"}


def department(gid, depts):
    for d in depts:
        if gid in d.get("goals", []):
            return d["name"]
    gk = gid.split(".")[1:2]
    for d in depts:
        if any(g.split(".")[1:2] == gk for g in d.get("goals", [])):
            return d["name"]
    return None


def build(charts_dir, status):
    depts = json.loads((charts_dir / "departments.json").read_text(encoding="utf-8"))["departments"]
    goals = {}
    for fellow in FELLOWS:
        for card in json.loads((charts_dir / f"{fellow}.json").read_text(encoding="utf-8")):
            g = goals.setdefault(card["id"], {"id": card["id"], "fellows": []})
            g["fellows"].append(fellow)
            for k, v in card.items():
                g.setdefault(k, v)
    for gid, g in goals.items():
        g["status"] = status.get(gid, "pending")
        g["department"] = department(gid, depts)
    return {"route": ROUTE, "goals": list(goals.values())}


def main():
    status_path = HERE / "r2_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    out = build(CHARTS, status)
    (HERE / "r2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"r2.json: {len(out['goals'])} goals, status {'from r2_status.json' if status_path.exists() else 'file missing, all pending'}")


if __name__ == "__main__":
    main()
