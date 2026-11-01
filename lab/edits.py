def commands(edits, loaded):
    out = []
    for op, x, y, z, block in edits:
        cell = (x >> 4, z >> 4)
        if cell not in loaded:
            raise ValueError(f"chunk {cell} is not loaded")
        name = "minecraft:air" if op == "break" else block
        out.append(f"setblock {x} {y} {z} {name}")
    return out
