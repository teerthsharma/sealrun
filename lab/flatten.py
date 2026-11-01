TILES = {"air": 0, "stone": 1, "water": 2, "tree": 3, "iron": 4, "goal": 5}
PASS = frozenset(
    "minecraft:" + n
    for n in (
        "air", "cave_air", "void_air", "grass", "tall_grass", "fern", "large_fern", "snow",
        "seagrass", "tall_seagrass", "kelp", "kelp_plant", "flowers", "sugar_cane", "dead_bush",
    )
)


def _ground(blocks):
    top = {}
    for (x, y, z), name in blocks.items():
        top.setdefault((x, z), None)
        if name is None or name in PASS or name.endswith("_leaves"):
            continue
        if top[(x, z)] is None or y > top[(x, z)][0]:
            top[(x, z)] = (y, name)
    for (x, z), g in top.items():
        if g is None:
            raise ValueError(f"no ground block at ({x}, {z})")
    return top


def _tile(blocks, ground, x, z):
    y, name = ground[(x, z)]
    if name.endswith("_log"):
        return TILES["tree"]
    if name == "minecraft:water":
        return TILES["water"]
    if any(blocks.get((x, yy, z)) == "minecraft:iron_ore" for yy in range(y - 6, y + 1)):
        return TILES["iron"]
    for nx, nz in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
        if (nx, nz) in ground and abs(ground[(nx, nz)][0] - y) >= 2:
            return TILES["stone"]
    return TILES["air"]


def grid(blocks, x0, z0, w, h):
    ground = _ground(blocks)
    return [[_tile(blocks, ground, x, z) for x in range(x0, x0 + w)] for z in range(z0, z0 + h)]
