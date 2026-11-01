import collections
import math
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anvil
import nbt

SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
U64 = (1 << 64) - 1


def pack(indices, bits):
    per = 64 // bits
    longs = [0] * math.ceil(len(indices) / per)
    for i, value in enumerate(indices):
        longs[i // per] |= value << ((i % per) * bits)
    return [v - (1 << 64) if v >> 63 else v for v in longs]


def unpack(longs, bits):
    per = 64 // bits
    mask = (1 << bits) - 1
    return [((longs[i // per] & U64) >> ((i % per) * bits)) & mask for i in range(4096)]


def names(n):
    return [f"minecraft:block_{i}" for i in range(n)]


class Lab(unittest.TestCase):
    def padded_packing_5_and_6_bits_not_spanning(self):
        for n, bits in ((16, 4), (17, 5), (33, 6), (300, 9)):
            with self.subTest(palette=n):
                palette = names(n)
                idx = [(i * 37 + (i >> 4)) % n for i in range(4096)]
                states = pack(idx, bits)
                per = 64 // bits
                self.assertEqual(len(states), math.ceil(4096 / per))
                self.assertEqual(anvil.section_blocks(palette, states), [palette[i] for i in idx])

    def real_region_sections_match_padded_layout(self):
        region = SERVER / "world" / "region"
        largest = max(region.glob("r.*.mca"), key=lambda p: p.stat().st_size)
        self.assertGreater(largest.stat().st_size, 0)
        seen = collections.Counter()
        sections = 0
        for lx, lz in anvil.present(largest):
            _, root = nbt.read(anvil.chunk_data(largest, lx, lz))
            for sec in root["Level"].get("Sections", []):
                if "Palette" not in sec or "BlockStates" not in sec:
                    continue
                palette = [p["Name"] for p in sec["Palette"]]
                states = sec["BlockStates"]
                bits = max(4, (len(palette) - 1).bit_length())
                per = 64 // bits
                with self.subTest(chunk=(lx, lz), y=sec.get("Y")):
                    self.assertEqual(len(states), math.ceil(4096 / per))
                    indices = unpack(states, bits)
                    self.assertLess(max(indices), len(palette))
                    self.assertEqual(anvil.section_blocks(palette, states), [palette[i] for i in indices])
                seen[bits] += 1
                sections += 1
        self.assertGreater(sections, 0)
        print(f"\nreal sections checked={sections} bit widths={dict(sorted(seen.items()))}", file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
