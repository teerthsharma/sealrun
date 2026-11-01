import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anvil

SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
REGION = SERVER / "world" / "region"


class Lab(unittest.TestCase):
    def block_at_negative_coords_status_and_missing_chunk(self):
        self.assertEqual(anvil.block_at(REGION, 3, 0, 20), "minecraft:bedrock")
        self.assertEqual(anvil.chunk_status(REGION, 0, 1), "full")
        self.assertEqual(anvil.block_at(REGION, -1, 0, 16), "minecraft:bedrock")
        self.assertEqual(anvil.chunk_status(REGION, -1, 1), "full")
        self.assertEqual(anvil.block_at(REGION, -1, 1, 16), "minecraft:stone")
        self.assertIsNone(anvil.chunk_status(REGION, 0, 0))
        self.assertIsNone(anvil.block_at(REGION, 0, 0, 0))
        self.assertIsNone(anvil.chunk_status(REGION, -1, 0))
        self.assertIsNone(anvil.block_at(REGION, -1, 0, 0))
        self.assertIsNone(anvil.chunk_status(REGION, -200, 0))
        self.assertIsNone(anvil.block_at(REGION, -3200, 0, 0))
        self.assertIsNone(anvil.block_at(REGION, -1, 0, -1))


if __name__ == "__main__":
    unittest.main()
