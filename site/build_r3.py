"""Join the round 3 cards with each goal's status into site/r3.json."""
import json
from pathlib import Path

HERE = Path(__file__).parent
CHARTS = HERE / "charts" / "r3"


def build(cards_dir, status_path):
    status_path = Path(status_path)
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    return [
        {"id": card["id"], "card": card, "status": status.get(card["id"], "pending")}
        for path in sorted(Path(cards_dir).glob("*.json"))
        for card in json.loads(path.read_text(encoding="utf-8"))
    ]


def main():
    out = build(CHARTS, HERE / "r3_status.json")
    (HERE / "r3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"r3.json: {len(out)} cards")


if __name__ == "__main__":
    main()
