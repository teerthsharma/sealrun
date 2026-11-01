import gzip
from pathlib import Path

import nbt
import server
import window


def read(scratch, half=48):
    srv = server.boot(scratch)
    try:
        srv.command("save-all flush")
    finally:
        srv.stop()
    root = Path(scratch["dir"]) / "world"
    level = nbt.read(gzip.decompress((root / "level.dat").read_bytes()))[1]["Data"]
    spawn_x, spawn_z = level["SpawnX"], level["SpawnZ"]
    blocks = window.box(
        root / "region",
        (spawn_x - half, 0, spawn_z - half),
        (spawn_x + half, 255, spawn_z + half),
    )
    return blocks, (spawn_x, spawn_z)
