import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import serverdir

PROPERTIES = (
    "enable-rcon=false\n"
    "rcon.port=25575\n"
    "rcon.password=\n"
    "server-port=25565\n"
    "level-seed=7\n"
    "view-distance=4\n"
)


def parse(text):
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def snapshot(folder):
    out = {}
    for dirpath, _, names in os.walk(folder):
        for name in names:
            p = Path(dirpath, name)
            out[str(p)] = (p.read_bytes(), p.stat().st_mtime_ns)
    return out


class Lab(unittest.TestCase):
    def scratch_copy_enables_rcon_and_leaves_original_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "source")
            root = Path(tmp, "scratch")
            (src / "world").mkdir(parents=True)
            root.mkdir()
            (src / "server.jar").write_bytes(b"FAKE-JAR")
            (src / "server.properties").write_text(PROPERTIES)
            (src / "eula.txt").write_text("eula=true\n")
            (src / "world" / "level.dat").write_bytes(b"FAKE-LEVEL")
            for p in src.rglob("*"):
                if p.is_file():
                    os.utime(p, ns=(1_000_000_000, 1_000_000_000))
            before = snapshot(src)

            first = serverdir.make_scratch(src, root)
            second = serverdir.make_scratch(src, root)

            for result in (first, second):
                d = Path(result["dir"])
                self.assertTrue(d.resolve().is_relative_to(root.resolve()))
                for name in ("server.jar", "server.properties", "eula.txt", serverdir.MARKER):
                    self.assertTrue((d / name).is_file(), name)
                self.assertFalse((d / "world").exists())
                props = parse((d / "server.properties").read_text())
                self.assertEqual(props["enable-rcon"], "true")
                self.assertEqual(int(props["rcon.port"]), result["rcon_port"])
                self.assertEqual(int(props["server-port"]), result["port"])
                self.assertNotEqual(result["port"], result["rcon_port"])
                self.assertTrue(result["rcon_password"])
                self.assertEqual(props["rcon.password"], result["rcon_password"])
                self.assertEqual(props["level-seed"], "7")
                self.assertEqual(props["view-distance"], "4")

            self.assertNotEqual(first["rcon_password"], second["rcon_password"])
            self.assertNotEqual(first["dir"], second["dir"])
            self.assertEqual(before, snapshot(src))


if __name__ == "__main__":
    unittest.main()
