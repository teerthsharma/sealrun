import os
import re
import unittest
from pathlib import Path

SOURCES = Path(os.environ.get(
    "SOURCES_MD",
    Path(__file__).resolve().parents[1] / "results" / "research" / "sources.md",
))
END = "## Process notes"
ENTRY = re.compile(r"^\s*(- |\|)")
TABLE_SEP = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
URL = re.compile(r"https?://[^\s)\]]+")
FAMILIES = {
    "Minecraft wiki": ["minecraft.wiki"],
    "bug tracker": ["mojira", "bugs.mojang"],
    "trace monoids": ["trace monoid", "trace rewriting"],
    "acyclic orientations": ["acyclic orientation"],
    "left regular bands": ["left regular band", "left-regular band", "lrb"],
    "order-independent generation": ["order-independent", "order independen"],
}


def entries(lines):
    out = []
    for line in lines:
        if line.startswith(END):
            break
        if ENTRY.match(line) and not TABLE_SEP.match(line):
            out.append(line)
    return out


class Lab(unittest.TestCase):
    def sources_cover_all_six_families(self):
        body = entries(SOURCES.read_text(encoding="utf-8").splitlines())
        failing = []
        for family, keys in FAMILIES.items():
            named = [l for l in body if any(k in l.lower() for k in keys)]
            with_url = [l for l in named if URL.search(l)]
            print(f"{family}: {len(named)} entries, {len(with_url)} with http(s) URL")
            if not with_url:
                failing.append(family)
        self.assertFalse(failing, f"no entry with an http(s) URL for: {', '.join(failing)}")


if __name__ == "__main__":
    unittest.main()
