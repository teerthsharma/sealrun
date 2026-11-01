# Verification plan, round 2 batch 14 (Wilson, 2026-11-01)

Read from: int/r2-b14 head 9b2dcfc = main b27a705 + res/N2.G1.4.5 df95ea7 (merge 64d7aa5) + res/N2.G3.C6 f0d3743.
`git diff --stat b27a705 9b2dcfc`: 4 files, 208 insertions (lab/pool.py 9, lab/tests/test_pool.py 60,
lab/tests/test_order_collapse.py 78, lab/results/order_collapse.json 61). Contract: house/lab-api.md:273-287.
Pins: 9b2dcfc. If `git rev-parse --short int/r2-b14` differs (other than this plan's own commit), stop and report.
Already run by Wilson on 9b2dcfc (Python 3.11.9), pure only, no server, no java: the pool test by name (GREEN, 5 more
repeats all `OK`), pool mutants PA..PI, an edge probe of `run` (E below). `git status --short` empty after each.

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v14-<gid> 9b2dcfc`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- The pool lane is pure and done (below); nothing to run there.
- Every real-server run goes through the slot holder, at most 2 real servers across ALL agents; every run below needs
  one slot and runs its boots one after another:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <test or probe> <name> > <your scratchpad>/<run>.txt 2>&1; echo EXIT=$?`
  Paste `grep -nE "slot.py|fingerprint|not_full|changed|by_chunk|running|stopped|loaded|^Ran|^OK|FAILED|Error|line [0-9]+" <run>.txt`.
- Free RAM before each real run: `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"`
  must print >= 1500; below that, wait.
- Java PIDs before and after: `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears
  and stays after the run is a defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- `ls -A ~/sealrun-lab` before and after. A `tmp*` folder present after and not before is a defect to report; if it
  holds `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- Always pass the test name (the methods lack `test_`; without it each file prints `Ran 0 tests`, `OK`, EXIT=0; Wilson
  ran both files without the name): `Lab.pool_returns_results_in_job_order_and_refuses_four_servers`,
  `Lab.same_first_chunk_orders_give_zero_diff`.
- The collapse test rewrites the tracked lab/results/order_collapse.json (test :53-64). After any run of it:
  `git diff lab/results/order_collapse.json` (paste it), then `git checkout -- lab/results/order_collapse.json`.
- Mutation: apply with the Edit tool (exact old/new below), run, then `git checkout -- <file>`; `git status --short`
  must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.

## Fixed facts (read by Wilson on 9b2dcfc)
- pool.py:5-6 checks `workers not in (1, 2)` and raises `ValueError` before the executor exists (:7), so no job starts;
  :7 `ThreadPoolExecutor(max_workers=workers)`; :8 submits every job; :9 `[f.result() for f in futures]` returns in
  job order and re-raises a job's exception. Matches lab-api.md:274-277.
- Probe E (Wilson, original pool.py): `run([0, 1], fn, 0)` and `run(..., 1.5)` raise `ValueError` with 0 calls;
  `run(..., True)` returns `[0, 1]` (True == 1, bool is an int). The contract does not name bool; not a defect.
- test_pool.py line numbers below are the file's own. Peak counting (:14-28) uses a lock around now/peak; delays
  :11 make job 1 finish first, so the as_completed mutant sees `r1` first.
- Collapse orders: O1 = `square_orders(64, 64)[0]` = square(64, 64) = [(64,64),(65,64),(64,65),(65,65)] (orders.py:43-48);
  O2 = [O1[0]] + O1[:0:-1] = [(64,64),(65,65),(64,65),(65,64)] (test :37-38). The committed json orders match both.
- Window: `run_order` boxes the min/max chunks of the order (orderrun.py:30-34), so every run reads the same 2x2
  square x 1024..1055, z 1024..1055, y 0..255 = 4 x 16 x 16 x 256 = 262144 positions = json "positions" 262144.
  All four chunks are at Chebyshev d <= 1 of the first ticket (64, 64).
- Committed order_collapse.json: control_changed 0, pair_changed 0, by_chunk_pair all 0, examples [], not_full
  [0, 0, 0], three fingerprints all `1a12bc506f9b6a7684ed71c8cea08eee70caa17b4974c95f1e59eabbb998e416`,
  when 2026-11-01T11:44:08.623282+05:30. The 64.3 s run time is not recorded in the json: unverified.
- The json and asserts implement the contract (lab-api.md:281-287): written before asserting (:53-64 before :72-74),
  asserts nones [0,0,0] (:72), control 0 (:73), pair 0 (:74). The test does not assert that O1/O2 equal the contract
  orders, nor that O2 != O1.

## Can the guard's window see the order at all
- Measured tile (lab/results/forceload_tile.json, test_forceload_tile.py:30-55): one `forceload add 1024 1024`
  ticket, `wait_loaded`, `save-all flush`, stop, then read: every offset with max(|dx|, |dz|) <= 2 is "full", every
  d = 3 offset is None. Offsets 0,0 / 1,0 / 0,1 / 1,1 (the whole collapse square) are "full" from the first ticket
  alone.
- So ticket 1 alone carries every chunk of the window to full; tickets 2-4 (the only part where O1 and O2 differ)
  change no chunk's final status inside the window. Chunks they newly reach (d = 3 of (64, 64), e.g. (67, 64)) lie
  outside the window.
- Not measured: the tile is read after `stop` (test_forceload_tile.py:31-33), not at the moment `run_order` issues
  ticket 2 (orderrun.py:25-27, right after the first `save-all flush`). Whether the square is already decorated/full
  before ticket 2 starts is unverified; probe PT below decides it.
- If PT prints all four chunks "full" while running: the window is final before the order of tickets 2-4 starts, so
  the guard cannot see that order, and pair_changed 0 says the same as control_changed 0 (run-to-run determinism of
  ticket 1 at d <= 1). If PT prints any square chunk not "full": tickets 2-4 can still race with generation of that
  chunk and the guard can see order there.
- Batch 12 fact (chunk (66, 64) at d 2 varied across identical single-ticket runs) is outside this window
  (x chunks 64..65), so the guard cannot see that variation either.
- AB vs BA (order_pair.json: 18 changed, by_chunk 64,64: 12, 65,64: 6) changed the FIRST ticket; the collapse test
  never changes the first ticket, so no committed result shows this window can detect any order change (no positive
  control). RM-1 below is that control.

## Pool (pure, decided by Wilson; old/new in lab/pool.py, test by name)
GREEN: `python lab/tests/test_pool.py Lab.pool_returns_results_in_job_order_and_refuses_four_servers` -> `Ran 1 test`,
`OK` (6 runs, all OK). Resident's RED lead (before pool.py): not re-run (unverified).

| id | old | new | expected | observed |
|---|---|---|---|---|
| PA | `ThreadPoolExecutor(max_workers=workers)` | `ThreadPoolExecutor(max_workers=1)` | FAIL peak | FAILED :38 `1 != 2` (killed; resident lead matches) |
| PB | same | `ThreadPoolExecutor(max_workers=2)` | FAIL peak | FAILED :42 `2 != 1` (killed) |
| PC | `    if workers not in (1, 2):` | `    if False:` | FAIL | FAILED :46 `ValueError not raised` (killed; resident lead matches) |
| PD | `workers not in (1, 2)` | `workers not in (1, 2, 3)` | FAIL | FAILED :46 (killed) |
| PI | `workers not in (1, 2)` | `workers not in (1, 2, 4)` | FAIL | FAILED :46 at workers 3 (killed) |
| PE | `        return [f.result() for f in futures]` | `        from concurrent.futures import as_completed` + `        return [f.result() for f in as_completed(futures)]` | FAIL order | FAILED :37 `['r1', 'r0', 'r2', 'r3']` (killed; resident lead matches) |
| PF | check at :5-6 moved inside the `with`, after the submit line | | FAIL calls | FAILED :48 `4 != 0`, peak 3 (killed) |
| PG | `        return [f.result() for f in futures]` | `        return [None if f.exception() else f.result() for f in futures]` | FAIL | FAILED :55 `RuntimeError not raised` (killed) |
| PH | `workers not in (1, 2)` | `workers > 2` | survive | OK (SURVIVES). Probe E under PH: 0 still raises (executor's own ValueError), 1.5 runs both jobs. Contract says "1 or 2; otherwise ValueError"; test has no 0 or non-int case |

## Collapse guard mutants (lab/tests/test_order_collapse.py; decided by reading, no boot)
The expected value of every assert is 0 (or [0,0,0]), so any mutant that makes a count smaller or skips a run
survives. All below SURVIVE on any run where ticket-1 generation repeats (committed control_changed 0):
- GA o2 equals o1: old `        o2 = [o1[0]] + list(o1[:0:-1])` new `        o2 = list(o1)` -> OK (no O2 != O1 check).
- GB pair against itself: old `        pair_d = blockdiff.diff(w1, w2)` new `        pair_d = blockdiff.diff(w1, w1)` -> OK.
- GC no control world: old `        wc = run_fresh(o1)` new `        wc = w1` -> OK (one boot fewer; fingerprints still equal).
- GD pair assert removed: delete `        self.assertEqual(pair_changed, 0)` -> OK.
- GE wrong O1: old `orders.square_orders(64, 64)[0]` new `orders.square_orders(64, 64)[1]` -> OK (orders not
  asserted; visible only in the json "orders").
- GF json after asserts: move :53-64 below :74 -> OK on a pass (differs only on failure).
- GG chunk key: old `chunk_key((x >> 4, z >> 4))` new `chunk_key((x // 16, z // 16))` -> equivalent for all x, z.
Killing side: only a mutant that makes the windows differ can fail the test, and that needs real boots (RM-1).

## Real runs needed (resident, 1 slot each, sequential boots)
1. GREEN re-run, 3 boots: `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python
   lab/tests/test_order_collapse.py Lab.same_first_chunk_orders_give_zero_diff > <scratch>/g14.txt 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, three fingerprints `1a12bc50...e416` (any other value with OK is a finding: the square
   is not run-to-run stable), not_full [0, 0, 0]. Then the json rule above.
2. RM-1 positive control, 3 boots: old `        o2 = [o1[0]] + list(o1[:0:-1])` new `        o2 = list(o1[::-1])`
   (first ticket (65, 65) instead of (64, 64)). Same command, `> <scratch>/rm1.txt`. Expected FAILED at :74 with
   pair_changed > 0 (the window sees a first-ticket change). `OK` = the window cannot see even a first-ticket change
   in this square (finding). Undecidable by reading: order_pair.json measured a 2-chunk window with a different first
   chunk. Paste pair_changed and by_chunk_pair, then `git checkout -- lab/tests/test_order_collapse.py
   lab/results/order_collapse.json`.
3. PT status probe, 1 boot. Save as `<scratch>/pt14.py`, run from the worktree root:
   `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <scratch>/pt14.py > <scratch>/pt14.txt 2>&1; echo EXIT=$?`
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, "lab")
   import anvil, orderrun, server, serverdir
   SRC = Path("C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1")
   ROOT = Path.home() / "sealrun-lab"
   SQ = [(64, 64), (65, 64), (64, 65), (65, 65)]
   scratch = serverdir.make_scratch(SRC, ROOT)
   region = Path(scratch["dir"]) / "world" / "region"
   srv = None
   try:
       srv = server.boot(scratch)
       print("loaded", orderrun.wait_loaded(srv, 64, 64))
       srv.command("save-all flush")
       print("running", {f"{x},{z}": anvil.chunk_status(region, x, z) for x, z in SQ})
       srv.stop()
       srv = None
       print("stopped", {f"{x},{z}": anvil.chunk_status(region, x, z) for x, z in SQ})
   finally:
       if srv is not None:
           srv.stop()
       serverdir.remove(scratch["dir"])
   ```
   It repeats `run_order`'s steps up to the point where ticket 2 would be issued (orderrun.py:22-27). Read: "running"
   all "full" = the square is final before ticket 2 (guard blind to the order of tickets 2-4); any other status = not
   final. A PermissionError reading the region file while java holds it = probe undecided (report it; Windows
   sharing on the open region file is unverified).

Boots: GREEN 3 + RM-1 3 + PT 1 = 7 server boots, 3 slot runs, each 1 slot. The three runs may use the 2 slots in
parallel only if no other agent holds a slot.

## Defects
- None in pool.py against lab-api.md:274-277 (PA..PG, PI killed). Test gap: no case for workers 0 or a non-int (PH
  survives).
- None in test_order_collapse.py against lab-api.md:281-287 (every clause is written as specified). Test gaps:
  every reduce-to-zero mutant survives (GA..GE); no positive control in the committed results (RM-1 open); whether
  the window can see the order of tickets 2-4 is unverified until PT runs (tile is read after stop, not at ticket 2).
