import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server
import serverdir


class Lab(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.root = self.base / "scratch"
        self.root.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def make_server(self, folder, marker=True):
        (folder / "world").mkdir(parents=True)
        (folder / "world" / "level.dat").write_bytes(b"level")
        (folder / "server.jar").write_bytes(b"jar")
        if marker:
            (folder / serverdir.MARKER).write_text("sealrun")
        return folder

    def assert_refused(self, folder, kept):
        with self.assertRaises(ValueError):
            server.delete_world(folder, self.root)
        self.assertTrue((kept / "world" / "level.dat").exists())

    def test_guard_reset_scope(self):
        with self.subTest("a: marked scratch folder inside root loses only world/"):
            s1 = self.make_server(self.root / "s1")
            server.delete_world(s1, self.root)
            self.assertFalse((s1 / "world").exists())
            self.assertTrue((s1 / serverdir.MARKER).exists())
            self.assertTrue((s1 / "server.jar").exists())

        with self.subTest("b: folder inside root without marker is refused"):
            s2 = self.make_server(self.root / "s2", marker=False)
            self.assert_refused(s2, s2)

        with self.subTest("c: marked folder outside root is refused"):
            outside = self.make_server(self.base / "outside")
            self.assert_refused(outside, outside)

        with self.subTest("d: escape path through root is refused"):
            self.make_server(self.root / "s4")
            outside = self.make_server(self.base / "outside_d")
            escape = self.root / "s4" / ".." / ".." / "outside_d"
            self.assert_refused(escape, outside)

        with self.subTest("e: decoy server folder outside root is refused"):
            decoy = self.make_server(self.base / "decoy", marker=False)
            (decoy / "server.properties").write_text("server-port=25565")
            self.assert_refused(decoy, decoy)


if __name__ == "__main__":
    unittest.main()
