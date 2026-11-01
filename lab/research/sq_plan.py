"""Layouts, build orders and pre-registered predictions for the squares lane (round 3, n3).

python lab/research/sq_plan.py <s> [--write]

Tickets A=(64,64), B=(64+s,64), C=(64,64+s), D=(64+s,64+s); an order is a string of letters.
The window is the rectangle around the tickets; ticket_world.py runs with --skip-far so only
chunks within Chebyshev 2 of some ticket are built and read.
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
CONTROL = "ABCD_rep"

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
    worlds = []
    for label in orders(s):
        worlds.append({"label": label, "order": label, "tickets": [list(t[c]) for c in label]})
    worlds.append({"label": CONTROL, "order": "ABCD", "tickets": [list(t[c]) for c in "ABCD"]})
    return {"spacing": s, "window": window(s), "worlds": worlds}


def predictions(s):
    n_orders = 24 if s == 3 else len(NAMED)
    return {
        "status": "pre-registered before any compute",
        "spacing": s,
        "tickets": {k: list(v) for k, v in tickets(s).items()},
        "window": window(s),
        "window_rule": "every chunk within Chebyshev 2 of some ticket (ticket_world --skip-far)",
        "orders_run": n_orders,
        "repeat_control": CONTROL,
        "predictions": {
            "cameron_8a3707c": {
                "file": "site/charts/r3/cameron.json",
                "rule": "each chunk stamped by the first ticket in the order that reaches it within 3 chunks",
                "classes_expected": CAMERON[s],
                "scope": "over all 24 orders",
                "note": "the run covers 6 named orders plus the repeat when s is 5 or 7" if s != 3 else "all 24 orders plus repeat",
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
        "named_orders_s5_s7": NAMED + [CONTROL] if s != 3 else None,
        "count_note": "the s=5 and s=7 list in the brief names 7 worlds (6 distinct orders plus the repeat); "
                      "identity ABCD is rotation 0, so it is not counted twice",
    }


def write_predictions(s):
    RES.mkdir(parents=True, exist_ok=True)
    path = RES / f"squares_s{s}.json"
    path.write_text(json.dumps({"spacing": s, "predictions": predictions(s)}, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    s = int(sys.argv[1])
    if "--write" in sys.argv:
        print(write_predictions(s))
    else:
        print(json.dumps(plan(s), indent=2))
