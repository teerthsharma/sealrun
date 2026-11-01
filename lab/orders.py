import itertools
import json
from pathlib import Path

SQUARES = [(64, 64), (-64, 64), (64, -64)]
OUT = Path(__file__).resolve().parent / "results" / "order_squares_more.json"


def square(cx, cz):
    return [(cx, cz), (cx + 1, cz), (cx, cz + 1), (cx + 1, cz + 1)]


def square_orders(cx, cz):
    return list(itertools.permutations(square(cx, cz)))


def table():
    rows = []
    for cx, cz in SQUARES:
        for order in square_orders(cx, cz):
            rows.append({
                "square": [cx, cz],
                "order": [list(p) for p in order],
                "status": "not run",
                "differing_blocks": None,
                "diamonds": None,
            })
    return {"squares": [list(s) for s in SQUARES], "rows": rows}


if __name__ == "__main__":
    OUT.write_text(json.dumps(table(), indent=2) + "\n")
