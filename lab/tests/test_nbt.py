import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nbt


def text(value):
    raw = value.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def header(tag, name):
    return bytes([tag]) + text(name)


class Lab(unittest.TestCase):
    def nbt_reads_compound_list_and_long_array(self):
        data = (
            header(10, "")
            + header(8, "Status") + text("full")
            + header(1, "Y") + struct.pack(">b", -1)
            + header(9, "Nodes") + bytes([10]) + struct.pack(">i", 2)
            + header(8, "Name") + text("minecraft:stone") + b"\x00"
            + header(8, "Name") + text("minecraft:air") + b"\x00"
            + header(12, "BlockStates") + struct.pack(">i", 3)
            + struct.pack(">qqq", 1, -1, 2**62)
            + header(9, "Empty") + bytes([0]) + struct.pack(">i", 0)
            + b"\x00"
        )
        root, value = nbt.read(data)
        self.assertEqual(root, "")
        self.assertEqual(
            value,
            {
                "Status": "full",
                "Y": -1,
                "Nodes": [{"Name": "minecraft:stone"}, {"Name": "minecraft:air"}],
                "BlockStates": [1, -1, 2**62],
                "Empty": [],
            },
        )

    def test_nbt_rejects_truncated_buffer(self):
        data = header(10, "") + header(8, "Status") + text("full") + b"\x00"
        with self.assertRaises(ValueError):
            nbt.read(data[: len(data) // 2])

    def test_nbt_rejects_unknown_tag(self):
        data = header(10, "") + header(13, "x") + b"\x00"
        with self.assertRaises(ValueError):
            nbt.read(data)


if __name__ == "__main__":
    unittest.main()
