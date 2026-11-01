"""Restriction refit of stable chunks: first(S), last(S) and pattern(S) of a ticket subset S.

python lab/research/restriction.py [E1 E2 E3 E4 P W]

E1 to E4 load through hypergraph.load (research/campaign); P and W load from research/leap by git show.
Writes lab/results/research/restriction.json and prints one summary table. A family fits a stable chunk
when equal signatures always give equal sha. The class counts per R are post-hoc: R was chosen after
looking at the data, so they are fits, not predictions.
"""
import itertools
import json
import math
import sys
from pathlib import Path

import hypergraph as H

OUT = H.ROOT / "lab" / "results" / "research" / "restriction.json"
SOURCES = {
    "E1": ("research/campaign", "E1"),
    "E2": ("research/campaign", "E2"),
    "E3": ("research/campaign", "E3"),
    "E4": ("research/campaign", "E4"),
    "P": ("research/leap", "leap_P"),
    "W": ("research/leap", "leap_W"),
}
FAMILIES = ("first", "last", "pattern")
RADII = (2, 3, 4, 5)
METHOD = {
    "first": "first ticket of S in the order",
    "last": "last ticket of S in the order",
    "pattern": "tuple of S's tickets in the order's sequence",
    "fit": "a family fits a chunk when equal signatures always give equal sha",
    "informative": "minimal fitting |S| below k, constant chunks excluded",
    "post_hoc": "restriction class counts use R chosen after the first look: fits, not predictions",
}


def signature(family, order, S):
    if family == "first":
        return next(t for t in order if t in S)
    if family == "last":
        return next(t for t in reversed(order) if t in S)
    return tuple(t for t in order if t in S)


def fits(family, orders, shas, S):
    seen = {}
    for order, sha in zip(orders, shas):
        if seen.setdefault(signature(family, order, S), sha) != sha:
            return False
    return True


def subsets(k):
    return [frozenset(c) for n in range(1, k + 1) for c in itertools.combinations(range(k), n)]


def family_record(family, orders, shas, c, tickets, subs):
    fitting = [S for S in subs if fits(family, orders, shas, S)]
    if not fitting:
        return {"fits": False, "min_size": None, "min_sets": [], "ball": {str(R): False for R in RADII}}
    n = min(len(S) for S in fitting)
    mins = [S for S in fitting if len(S) == n]
    ball = {str(R): any(S == H.ball(c, tickets, R) for S in mins) for R in RADII}
    return {"fits": True, "min_size": n, "min_sets": [sorted(S) for S in mins], "ball": ball}


def informative(rec, k):
    return rec["min_size"] is not None and rec["min_size"] < k


def analyze(worlds):
    tickets = sorted({tuple(t) for t in worlds[0]["order"]})
    index = {t: i for i, t in enumerate(tickets)}
    k = len(tickets)
    orders = [tuple(index[tuple(t)] for t in w["order"]) for w in worlds]
    distinct = list(dict.fromkeys(orders))
    keys = sorted(set.intersection(*(set(w["chunks"]) for w in worlds)))
    noisy = H.repeat_diffs(worlds)
    subs = subsets(k)
    chunks, stable, shas_of = {}, [], {}
    for key in keys:
        if key in noisy:
            chunks[key] = {"noisy": True, "repeat_diff_orders": noisy[key]}
            continue
        c = tuple(int(v) for v in key.split(","))
        shas = [w["chunks"][key]["sha256"] for w in worlds]
        shas_of[key] = shas
        chunks[key] = {
            "noisy": False,
            "constant": H.is_constant(shas),
            "hypergraph_first_partition_fits": bool(H.fitting_sets(orders, shas, k)),
            "families": {f: family_record(f, orders, shas, c, tickets, subs) for f in FAMILIES},
        }
        stable.append(key)
    live = [key for key in stable if not chunks[key]["constant"]]
    fam_summary = {}
    for f in FAMILIES:
        hist = {str(n): 0 for n in range(1, k + 1)}
        hist["none"] = 0
        ball = {str(R): {"matches": 0, "of": 0, "chance": 0.0} for R in RADII}
        for key in live:
            rec = chunks[key]["families"][f]
            hist["none" if rec["min_size"] is None else str(rec["min_size"])] += 1
            if informative(rec, k):
                c = tuple(int(v) for v in key.split(","))
                m = rec["min_size"]
                for R in RADII:
                    b = H.ball(c, tickets, R)
                    ball[str(R)]["of"] += 1
                    ball[str(R)]["matches"] += rec["ball"][str(R)]
                    ball[str(R)]["chance"] += (len(b) == m) / math.comb(k, m)
        for R in RADII:
            ball[str(R)]["chance"] = round(ball[str(R)]["chance"], 2)
        fam_summary[f] = {
            "informative": sum(informative(chunks[key]["families"][f], k) for key in live),
            "fits_none": hist["none"],
            "min_size_hist": hist,
            "ball_match": ball,
        }
    measured, predicted = set(), {str(R): set() for R in RADII}
    exact = {str(R): 0 for R in RADII}
    exact_live = {str(R): 0 for R in RADII}
    for key in stable:
        c = tuple(int(v) for v in key.split(","))
        first_sha = {}
        for o, s in zip(orders, shas_of[key]):
            first_sha.setdefault(o, s)
        got = H.partition([first_sha[d] for d in distinct])
        measured.add(got)
        for R in RADII:
            b = H.ball(c, tickets, R)
            pred = H.partition([tuple(t for t in d if t in b) for d in distinct])
            predicted[str(R)].add(pred)
            exact[str(R)] += pred == got
            exact_live[str(R)] += (pred == got) and not chunks[key]["constant"]
    return {
        "k": k,
        "tickets": [list(t) for t in tickets],
        "worlds_n": len(worlds),
        "distinct_orders": len(distinct),
        "chunks_total": len(keys),
        "chunks_noisy": len(keys) - len(stable),
        "chunks_stable": len(stable),
        "constant": len(stable) - len(live),
        "summary": {
            "families": fam_summary,
            "unexplained_below_k": [key for key in live
                                    if not any(informative(chunks[key]["families"][f], k) for f in FAMILIES)],
            "pattern_all_fits_failures": sum(not chunks[key]["families"]["pattern"]["fits"] for key in stable),
            "control_hypergraph_first_partition_violations":
                sum(not chunks[key]["hypergraph_first_partition_fits"] for key in stable),
        },
        "classes": {
            "measured": len(measured),
            "restriction": {str(R): {"predicted": len(predicted[str(R)]), "exact": exact[str(R)]}
                            for R in RADII},
            "exact_live": exact_live,
        },
        "chunks": chunks,
    }


def load(name):
    ref, prefix = SOURCES[name]
    if name.startswith("E"):
        paths, worlds = H.load(name)
        return ref, paths, worlds
    paths = [p for p in H.git("ls-tree", "-r", "--name-only", ref, H.WORLDS).split()
             if Path(p).name.startswith(prefix + "_") and p.endswith(".json")]
    return ref, paths, [json.loads(H.git("show", f"{ref}:{p}")) for p in paths]


def run(name):
    ref, paths, worlds = load(name)
    if not worlds:
        raise SystemExit(f"{name}: no worlds on {ref}")
    if len({tuple(sorted(tuple(t) for t in w["order"])) for w in worlds}) != 1:
        raise SystemExit(f"{name}: worlds do not share one ticket set")
    return {"experiment": name, "source": ref, "source_sha": H.git("rev-parse", ref).strip(),
            "worlds": paths, **analyze(worlds)}


def table(runs):
    out = ["Minimal-|S| histogram and ball matches. Cell m/i~c: informative chunks (min|S|<k, live) whose "
           "some minimal S equals ball(c,R) = m of i; c = expected matches for a uniform random S of the same size"]
    out.append(f"{'exp':<4}{'family':<9}{'inf':>4}  {'min|S| 1..k, none (live chunks)':<34}"
               + "".join(f"{'R=' + str(R):>13}" for R in RADII))
    for r in runs:
        k = r["k"]
        for f in FAMILIES:
            fs = r["summary"]["families"][f]
            hist = " ".join(f"{n}:{fs['min_size_hist'][str(n)]}" for n in range(1, k + 1))
            hist += f" none:{fs['min_size_hist']['none']}"
            cells = "".join(
                f"{fs['ball_match'][str(R)]['matches']}/{fs['ball_match'][str(R)]['of']}"
                f"~{fs['ball_match'][str(R)]['chance']:.2f}".rjust(13) for R in RADII)
            out.append(f"{r['experiment']:<4}{f:<9}{fs['informative']:>4}  {hist:<34}{cells}")
    out.append("")
    out.append("Chunk counts and classes. post/exact_live: post-hoc predicted restriction classes / "
               "stable live chunks whose measured partition equals the restriction partition (post-hoc R)")
    out.append(f"{'exp':<4}{'k':>2}{'orders':>7}{'stable':>7}{'const':>6}{'live':>6}{'unexpl<k':>9}"
               f"{'hyp-1st-viol':>13}{'measured':>9}" + "".join(f"{'R=' + str(R):>13}" for R in RADII))
    for r in runs:
        s, cl = r["summary"], r["classes"]
        cols = "".join(
            f"{str(cl['restriction'][str(R)]['predicted']) + '/' + str(cl['exact_live'][str(R)]):>13}"
            for R in RADII)
        live = r["chunks_stable"] - r["constant"]
        out.append(f"{r['experiment']:<4}{r['k']:>2}{r['distinct_orders']:>7}{r['chunks_stable']:>7}"
                   f"{r['constant']:>6}{live:>6}{len(s['unexplained_below_k']):>9}"
                   f"{s['control_hypergraph_first_partition_violations']:>13}{cl['measured']:>9}{cols}")
    return "\n".join(out)


def main(argv):
    names = argv or list(SOURCES)
    runs = [run(n) for n in names]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"method": METHOD, "runs": runs}, indent=2) + "\n", encoding="utf-8")
    print(table(runs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
