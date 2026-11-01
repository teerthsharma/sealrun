"""Inverse of the stamp law: which tickets does each chunk listen to.

python lab/research/hypergraph.py <experiment> [...]

Reads worlds/<experiment>_*.json from research/campaign (git show, no checkout) and appends one run
per experiment to lab/results/research/hypergraph.json. Law under test (House, unverified): a chunk's
sha depends on the order only through min_sigma S(c), the first ticket of S(c) in the order.
"""
import itertools
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "lab" / "results" / "research" / "hypergraph.json"
REF = "research/campaign"
WORLDS = "lab/results/research/worlds"
RADII = (2, 3, 4)
IST = timezone(timedelta(hours=5, minutes=30))
LAW = "chunk sha depends on the order only through min_sigma S(c); S_hat(c) = smallest S whose first-of-S partition equals the sha partition"


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def ball(c, tickets, R):
    return frozenset(i for i, t in enumerate(tickets) if cheb(t, c) <= R)


def is_ball(S, c, tickets):
    top = max(cheb(t, c) for t in tickets)
    return any(S == ball(c, tickets, r) for r in range(top + 1))


def first_of(order, S):
    return next(t for t in order if t in S)


def partition(labels):
    groups = {}
    for i, lab in enumerate(labels):
        groups.setdefault(lab, set()).add(i)
    return frozenset(frozenset(g) for g in groups.values())


def fitting_sets(orders, shas, k):
    target = partition(shas)
    fits = []
    for n in range(1, k + 1):
        for S in itertools.combinations(range(k), n):
            S = frozenset(S)
            if partition([first_of(o, S) for o in orders]) == target:
                fits.append(S)
    return fits


def smallest(fits):
    n = min(len(S) for S in fits)
    return [S for S in fits if len(S) == n]


def minimal(orders, shas, k):
    fits = fitting_sets(orders, shas, k)
    return smallest(fits) if fits else []


def is_constant(shas):
    return len(set(shas)) == 1


def repeat_mismatches(worlds):
    groups = {}
    for w in worlds:
        groups.setdefault(json.dumps(w["order"]), []).append(w)
    bad = []
    for order, ws in groups.items():
        for key in ws[0]["chunks"]:
            shas = sorted({str(w["chunks"].get(key, {}).get("sha256")) for w in ws})
            if len(shas) > 1:
                bad.append({"order": json.loads(order), "chunk": key, "shas": shas})
    return bad


def repeat_diffs(worlds):
    counts = {}
    for x in repeat_mismatches(worlds):
        counts[x["chunk"]] = counts.get(x["chunk"], 0) + 1
    return counts


def analyze(worlds):
    tickets = sorted({tuple(t) for t in worlds[0]["order"]})
    index = {t: i for i, t in enumerate(tickets)}
    k = len(tickets)
    orders = [tuple(index[tuple(t)] for t in w["order"]) for w in worlds]
    keys = sorted(set.intersection(*(set(w["chunks"]) for w in worlds)))
    noisy = repeat_diffs(worlds)
    chunks, violations, non_ball = {}, [], []
    match = {R: {"exact": 0, "tied": 0, "fits": 0} for R in RADII}
    for key in keys:
        if key in noisy:
            chunks[key] = {"noisy": True, "repeat_diff_orders": noisy[key]}
            continue
        c = tuple(int(v) for v in key.split(","))
        shas = [w["chunks"][key]["sha256"] for w in worlds]
        fits = fitting_sets(orders, shas, k)
        rec = {"noisy": False, "constant": is_constant(shas), "n_fits": len(fits)}
        if not fits:
            violations.append(key)
            rec["violation"] = True
            rec["partition"] = [
                [[list(tickets[t]) for t in orders[i]] for i in sorted(g)] for g in partition(shas)
            ]
            chunks[key] = rec
            continue
        s_hat = smallest(fits)
        rec["fits"] = [sorted(S) for S in fits]
        rec["S_hat"] = [sorted(S) for S in s_hat]
        if not rec["constant"] and not any(is_ball(S, c, tickets) for S in s_hat):
            non_ball.append(key)
        rec["ball"] = {}
        for R in RADII:
            b = ball(c, tickets, R)
            exact = s_hat == [b]
            tied = b in s_hat and len(s_hat) > 1
            fit = b in fits
            match[R]["exact"] += exact
            match[R]["tied"] += tied
            match[R]["fits"] += fit
            rec["ball"][str(R)] = {"set": sorted(b), "exact": exact, "tied": tied, "fits": fit}
        chunks[key] = rec
    return {
        "k": k,
        "tickets": [list(t) for t in tickets],
        "distinct_orders": len({o for o in orders}),
        "chunks_total": len(keys),
        "chunks_stable": len(keys) - len(noisy),
        "summary": {
            "noisy": sorted(key for key in keys if key in noisy),
            "violations": violations,
            "constant": sum(r.get("constant", False) for r in chunks.values()),
            "non_ball_S_hat": non_ball,
            "match_by_R": {str(R): match[R] for R in RADII},
        },
        "chunks": chunks,
    }


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def load(exp):
    paths = [p for p in git("ls-tree", "-r", "--name-only", REF, WORLDS).split()
             if Path(p).name.startswith(exp + "_") and p.endswith(".json")]
    return paths, [json.loads(git("show", f"{REF}:{p}")) for p in paths]


def run(exp):
    sha = git("rev-parse", REF).strip()
    paths, worlds = load(exp)
    if not worlds:
        return None
    ticket_sets = {tuple(sorted(tuple(t) for t in w["order"])) for w in worlds}
    if len(ticket_sets) != 1:
        raise SystemExit(f"{exp}: worlds do not share one ticket set")
    ctrl = repeat_mismatches(worlds)
    entry = {"experiment": exp, "campaign_sha": sha, "worlds": paths,
             "tickets": [list(t) for t in sorted({tuple(t) for t in worlds[0]["order"]})],
             "repeat_control": {"noisy_chunks": len(repeat_diffs(worlds)), "mismatches": ctrl},
             "when": datetime.now(IST).isoformat()}
    entry.update(analyze(worlds))
    return entry


def main(argv):
    res = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"law": LAW, "runs": []}
    for exp in argv:
        entry = run(exp)
        if entry is None:
            print(f"{exp}: no worlds on {REF}")
            continue
        res["runs"].append(entry)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
        s = entry["summary"]
        print(f"{exp} @ {entry['campaign_sha'][:7]} worlds {len(entry['worlds'])} "
              f"chunks {entry['chunks_total']} noisy {len(s['noisy'])} stable {entry['chunks_stable']} "
              f"violations {len(s['violations'])} match {s['match_by_R']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
