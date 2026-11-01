import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _string(s):
    b = s.encode()
    return struct.pack(">H", len(b)) + b


def _named(name, tid, payload):
    return bytes([tid]) + _string(name) + payload


def _compound(*entries):
    return b"".join(entries) + b"\x00"


def _list(tid, items):
    return bytes([tid]) + struct.pack(">i", len(items)) + b"".join(items)


def _chunk_nbt(cx, cz, status):
    palette = _list(10, [
        _compound(_named("Name", 8, _string("minecraft:air"))),
        _compound(_named("Name", 8, _string("minecraft:stone"))),
    ])
    section = _compound(
        _named("Y", 1, struct.pack(">b", 0)),
        _named("Palette", 9, palette),
        _named("BlockStates", 12, struct.pack(">i", 256) + struct.pack(">256q", *[0x1111111111111111] * 256)),
    )
    level = _compound(
        _named("xPos", 3, struct.pack(">i", cx)),
        _named("zPos", 3, struct.pack(">i", cz)),
        _named("Status", 8, _string(status)),
        _named("Sections", 9, _list(10, [section])),
    )
    return _named("", 10, _compound(
        _named("DataVersion", 3, struct.pack(">i", 2567)),
        _named("Level", 10, level),
    ))


def _region(chunks):
    header = bytearray(8192)
    body = bytearray()
    sector = 2
    for (lx, lz), nbt in sorted(chunks.items()):
        comp = zlib.compress(nbt)
        blob = struct.pack(">I", len(comp) + 1) + bytes([2]) + comp
        count = -(-len(blob) // 4096)
        blob += b"\x00" * (count * 4096 - len(blob))
        i = lx + 32 * lz
        header[4 * i:4 * i + 4] = sector.to_bytes(3, "big") + bytes([count])
        body += blob
        sector += count
    return bytes(header) + bytes(body)


class Lab(unittest.TestCase):
    def test_guard_chunk_status_full(self):
        import anvil

        with tempfile.TemporaryDirectory() as tmp:
            region_dir = Path(tmp)
            (region_dir / "r.0.0.mca").write_bytes(_region({
                (0, 0): _chunk_nbt(0, 0, "full"),
                (1, 0): _chunk_nbt(1, 0, "features"),
            }))
            self.assertEqual(anvil.chunk_status(region_dir, 0, 0), "full")
            self.assertEqual(anvil.block_at(region_dir, 0, 0, 0), "minecraft:stone")
            self.assertEqual(anvil.chunk_status(region_dir, 1, 0), "features")
            self.assertIsNone(anvil.block_at(region_dir, 16, 0, 0))
            self.assertIsNone(anvil.chunk_status(region_dir, 2, 0))
            self.assertIsNone(anvil.block_at(region_dir, 32, 0, 0))


if __name__ == "__main__":
    unittest.main()
