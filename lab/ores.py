ORES = ("diamond", "iron", "coal", "gold", "lapis", "redstone", "emerald")
_BY_BLOCK = {f"minecraft:{ore}_ore": ore for ore in ORES}


def tally(blocks):
    out = {}
    for (x, _, z), name in blocks.items():
        counts = out.setdefault((x >> 4, z >> 4), {ore: 0 for ore in ORES})
        ore = _BY_BLOCK.get(name)
        if ore:
            counts[ore] += 1
    return out
