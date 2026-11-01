import os
import re
import unittest
from pathlib import Path

SOURCES = Path(os.environ.get(
    "SOURCES_MD",
    Path(__file__).resolve().parents[1] / "results" / "research" / "sources.md",
))
HAND_HEADINGS = 7
END = "## Process notes"
ENTRY = re.compile(r"^\s*(- |\|)")
TABLE_SEP = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
URL = re.compile(r"https?://[^\s)\]]+")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# A query is written as search ("terms"), searched for "terms", search "terms", or query: terms.
QUERY = re.compile(r'(?i)\bsearch(es|ed)?\b\s*(for\s*|\(\s*)?"[^"\n]+"|\bquer(y|ies)\s*:')
QUOTE = re.compile(r'"([^"\n]*)"')


def entries(lines):
    out = []
    for i, line in enumerate(lines):
        if line.startswith(END):
            break
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if not ENTRY.match(line) or TABLE_SEP.match(line) or TABLE_SEP.match(nxt):
            continue
        out.append((i + 1, line))
    return out


def missing_parts(line):
    missing = []
    if not QUERY.search(line):
        missing.append("query")
    if not URL.search(line):
        missing.append("URL")
    prose = URL.sub(" ", LINK.sub(r"\1", line))
    if len(re.findall(r"[A-Za-z]{2,}", prose)) < 4:
        missing.append("finding")
    return missing


class Lab(unittest.TestCase):
    def sources_have_urls_and_queries(self):
        lines = SOURCES.read_text(encoding="utf-8").split("\n")
        ents = entries(lines)
        print(f"headings(hand)={HAND_HEADINGS} entries={len(ents)}")
        self.assertGreaterEqual(len(ents), HAND_HEADINGS,
                                "fewer entries than ### headings: the parser found too little")
        lacking = []
        for n, line in ents:
            miss = missing_parts(line)
            if miss:
                lacking.append(f"  line {n} lacks {'/'.join(miss)}: {line.strip()[:100]}")
        long_quotes = []
        for n, line in enumerate(lines, 1):
            for q in QUOTE.findall(line):
                if len(q.split()) > 15:
                    long_quotes.append(f"  line {n} quote is {len(q.split())} words: {q[:100]}")
        problems = []
        if lacking:
            problems.append(f"{len(lacking)} entries lack a part:\n" + "\n".join(lacking))
        if long_quotes:
            problems.append(f"{len(long_quotes)} quotes over 15 words:\n" + "\n".join(long_quotes))
        if problems:
            self.fail("\n".join(problems))


if __name__ == "__main__":
    unittest.main()
