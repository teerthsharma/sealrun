import struct

from flatten import TILES


def to_bytes(rows):
    if not rows:
        raise ValueError("no rows")
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        raise ValueError("ragged rows")
    if any(v not in TILES.values() for r in rows for v in r):
        raise ValueError("tile outside TILES")
    return struct.pack("<II", w, len(rows)) + bytes(v for r in rows for v in r)


def write(path, rows):
    with open(path, "wb") as f:
        f.write(to_bytes(rows))
