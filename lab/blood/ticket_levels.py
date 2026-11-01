# SOURCE: https://minecraft.wiki/w/Chunk "created individually at load level 31"
LEVEL_FORCELOAD = 31
FULL_MAX_LEVEL = 33


def level(distance):
    return LEVEL_FORCELOAD + distance


def is_full(lvl):
    return lvl <= FULL_MAX_LEVEL


def full_tile(ticket=(0, 0), reach=6):
    tx, tz = ticket
    return {
        (tx + dx, tz + dz)
        for dx in range(-reach, reach + 1)
        for dz in range(-reach, reach + 1)
        if is_full(level(max(abs(dx), abs(dz))))
    }
