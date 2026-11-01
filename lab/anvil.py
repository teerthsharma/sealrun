import gzip
import zlib
from pathlib import Path

import nbt


def present(region_path):
    with open(region_path, "rb") as f:
        table = f.read(4096)
    cells = []
    for i in range(1024):
        if int.from_bytes(table[4 * i:4 * i + 3], "big"):
            cells.append((i % 32, i // 32))
    return sorted(cells)


def chunk_data(region_path, lx, lz):
    with open(region_path, "rb") as f:
        f.seek(4 * (lx + 32 * lz))
        offset = int.from_bytes(f.read(3), "big")
        if not offset:
            return None
        f.seek(offset * 4096)
        length = int.from_bytes(f.read(4), "big")
        comp = f.read(1)[0]
        raw = f.read(length - 1)
    if comp == 1:
        return gzip.decompress(raw)
    if comp == 2:
        return zlib.decompress(raw)
    if comp == 3:
        return raw
    raise ValueError(f"unknown compression {comp}")


def section_blocks(palette, states):
    bits = max(4, (len(palette) - 1).bit_length())
    per = 64 // bits
    mask = (1 << bits) - 1
    return [
        palette[((states[i // per] & 0xFFFFFFFFFFFFFFFF) >> ((i % per) * bits)) & mask]
        for i in range(4096)
    ]


def _level(region_dir, cx, cz):
    path = Path(region_dir) / f"r.{cx >> 5}.{cz >> 5}.mca"
    if not path.is_file():
        return None
    data = chunk_data(path, cx & 31, cz & 31)
    return None if data is None else nbt.read(data)[1]["Level"]


def chunk_status(region_dir, cx, cz):
    level = _level(region_dir, cx, cz)
    return None if level is None else level.get("Status")


def block_at(region_dir, x, y, z):
    level = _level(region_dir, x >> 4, z >> 4)
    if level is None or level.get("Status") != "full":
        return None
    for section in level.get("Sections", []):
        if section["Y"] == y >> 4 and "Palette" in section:
            names = [p["Name"] for p in section["Palette"]]
            return section_blocks(names, section["BlockStates"])[(y & 15) * 256 + (z & 15) * 16 + (x & 15)]
    return "minecraft:air"
