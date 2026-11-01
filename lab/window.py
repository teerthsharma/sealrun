import hashlib

import anvil


def chunk_blocks(level):
    cx, cz = level["xPos"], level["zPos"]
    out = {}
    for section in level.get("Sections", []):
        if "Palette" not in section:
            continue
        names = [p["Name"] for p in section["Palette"]]
        y0 = section["Y"] * 16
        for i, name in enumerate(anvil.section_blocks(names, section["BlockStates"])):
            out[(cx * 16 + (i & 15), y0 + (i >> 8), cz * 16 + ((i >> 4) & 15))] = name
    return out


def box(region_dir, lo, hi):
    out = {}
    for cx in range(lo[0] >> 4, (hi[0] >> 4) + 1):
        for cz in range(lo[2] >> 4, (hi[2] >> 4) + 1):
            level = anvil._level(region_dir, cx, cz)
            full = level is not None and level.get("Status") == "full"
            blocks = chunk_blocks(level) if full else None
            for x in range(max(lo[0], cx * 16), min(hi[0], cx * 16 + 15) + 1):
                for z in range(max(lo[2], cz * 16), min(hi[2], cz * 16 + 15) + 1):
                    for y in range(lo[1], hi[1] + 1):
                        out[(x, y, z)] = None if blocks is None else blocks.get((x, y, z), "minecraft:air")
    return out


def fingerprint(blocks):
    h = hashlib.sha256()
    for pos, name in sorted(blocks.items()):
        h.update(f"{pos[0]} {pos[1]} {pos[2]} {name}\n".encode())
    return h.hexdigest()
