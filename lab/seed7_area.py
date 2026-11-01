import flatten
import gridfile
import spawn_area

HALF = 32
SIZE = 64


def rows(blocks, spawn):
    sx, sz = spawn
    return flatten.grid(blocks, sx - HALF, sz - HALF, SIZE, SIZE)


def write(blocks, spawn, path):
    gridfile.write(path, rows(blocks, spawn))


def capture(scratch, path):
    blocks, spawn = spawn_area.read(scratch, half=HALF)
    write(blocks, spawn, path)
    return spawn
