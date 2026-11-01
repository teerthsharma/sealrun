import os
import re
import unittest
from pathlib import Path

SOURCES = Path(os.environ.get(
    "SOURCES_MD",
    Path(__file__).resolve().parents[1] / "results" / "research" / "sources.md",
))
NEAR = re.compile(r"(?i)\b(closest|nearest)\b")
GAP = re.compile(r"\bGap:\s*(.*)")


class Lab(unittest.TestCase):
    def closest_prior_work_names_its_gap(self):
        lines = SOURCES.read_text(encoding="utf-8").split("\n")
        hits = [(n, line) for n, line in enumerate(lines, 1) if NEAR.search(line)]
        self.assertGreater(len(hits), 0, "no near hit: the file marks no closest prior work")
        named, lacking = [], []
        for n, line in hits:
            m = GAP.search(line)
            if m and len(re.findall(r"[A-Za-z]{2,}", m.group(1))) >= 4:
                named.append(n)
            else:
                lacking.append(f"  line {n} has no one-line Gap: statement: {line.strip()[:100]}")
        print(f"near_hits={len(hits)} named_gap={len(named)}")
        if lacking:
            self.fail(f"{len(lacking)} near hits lack a gap line:\n" + "\n".join(lacking))


if __name__ == "__main__":
    unittest.main()
