import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import oneprocess_worlds

LAB = Path(__file__).resolve().parents[1]
NETWORK = ("urllib", "http", "socket", "requests")


class Lab(unittest.TestCase):
    def one_process_many_worlds_measured_or_blocked_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            got = oneprocess_worlds.result(empty)
            self.assertEqual(got["status"], "blocked")
            self.assertIn("not approved", got["reason"])
            self.assertIn("fabric_loader", got["reason"])
            self.assertIn("mods", got["reason"])
            self.assertIsNone(got["worlds_per_minute"])
            self.assertIsNone(got["mb_per_world"])

            staged = Path(tmp) / "staged"
            (staged / "versions" / "fabric-loader-x").mkdir(parents=True)
            (staged / "mods").mkdir()
            (staged / "mods" / "speedrunner.jar").write_bytes(b"stub")
            got = oneprocess_worlds.result(staged)
            self.assertEqual(got["status"], "not run")
            self.assertIsNone(got["worlds_per_minute"])
            self.assertIsNone(got["mb_per_world"])

        source = (LAB / "oneprocess_worlds.py").read_text(encoding="utf-8")
        for name in NETWORK:
            self.assertIsNone(
                re.search(rf"^\s*(import|from)\s+{name}\b", source, re.M),
                f"oneprocess_worlds imports {name}",
            )

        out = LAB / "results" / "worlds_one_process.json"
        self.assertTrue(out.is_file())
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "blocked")
        self.assertIsNone(saved["worlds_per_minute"])
        self.assertIsNone(saved["mb_per_world"])


if __name__ == "__main__":
    unittest.main()
