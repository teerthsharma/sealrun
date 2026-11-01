import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

from test_render import SITE, VOID, check, extract_render, render_with_node

MAP = {"pending": "not started", "active": "in progress", "blocked": "failing", "reached": "passing", "retired": "retired"}
FORCED = {"G1.1": "pending", "G1.2": "active", "G1.3": "blocked", "G1.4": "reached"}


class BadgeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.card = None
        self.badges = {}

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if tag == "article":
            if "data-goal" in a:
                self.card = ("goal", a["data-goal"])
            elif "data-alt" in a:
                self.card = ("alt", a["data-alt"])
            else:
                self.card = None
            if self.card:
                self.badges[self.card] = []
        is_badge = "data-badge" in a
        if is_badge and self.card:
            self.badges[self.card].append("")
        self.stack.append((tag, is_badge))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.card and any(b for _, b in self.stack):
            self.badges[self.card][-1] += data


def site_page_shows_live_status():
    index = SITE / "index.html"
    src = index.read_text(encoding="utf-8")
    data = json.loads((SITE / "goals.json").read_text(encoding="utf-8"))
    ids = {g["id"] for g in data["goals"]}
    check(set(FORCED) <= ids, f"forced goals missing from goals.json: {sorted(set(FORCED) - ids)}")
    for g in data["goals"]:
        if g["id"] in FORCED:
            g["status"] = FORCED[g["id"]]

    with tempfile.TemporaryDirectory() as tmp:
        forced_path = Path(tmp) / "goals.json"
        forced_path.write_text(json.dumps(data), encoding="utf-8")
        out = render_with_node(forced_path, extract_render(src))

    parser = BadgeParser()
    parser.feed(out)
    parser.close()

    for g in data["goals"]:
        key = ("goal", g["id"])
        check(key in parser.badges, f"card {g['id']} not rendered")
        texts = parser.badges[key]
        check(len(texts) == 1, f"card {g['id']} has {len(texts)} badges, want 1")
        want = MAP.get(g["status"])
        check(want is not None, f"goal {g['id']} has unmapped status {g['status']}")
        got = " ".join(texts[0].split())
        check(got == want, f"card {g['id']} status {g['status']} shows '{got}', want '{want}'")

    for a in data["alternatives"]:
        key = ("alt", a["id"])
        check(key in parser.badges, f"alternative card {a['id']} not rendered")
        check(len(parser.badges[key]) == 1, f"alternative card {a['id']} has no single badge")

    check(re.search(r"setInterval\(\s*\w+\s*,\s*5000\s*\)", src), "index.html does not re-fetch every 5000 ms")
    check("cache: 'no-store'" in src, "index.html re-fetch does not use cache: 'no-store'")
    check('aria-live="polite"' in src, "index.html has no aria-live region")


if __name__ == "__main__":
    try:
        site_page_shows_live_status()
    except AssertionError as e:
        print(f"FAIL site_page_shows_live_status: {e}")
        sys.exit(1)
    print("PASS site_page_shows_live_status")
