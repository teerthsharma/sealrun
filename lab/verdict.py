import json
from pathlib import Path

NEXT_ROUTE = "edit the border band before the neighbour is built (N2.G3.5)"
LEVER = {True: "order lever alive", False: "order lever dead", None: "order lever not run"}


def statements(paths):
    return [_statement(Path(p)) for p in paths]


def _statement(path):
    if not path.exists():
        return f"{path.name}: not run"
    doc = json.loads(path.read_text(encoding="utf-8"))
    rd = doc["control"]["repeat_diff"]
    s = f"{path.name}: seed {doc['seed']}, area {doc['area']}, height {doc['height']}, {doc['orders']} orders"
    if rd is None:
        s += ", noise floor not measured"
    else:
        s += ", shaky" if rd > 0 else ", repeat holds"
        s += ", " + LEVER[doc["lever"]]
    if doc["lever"] is False:
        s += "; next route: " + NEXT_ROUTE
    return s
