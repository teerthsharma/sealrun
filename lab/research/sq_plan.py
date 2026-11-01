"""Layouts, build orders and pre-registered predictions for the squares lane (round 3, n3).

python lab/research/sq_plan.py <s> [--write]

Tickets A=(64,64), B=(64+s,64), C=(64,64+s), D=(64+s,64+s); an order is a string of letters.
The window is the rectangle around the tickets; ticket_world.py runs with --skip-far so only
chunks within Chebyshev 2 of some ticket are built and read.
Two repeat controls per spacing (ABCD and DCBA, added as an amendment after the first commit):
the same order built again, so the noise between identical builds is measured.
"""
import json
import sys
from itertools import permutations
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
RES = LAB / "results" / "research"
BASE = 64
REACH = 2
NAMED = ["ABCD", "DCBA", "BCDA", "CDAB", "DABC", "ACBD"]
CONTROLS = {"ABCD_rep": "ABCD", "DCBA_rep": "DCBA"}

CAMERON = {1: 4, 2: 4, 3: 20, 4: 20, 5: 1, 6: 1, 7: 1}
CAMERON_SHA = "8a3707c4f395eb24e49d712a16c630a7f67ab1f0"
POLY_SHA = "b04b482"
POLY_HEAD = "43faa40d0b755458ebebd7dd1955e1b8baef298b"


def tickets(s):
    return {
        "A": (BASE, BASE),
        "B": (BASE + s, BASE),
        "C": (BASE, BASE + s),
        "D": (BASE + s, BASE + s),
    }


def window(s):
    lo, hi = BASE - REACH, BASE + s + REACH
    return f"{lo},{lo},{hi},{hi}"


def orders(s):
    if s == 3:
        return ["".join(p) for p in permutations("ABCD")]
    return NAMED


def plan(s):
    t = tickets(s)
    worlds = [{"label": o, "order": o, "tickets": [list(t[c]) for c in o]} for o in orders(s)]
    for label, o in CONTROLS.items():
        worlds.append({"label": label, "order": o, "tickets": [list(t[c]) for c in o]})
    return {"spacing": s, "window": window(s), "worlds": worlds}


def predictions(s):
    return {
        "status": "pre-registered before any compute",
        "spacing": s,
        "tickets": {k: list(v) for k, v in tickets(s).items()},
        "window": window(s),
        "window_rule": "every chunk within Chebyshev 2 of some ticket (ticket_world --skip-far)",
        "orders_run": 24 if s == 3 else len(NAMED),
        "repeat_controls": list(CONTROLS),
        "predictions": {
            "cameron_8a3707c": {
                "file": "site/charts/r3/cameron.json",
                "rule": "each chunk stamped by the first ticket in the order that reaches it within 3 chunks",
                "classes_expected": CAMERON[s],
                "scope": "over all 24 orders; the s=5 and s=7 run covers 6 named orders",
            },
            "polytope_research_polytope": {
                "file": "lab/results/research/quotient_polytope.json",
                "head_sha": POLY_HEAD,
                "file_last_commit": POLY_SHA,
                "square_rows_at_spacing_s": "absent: the file has E0_square (2x2 square, spacing 1) only, plus E2_E3_E4_squares with no hand prediction",
                "E0_square_F_classes": 4,
                "E0_square_F_prime_classes": 24,
            },
        },
    }


AMENDMENT = {
    "date": "2026-11-01",
    "reason": "coordinator note: the same order can give different worlds (determinism.json on main: "
              "differing blocks 54, 40, 94 across its three pairs)",
    "changes": [
        "added repeat control DCBA_rep (order DCBA built twice) per spacing",
        "class counts computed on chunks where both repeat pairs agree; noisy chunks listed apart",
        "concurrent lab server count recorded at launch, boot, last sample and max, per world",
        "predictions block above is unchanged",
    ],
}


def write_predictions(s, amend=False):
    RES.mkdir(parents=True, exist_ok=True)
    path = RES / f"squares_s{s}.json"
    base = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"spacing": s}
    if "predictions" not in base:
        base["predictions"] = predictions(s)
    if amend and AMENDMENT not in base.get("amendments", []):
        base.setdefault("amendments", []).append(AMENDMENT)
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    s = int(sys.argv[1])
    if "--write" in sys.argv:
        print(write_predictions(s, amend="--amend" in sys.argv))
    else:
        print(json.dumps(plan(s), indent=2))
