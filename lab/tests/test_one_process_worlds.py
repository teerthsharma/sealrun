import ast
import json
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
            self.assertNotIn("not approved", got["reason"])
            self.assertIn("later leaf", got["reason"])
            self.assertIsNone(got["worlds_per_minute"])
            self.assertIsNone(got["mb_per_world"])

            mods_only = Path(tmp) / "mods_only"
            (mods_only / "mods").mkdir(parents=True)
            (mods_only / "mods" / "speedrunner.jar").write_bytes(b"stub")
            got = oneprocess_worlds.result(mods_only)
            self.assertEqual(got["status"], "blocked")
            self.assertIn("not approved", got["reason"])

            loader_only = Path(tmp) / "loader_only"
            (loader_only / "versions" / "fabric-loader-x").mkdir(parents=True)
            got = oneprocess_worlds.result(loader_only)
            self.assertEqual(got["status"], "blocked")
            self.assertIn("not approved", got["reason"])

        tree = ast.parse((LAB / "oneprocess_worlds.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(sorted(imported & set(NETWORK)), [], "oneprocess_worlds imports a network library")

        out = LAB / "results" / "worlds_one_process.json"
        self.assertTrue(out.is_file())
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "blocked")
        self.assertIsNone(saved["worlds_per_minute"])
        self.assertIsNone(saved["mb_per_world"])


if __name__ == "__main__":
    unittest.main()
