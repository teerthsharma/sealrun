import json
import unittest
from itertools import permutations
from pathlib import Path

PARTITIONS = Path(__file__).resolve().parents[1] / "results" / "research" / "partitions.json"


def pair_table(run):
    pairs = run.get("pairs")
    if not pairs:
        return None, None
    d = {}
    for p in pairs:
        a, b, v = p["a"], p["b"], p["diff_total"]
        if a == b or not isinstance(v, int) or v < 0:
            raise AssertionError(f"{run['experiment']}: bad pair {p}")
        for key in ((a, b), (b, a)):
            if d.get(key, v) != v:
                raise AssertionError(f"{run['experiment']}: asymmetric pair {p}")
            d[key] = v
    worlds = sorted({a for a, _ in d})
    if len(worlds) != run.get("n_worlds"):
        raise AssertionError(f"{run['experiment']}: {len(worlds)} worlds in pairs, n_worlds={run.get('n_worlds')}")
    missing = [(a, b) for a, b in permutations(worlds, 2) if (a, b) not in d]
    if missing:
        raise AssertionError(f"{run['experiment']}: {len(missing)} missing pairs, first {missing[0]}")
    return worlds, d


class Lab(unittest.TestCase):
    def sameness_is_transitive_on_every_measured_triple(self):
        data = json.loads(PARTITIONS.read_text(encoding="utf-8"))
        with_pairs = []
        checked = 0
        premise = 0
        violations = []
        for run in data["runs"]:
            worlds, d = pair_table(run)
            if worlds is None:
                continue
            with_pairs.append(run["experiment"])
            for a, b, c in permutations(worlds, 3):
                checked += 1
                if d[a, b] == 0 and d[b, c] == 0:
                    premise += 1
                    if d[a, c] != 0:
                        violations.append((run["experiment"], a, b, c, d[a, c]))
        print(f"experiments with pairwise counts: {len(with_pairs)} of {len(data['runs'])} ({', '.join(with_pairs) or 'none'})")
        print(f"triples checked: {checked}")
        print(f"triples with premise true (d(a,b)=0 and d(b,c)=0): {premise}")
        print(f"violations (d(a,c)!=0): {len(violations)}")
        for v in violations[:10]:
            print("  violation", v)
        self.assertGreaterEqual(premise, 1, "no triple had the premise true: nothing checked, refusing to pass empty")
        self.assertEqual(violations, [], "sameness is not transitive on measured triples")


if __name__ == "__main__":
    unittest.main()
