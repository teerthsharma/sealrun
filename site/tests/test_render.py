import html.parser
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class CardParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.goal_ids = []
        self.text = {}

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        goal = dict(attrs).get("data-goal")
        if goal is not None:
            self.goal_ids.append(goal)
            self.text.setdefault(goal, [])
        self.stack.append((tag, goal))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        for _, goal in self.stack:
            if goal is not None:
                self.text[goal].append(data)


def norm(s):
    return " ".join(s.split())


def extract_render(index_html):
    m = re.search(r"^function renderPage\(.*?^\}", index_html, re.S | re.M)
    check(m is not None, "index.html has no top-level renderPage function")
    return m.group(0)


def render_with_node(data_path, render_src):
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "render.cjs"
        script.write_text(
            render_src
            + "\nprocess.stdout.write(renderPage(JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'))));\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(script), str(data_path)],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    check(proc.returncode == 0, f"node render failed: {proc.stderr.strip()}")
    return proc.stdout


def site_page_renders_goal_cards():
    index = SITE / "index.html"
    check(index.is_file(), f"missing {index}")
    data_path = SITE / "goals.json"
    goals = json.loads(data_path.read_text(encoding="utf-8"))["goals"]
    ids = [g["id"] for g in goals]

    out = render_with_node(data_path, extract_render(index.read_text(encoding="utf-8")))
    parser = CardParser()
    parser.feed(out)
    parser.close()

    counts = Counter(parser.goal_ids)
    missing = sorted(set(ids) - set(counts))
    extra = sorted(set(counts) - set(ids))
    dup = sorted(k for k, v in counts.items() if v > 1)
    check(not missing, f"no card for goals: {missing[:10]}")
    check(not extra, f"cards for unknown goals: {extra[:10]}")
    check(not dup, f"more than one card for goals: {dup[:10]}")

    for g in goals:
        text = norm(" ".join(parser.text[g["id"]]))
        check(norm(g["title"]) in text, f"card {g['id']} does not show its title")
        if g["plain"]:
            check(norm(g["plain"]) in text, f"card {g['id']} does not show its plain text")


if __name__ == "__main__":
    try:
        site_page_renders_goal_cards()
    except AssertionError as e:
        print(f"FAIL site_page_renders_goal_cards: {e}")
        sys.exit(1)
    print("PASS site_page_renders_goal_cards")
