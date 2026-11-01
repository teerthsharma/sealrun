import copy
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anvil
import nbt

SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
REGION = SERVER / "world" / "region" / "r.0.0.mca"


def _shift(values):
    return [v + 1 for v in values]


def _metadata_only(level):
    touched = copy.deepcopy(level)
    touched["LastUpdate"] = touched["LastUpdate"] + 1
    touched["InhabitedTime"] = touched["InhabitedTime"] + 1
    touched["Heightmaps"] = {k: _shift(v) for k, v in touched["Heightmaps"].items()}
    for section in touched["Sections"]:
        section["SkyLight"] = _shift(section.get("SkyLight", []))
        section["BlockLight"] = _shift(section.get("BlockLight", []))
    return touched


def _one_block_long(level):
    edited = copy.deepcopy(level)
    section = next(s for s in edited["Sections"] if len(s["Palette"]) > 1)
    palette_size = len(section["Palette"])
    bits = max(4, (palette_size - 1).bit_length())
    mask = (1 << bits) - 1
    states = section["BlockStates"]
    index = states[0] & mask
    states[0] = (states[0] & ~mask) | ((index + 1) % palette_size)
    return edited


class Lab(unittest.TestCase):
    def test_guard_diff_blocks_only(self):
        import window

        lx, lz = anvil.present(REGION)[0]
        _, root = nbt.read(anvil.chunk_data(REGION, lx, lz))
        level = root["Level"]

        touched = _metadata_only(level)
        self.assertNotEqual(touched, level)

        original_blocks = window.chunk_blocks(level)
        touched_blocks = window.chunk_blocks(touched)
        self.assertEqual(touched_blocks, original_blocks)
        self.assertEqual(
            window.fingerprint(touched_blocks),
            window.fingerprint(original_blocks),
        )

        control = _one_block_long(level)
        self.assertNotEqual(window.chunk_blocks(control), original_blocks)


if __name__ == "__main__":
    unittest.main()
