import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_r3

CHARTS = Path(__file__).resolve().parents[1] / "charts" / "r3"


def write(folder, name, data):
    (folder / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class Lab(unittest.TestCase):
    def build_r3_merges_cards_with_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cards = folder / "cards"
            cards.mkdir()
            write(cards, "foreman.json", [
                {"id": "N3.G1", "plain": "foreman card"},
                {"id": "N3.G2", "plain": "second foreman card"},
            ])
            write(cards, "chase.json", [{"id": "N3.C1", "why": "chase card"}])
            write(folder, "status.json", {"N3.G1": "reached", "N3.C1": "partial"})

            result = build_r3.build(cards, folder / "status.json")

        ids = sorted(e["id"] for e in result)
        self.assertEqual(ids, ["N3.C1", "N3.G1", "N3.G2"])
        status = {e["id"]: e["status"] for e in result}
        self.assertEqual(status["N3.G1"], "reached")
        self.assertEqual(status["N3.C1"], "partial")
        self.assertEqual(status["N3.G2"], "pending")

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.json"
            write(Path(tmp), "empty.json", {})
            real = build_r3.build(CHARTS, empty)

        expected = sorted(
            card["id"]
            for name in ("foreman", "chase", "cameron")
            for card in json.loads((CHARTS / f"{name}.json").read_text(encoding="utf-8"))
        )
        self.assertEqual(sorted(e["id"] for e in real), expected)
        self.assertTrue(all(e["status"] == "pending" for e in real))
        print(f"r3 cards: {len(real)}")


if __name__ == "__main__":
    unittest.main()
