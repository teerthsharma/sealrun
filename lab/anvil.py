import gzip
import zlib


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
