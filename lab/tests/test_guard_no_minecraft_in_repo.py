import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
DESTINATIONS = ("server-1.16.1", "lab/scratch")
PROBES = ["crates/world/src/new.rs", "crates/topo/src/new.rs", "Cargo.lock", "lab/new.py"]


def server_files(server: Path) -> list[str]:
    found = []
    for folder, _, names in os.walk(server):
        for name in names:
            found.append(Path(folder, name).relative_to(server).as_posix())
    return sorted(found)


def ignore_verdict(paths: list[str]) -> dict[str, bool]:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin", "-v", "-n"],
        input=("\n".join(paths) + "\n").encode(),
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.decode())
    verdict = {}
    for line in result.stdout.decode().splitlines():
        source, path = line.split("\t", 1)
        verdict[path] = source != "::" and not source.split(":", 2)[2].startswith("!")
    return verdict


class Lab(unittest.TestCase):
    def test_guard_no_minecraft_in_repo(self):
        self.assertTrue(SERVER.is_dir(), f"server folder missing: {SERVER}")
        candidates = [f"{dest}/{rel}" for dest in DESTINATIONS for rel in server_files(SERVER)]
        verdict = ignore_verdict(candidates)
        problems = []
        leaked = [path for path in candidates if not verdict.get(path)]
        if leaked:
            problems.append("server files not ignored: " + ", ".join(leaked))
        tracked = subprocess.run(
            ["git", "ls-files", "-ci", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        ).stdout.split()
        if tracked:
            problems.append("tracked files ignored: " + ", ".join(tracked))
        probes = ignore_verdict(PROBES)
        blocked = [path for path in PROBES if probes.get(path)]
        if blocked:
            problems.append("repo files wrongly ignored: " + ", ".join(blocked))
        self.assertFalse(problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
