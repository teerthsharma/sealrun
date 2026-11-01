import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rcon


class Lab(unittest.TestCase):
    def rcon_packet_bytes_match_spec(self):
        self.assertEqual((rcon.LOGIN, rcon.COMMAND, rcon.RESPONSE), (3, 2, 0))
        self.assertEqual(
            rcon.encode(1, 3, "pw"),
            b"\x0c\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00pw\x00\x00",
        )
        self.assertEqual(
            rcon.encode(5, 2, ""),
            b"\x0a\x00\x00\x00\x05\x00\x00\x00\x02\x00\x00\x00\x00\x00",
        )
        self.assertEqual(rcon.decode(rcon.encode(5, 2, "")), (5, 2, "", b""))
        self.assertEqual(rcon.decode(rcon.encode(-1, 0, "x")), (-1, 0, "x", b""))
        first = rcon.encode(1, 3, "pw")
        second = rcon.encode(2, 2, "list")
        self.assertEqual(rcon.decode(first + second), (1, 3, "pw", second))
        self.assertEqual(rcon.decode(second), (2, 2, "list", b""))
        with self.assertRaises(ValueError):
            rcon.decode(first[:-1])
        with self.assertRaises(ValueError):
            rcon.decode(b"\x0c\x00")


if __name__ == "__main__":
    unittest.main()
