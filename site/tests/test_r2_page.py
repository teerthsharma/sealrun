import html.parser
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BADGE = {"reached": "passing", "blocked": "failing", "active": "in progress"}


class Parsed(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.goals = []
        self.orders = []
        self.all_text = []
        self.marks = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        sink = None
        owner = next((o for _, _, o in reversed(self.stack) if o), None)
        if "data-goal" in a:
            sink = []
            owner = ("goal", a["data-goal"])
            self.goals.append((a["data-goal"], sink))
        elif "data-order" in a:
            sink = []
            owner = ("order", len(self.orders))
            self.orders.append(sink)
        if owner:
            self.marks.append((owner, a))
        self.stack.append((tag, sink, owner))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.all_text.append(data)
        for _, sink, _ in self.stack:
            if sink is not None:
                sink.append(data)


def norm(s):
    return " ".join(s.split())


def marks(parsed, owner, name):
    return [a[name] for o, a in parsed.marks if o == owner and name in a]


def card_text(parsed, gid):
    return norm(" ".join(next(s for g, s in parsed.goals if g == gid)))


def extract_render(source):
    m = re.search(r"^function renderR2\(.*?^\}", source, re.S | re.M)
    if m is None:
        raise AssertionError("r2.html has no top-level renderR2 function")
    return m.group(0)


def render(render_src, data):
    with tempfile.TemporaryDirectory() as tmp:
        data_path = Path(tmp) / "data.json"
        data_path.write_text(json.dumps(data), encoding="utf-8")
        script = Path(tmp) / "render.cjs"
        script.write_text(
            render_src
            + "\nprocess.stdout.write(renderR2(JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'))));\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(script), str(data_path)],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    if proc.returncode != 0:
        raise AssertionError(f"node render failed: {proc.stderr.strip()}")
    parsed = Parsed()
    parsed.feed(proc.stdout)
    parsed.close()
    return parsed


def goal(gid, title, status="pending", department=None):
    return {
        "id": gid, "fellows": ["foreman"], "title": title, "plain": f"About {gid}",
        "why": "why", "done_when": "done", "status": status, "department": department,
    }


class Lab(unittest.TestCase):
    def page_reads_r2_json_and_draws_cards_and_bars(self):
        page = SITE / "r2.html"
        self.assertTrue(page.is_file(), f"missing {page}")
        source = page.read_text(encoding="utf-8")
        self.assertTrue('fetch("r2.json")' in source or "fetch('r2.json')" in source,
                        "r2.html does not fetch r2.json")
        render_src = extract_render(source)

        goals = [
            goal("N2.A", "First goal", "reached", "neurology"),
            goal("N2.B", "Second goal", "blocked"),
            goal("N2.C", "Third goal", "active", "oncology"),
            goal("N2.D", "Fourth goal", "reached"),
        ]
        ids = [g["id"] for g in goals]
        route = {"played": False, "note": "NOTE MARKER"}
        orders = [
            {"order": [[0, 0], [1, 0]], "diff": 10},
            {"order": [[0, 1]], "diff": 20},
        ]

        with_orders = render(render_src, {"route": route, "goals": goals, "orders": orders})
        self.assertEqual([g for g, _ in with_orders.goals], ids)
        self.assertEqual(len(with_orders.orders), 2)
        self.assertIn("NOTE MARKER", norm(" ".join(with_orders.all_text)))

        for g in goals:
            text = card_text(with_orders, g["id"])
            self.assertIn(g["title"], text)
            self.assertIn(BADGE[g["status"]], text)
            if g["department"]:
                self.assertIn(g["department"], text)
            else:
                self.assertNotIn("null", text)

        status = {g["id"]: marks(with_orders, ("goal", g["id"]), "data-status") for g in goals}
        for g in goals:
            self.assertEqual(status[g["id"]], [g["status"]])
        self.assertNotEqual(status["N2.A"], status["N2.B"])
        self.assertEqual(status["N2.A"], status["N2.D"])

        heights = []
        for i, o in enumerate(orders):
            style = marks(with_orders, ("order", i), "style")
            self.assertEqual(len(style), 1)
            heights.append(int(re.search(r"height:(\d+)px", style[0]).group(1)))
            self.assertIn(str(o["diff"]), norm(" ".join(with_orders.orders[i])).split())
        self.assertEqual(heights[1], 2 * heights[0])

        without = render(render_src, {"route": route, "goals": goals})
        self.assertEqual([g for g, _ in without.goals], ids)
        self.assertIn("not run yet", norm(" ".join(without.all_text)))
        self.assertEqual(without.orders, [])

        real = json.loads((SITE / "r2.json").read_text(encoding="utf-8"))
        parsed = render(render_src, real)
        self.assertEqual([g for g, _ in parsed.goals], [g["id"] for g in real["goals"]])


if __name__ == "__main__":
    unittest.main()
