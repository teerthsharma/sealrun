import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verdict


def result(repeat_diff, lever):
    return {
        "seed": 7,
        "area": "square",
        "height": 64,
        "orders": 24,
        "control": {"repeat_diff": repeat_diff},
        "lever": lever,
    }


class Lab(unittest.TestCase):
    def test_guard_noise_floor_first(self):
        cases = [
            ("order_none.json", result(None, True)),
            ("order_zero.json", result(0, True)),
            ("order_shaky.json", result(2, True)),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, body in cases:
                path = Path(tmp) / name
                path.write_text(json.dumps(body), encoding="utf-8")
                paths.append(path)
            none_line, zero_line, shaky_line = verdict.statements(paths)
        for claim in ("lever", "order matters", "more diamonds"):
            self.assertNotIn(claim, none_line.lower())
        self.assertIn("noise floor not measured", none_line)
        self.assertNotIn("shaky", zero_line)
        self.assertIn("shaky", shaky_line)


if __name__ == "__main__":
    unittest.main()
