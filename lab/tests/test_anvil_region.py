import gzip
import os
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anvil

SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
PAY_A = b"\x0a\x00\x00alpha"
PAY_B = b"\x0a\x00\x04beta"


def chunk_blob(comp, payload):
    data = zlib.compress(payload) if comp == 2 else gzip.compress(payload)
    blob = (len(data) + 1).to_bytes(4, "big") + bytes([comp]) + data
    return blob + b"\0" * (-len(blob) % 4096)


def write_region(path, entries):
    header = bytearray(8192)
    body = bytearray()
    sector = 2
    for lx, lz, comp, payload in entries:
        blob = chunk_blob(comp, payload)
        n = len(blob) // 4096
        i = lx + 32 * lz
        header[4 * i:4 * i + 4] = sector.to_bytes(3, "big") + bytes([n])
        body += blob
        sector += n
    path.write_bytes(bytes(header) + bytes(body))


class Lab(unittest.TestCase):
    def region_lists_present_chunks_and_inflates_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "r.0.0.mca"
            write_region(f, [(0, 0, 2, PAY_A), (5, 31, 1, PAY_B)])
            self.assertEqual(anvil.present(f), [(0, 0), (5, 31)])
            self.assertEqual(anvil.chunk_data(f, 0, 0), PAY_A)
            self.assertEqual(anvil.chunk_data(f, 5, 31), PAY_B)
            self.assertIsNone(anvil.chunk_data(f, 1, 0))

        region = SERVER / "world" / "region"
        files = sorted(region.glob("r.*.mca"))
        self.assertTrue(files, f"no region files in {region}")
        self.assertTrue(any(f.stat().st_size for f in files), "every region file is empty")
        for f in files:
            with self.subTest(file=f.name):
                cs = anvil.present(f)
                if f.stat().st_size == 0:
                    self.assertEqual(cs, [])
                    continue
                self.assertTrue(cs)
                data = anvil.chunk_data(f, *cs[0])
                self.assertIsNotNone(data)
                self.assertEqual(data[0], 10)


if __name__ == "__main__":
    unittest.main()
