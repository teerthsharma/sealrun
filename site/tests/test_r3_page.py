import html.parser
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE))

import build_r3

CHARTS = SITE / "charts" / "r3"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Cards(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.cards = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if "data-goal" in a:
            self.cards.append({"id": a["data-goal"], "classes": a.get("class", "").split(), "text": []})
            self.stack.append((tag, len(self.cards) - 1))
        else:
            self.stack.append((tag, None))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        for _, idx in self.stack:
            if idx is not None:
                self.cards[idx]["text"].append(data)


def norm(s):
    return " ".join(s.split())


def extract_render(source):
    blocks = re.findall(r"<script>(.*?)</script>", source, re.S)
    found = [b for b in blocks if "function renderCards(" in b]
    if len(found) != 1:
        raise AssertionError(f"r3.html needs one inline script defining renderCards, found {len(found)}")
    return found[0]


def render(script_src, data):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        data_path = tmp / "r3.json"
        data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        wrapper = tmp / "render.cjs"
        wrapper.write_text(
            script_src
            + "\nprocess.stdout.write(renderCards(JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'))));\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(wrapper), str(data_path)],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    if proc.returncode != 0:
        raise AssertionError(f"node render failed: {proc.stderr.strip()}")
    parsed = Cards()
    parsed.feed(proc.stdout)
    parsed.close()
    return parsed.cards


class Lab(unittest.TestCase):
    def r3_page_renders_cards(self):
        page = SITE / "r3.html"
        self.assertTrue(page.is_file(), f"missing {page}")
        source = page.read_text(encoding="utf-8")
        self.assertTrue('fetch("r3.json")' in source or "fetch('r3.json')" in source,
                        "r3.html does not fetch r3.json")
        script = extract_render(source)

        with tempfile.TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            status.write_text(json.dumps({"N3.G1": "reached", "N3.C1": "active", "N3.G2": "blocked"}),
                              encoding="utf-8")
            data = build_r3.build(CHARTS, status)

        self.assertTrue(data, "build_r3 returned no cards")
        cards = render(script, data)
        self.assertEqual(len(cards), len(data), "one card per goal")
        print(f"r3 cards: {len(cards)}")

        for entry, card in zip(data, cards):
            self.assertEqual(card["id"], entry["id"])
            text = norm(" ".join(card["text"]))
            self.assertIn(entry["card"]["title"], text, entry["id"])
            self.assertIn(entry["card"]["plain"], text, entry["id"])
            self.assertIn(entry["status"], text, entry["id"])
            self.assertIn(entry["status"], card["classes"], entry["id"])
            if entry["status"] == "pending":
                self.assertIn("pending", text, entry["id"])

        pending = [c for c, e in zip(cards, data) if e["status"] == "pending"]
        self.assertTrue(pending, "expected pending goals in the real data")
        self.assertTrue(all("pending" in c["classes"] for c in pending))


if __name__ == "__main__":
    unittest.main()
