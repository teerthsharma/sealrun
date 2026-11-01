"""Merge the house graph snapshot (tree.json) with the fellows' plain-English copy into goals.json.

    python site/build_goals.py                 # rebuild
    python site/build_goals.py G6.1=reached    # set statuses, then rebuild
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
CHARTS = HERE / "charts"


def load(name, default):
    p = CHARTS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def main(argv):
    tree = json.loads((HERE / "tree.json").read_text(encoding="utf-8"))
    for arg in argv:
        gid, status = arg.split("=", 1)
        tree["status"][gid] = status
    (HERE / "tree.json").write_text(json.dumps(tree, indent=1), encoding="utf-8")

    copy = {}
    for f in ("foreman.json", "chase.json", "cameron.json"):
        for c in load(f, []):
            copy[c["id"]] = c
    depts = load("departments.json", {"departments": []})["departments"]
    dept_of = {g: d["name"] for d in depts for g in d.get("goals", [])}

    def goal(gid, parent, leaf, fellow, test, status):
        c = copy.get(gid, {})
        top = gid.split(".")[0]
        return {"id": gid, "parent": parent, "leaf": leaf, "fellow": fellow, "test": test,
                "status": status, "department": dept_of.get(top),
                "title": c.get("title", gid), "plain": c.get("plain", ""),
                "why": c.get("why", ""), "done_when": c.get("done_when", "")}

    goals = [goal(*g, tree["status"].get(g[0], "pending")) for g in tree["goals"]]
    alternatives = [dict(goal(a, None, True, f, None, "retired"), alt_of=t) for a, t, f in tree["retired"]]
    out = {"need": "G0", "goals": goals, "alternatives": alternatives,
           "theory": load("theory.json", []), "facts": load("wilson.json", []),
           "departments": depts}
    (HERE / "goals.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    missing = [g["id"] for g in goals if not g["plain"]]
    print(f"goals.json: {len(goals)} goals, {len(alternatives)} alternatives, no copy for {missing or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1:])
