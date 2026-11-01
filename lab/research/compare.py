"""Differing blocks between worlds, counted from their raw chunk dumps.

python lab/research/compare.py <a.json> <b.json> [--out result.json]

Raw dumps are zlib-compressed names in fixed (x, y, z) order, kept outside the repo.
A pair is read from raw only when its chunk hashes differ, or when it is a control (full=True);
a hash mismatch with the raw count is an error.
"""
import argparse
import json
import sys
import zlib
from pathlib import Path


def load_ids(path, table):
    names = zlib.decompress(Path(path).read_bytes()).decode().split("\n")
    return [table.setdefault(n, len(table)) for n in names]


def chunk_file(raw_dir, ck):
    return Path(raw_dir) / f"{ck.replace(',', '_')}.z"


def diff_pairs(worlds, pairs, full=()):
    table = {}
    out = {p: {"total": 0, "by_chunk": {}} for p in pairs}
    for ck in next(iter(worlds.values()))["chunks"]:
        ids = {}
        for p in pairs:
            a, b = p
            same = worlds[a]["chunks"][ck]["sha256"] == worlds[b]["chunks"][ck]["sha256"]
            if same and p not in full:
                continue
            for w in p:
                if w not in ids:
                    ids[w] = load_ids(chunk_file(worlds[w]["raw"], ck), table)
            n = sum(1 for x, y in zip(ids[a], ids[b]) if x != y)
            if same != (n == 0):
                raise RuntimeError(f"hash and raw disagree for {p} chunk {ck}: {n} differing")
            if n:
                out[p]["by_chunk"][ck] = n
                out[p]["total"] += n
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--out")
    args = p.parse_args(argv)
    worlds = {}
    for path in (args.a, args.b):
        label = Path(path).stem
        worlds[label] = json.loads(Path(path).read_text(encoding="utf-8"))
    la, lb = list(worlds)
    if list(worlds[la]["chunks"]) != list(worlds[lb]["chunks"]):
        sys.exit("worlds cover different chunks")
    res = diff_pairs(worlds, [(la, lb)], full=((la, lb),))[(la, lb)]
    equal_by_hash = sum(
        worlds[la]["chunks"][ck]["sha256"] == worlds[lb]["chunks"][ck]["sha256"] for ck in worlds[la]["chunks"]
    )
    report = {"a": la, "b": lb, "total": res["total"], "by_chunk": res["by_chunk"],
              "chunks": len(worlds[la]["chunks"]), "chunks_equal_by_hash": equal_by_hash}
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
