import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_RESULT_BYTES = 2 * 1024 * 1024
WORLD_PARTS = {"region", "playerdata", "poi", "DIM-1", "DIM1", "advancements", "stats", "datapacks"}


def reason(path, root):
    p = Path(path)
    if p.suffix in (".mca", ".mcr"):
        return "region file"
    if p.name in ("level.dat", "level.dat_old"):
        return "level.dat"
    if p.suffix == ".jar":
        return "server jar"
    if p.name == "session.lock" or WORLD_PARTS & set(p.parts):
        return "world folder file"
    if p.parts[:2] == ("lab", "results") and (root / p).is_file() and (root / p).stat().st_size > MAX_RESULT_BYTES:
        return "result file over 2 MB"
    return None


def violations(root):
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    found = []
    for path in listed:
        why = reason(path, root)
        if why:
            found.append((path, why))
    return found


class Lab(unittest.TestCase):
    def test_violations_flag_each_kind_and_skip_ignored_and_harmless(self):
        expected = {
            "r.0.0.mca": "region file",
            "level.dat": "level.dat",
            "server.jar": "server jar",
            "world/playerdata/x.dat": "world folder file",
            "world/session.lock": "world folder file",
            "lab/results/big.json": "result file over 2 MB",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for rel in expected:
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_bytes(b"x")
            (root / "lab/results/big.json").write_bytes(b"0" * (MAX_RESULT_BYTES + 1))
            (root / "README.txt").write_text("harmless\n")
            (root / "secret.jar").write_bytes(b"x")
            (root / ".gitignore").write_text("secret.jar\n")
            self.assertEqual(sorted(violations(root)), sorted(expected.items()))

    def test_real_repo_has_no_minecraft_files(self):
        found = violations(ROOT)
        self.assertEqual(found, [], "\n".join(f"{p}: {why}" for p, why in found))


if __name__ == "__main__":
    unittest.main()
