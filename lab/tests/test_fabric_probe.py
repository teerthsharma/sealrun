import socket
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fabric_probe

JAVA = "runtime/jre-legacy/windows/jre-legacy/bin/java.exe"


def _build_full(root: Path) -> None:
    (root / "versions" / "1.16.1").mkdir(parents=True)
    (root / "versions" / "1.16.1" / "1.16.1.jar").write_bytes(b"stub")
    (root / "versions" / "fabric-loader-0.11.6-1.16.1").mkdir(parents=True)
    (root / "mods").mkdir()
    (root / "mods" / "a.jar").write_bytes(b"stub")
    (root / JAVA).parent.mkdir(parents=True)
    (root / JAVA).write_bytes(b"not a program")


def _snapshot(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size)
        for p in [root, *root.rglob("*")]
    }


class Lab(unittest.TestCase):
    def probe_lists_client_loader_mods_and_java_without_downloading(self):
        def refuse(*args, **kwargs):
            raise AssertionError("network use")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(socket, "socket", refuse), \
                mock.patch.object(urllib.request, "urlopen", refuse):
            full = Path(tmp) / "full"
            _build_full(full)
            before = _snapshot(full)
            got = fabric_probe.probe(full)
            self.assertEqual(_snapshot(full), before)
            self.assertEqual(got, {
                "client_1_16_1": {"present": True, "path": "versions/1.16.1/1.16.1.jar"},
                "fabric_loader": ["fabric-loader-0.11.6-1.16.1"],
                "mods": ["a.jar"],
                "java": [{"path": JAVA, "version": None}],
            })

            empty = Path(tmp) / "empty"
            empty.mkdir()
            self.assertEqual(fabric_probe.probe(empty), {
                "client_1_16_1": {"present": False, "path": "versions/1.16.1/1.16.1.jar"},
                "fabric_loader": [],
                "mods": [],
                "java": [],
            })


if __name__ == "__main__":
    unittest.main()
