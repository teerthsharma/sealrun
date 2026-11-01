import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = {"server.jar", "level.dat", "server.properties", "eula.txt"}
SUFFIXES = (".mca", ".mcr", ".jar")
SKIP = {".git", "target"}
IGNORES = ["server.jar", "level.dat", "server.properties", "eula.txt", "*.mca", "*.mcr", "*.jar"]


def offenders(root: Path) -> list[str]:
    found = []
    stack = [root]
    while stack:
        folder = stack.pop()
        for entry in folder.iterdir():
            rel = entry.relative_to(root).as_posix()
            if entry.is_dir() and not entry.is_symlink():
                if entry.name in SKIP:
                    continue
                stack.append(entry)
            elif entry.name in NAMES or entry.name.endswith(SUFFIXES):
                found.append(rel)
    return sorted(found)


def missing_ignores(gitignore: Path) -> list[str]:
    lines = {line.strip() for line in gitignore.read_text().splitlines()} if gitignore.exists() else set()
    return [pattern for pattern in IGNORES if pattern not in lines]


class Lab(unittest.TestCase):
    def no_minecraft_file_inside_repo(self):
        problems = []
        found = offenders(ROOT)
        if found:
            problems.append("server files inside repo: " + ", ".join(found))
        missing = missing_ignores(ROOT / ".gitignore")
        if missing:
            problems.append(".gitignore lacks: " + ", ".join(missing))
        self.assertFalse(problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
