# Verification plan, round 2 batch 10 (Wilson, 2026-11-01)

Read from: int/r2-b10 head 81bd937 = 908b679 + res/N2.G1.4.1 cc6077e (merge fe8f9c6) + res/N2.G3.2.A1 d908737
(merge a363b59) + res/N2.G3.C3 295a8cb (merge 81bd937). `git diff --stat 908b679 81bd937`: 6 files, 362 insertions
(lab/bench_vanilla.py 84, lab/tests/test_bench_vanilla.py 59, lab/results/worlds_vanilla.json 28,
lab/tests/test_forceload_tile.py 75, lab/results/forceload_tile.json 59, lab/tests/test_guard_settle_invariance.py 57).
Contract: house/lab-api.md:199-218. Pins: cc6077e, d908737, 295a8cb, int 81bd937. `main` is now 85a075b (moved
after the merge base 908b679); this plan pins 81bd937 only. If `git rev-parse --short int/r2-b10` differs, stop and report.
Already run by Wilson on 81bd937 (Python 3.11.9), pure only: harness H (below) on the original and on mutants BA..BM
in memory; probes G1, G2, G3 below; `python lab/tests/test_bench_vanilla.py` and `python lab/tests/test_forceload_tile.py`
with no name (each `Ran 0 tests`, `OK`). Real-server tests: not run by Wilson. `git status --short` empty after the
probes (plan file aside). At plan time: free RAM 2931 MB, one java.exe (PID 34964, not Wilson's), `~/sealrun-lab`
holds `.slot1` and `tmp5apuooqx` (not Wilson's).

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v10-<gid> 81bd937`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- Every real-server run goes through the slot holder, at most 2 real servers across ALL agents:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <test or probe> <name> > <your scratchpad>/<run>.txt 2>&1; echo EXIT=$?`
  A run that measures concurrency (only V-C below) holds both: `python .../slot.py python .../slot.py python <probe>`.
  Paste `grep -nE "slot.py|fingerprint|differing|^Ran|^OK|FAILED|Error|line [0-9]+" <run>.txt` and `head -c 600` of
  any AssertionError line.
- Free RAM before each real run: `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"`
  must print >= 1500 (>= 2500 for V-C); below that, wait.
- Java PIDs before and after: `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears
  and stays after the run is a defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- `ls -A ~/sealrun-lab` before and after. A `tmp*` folder present after and not before is a defect to report; if it
  holds `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- Always pass the test name where the method lacks `test_` (without it the file prints `Ran 0 tests`, `OK`, EXIT=0;
  Wilson ran both): `Lab.n_vanilla_servers_worlds_per_minute_and_ram_per_world`,
  `Lab.forceload_tile_full_at_0_to_2_and_not_saved_at_3`. The guard method is `test_settle_does_not_change_blocks`;
  the whole file runs it.
- The tile test rewrites the tracked `lab/results/forceload_tile.json` (test :61-62) on every run. After each tile run:
  `git diff lab/results/forceload_tile.json` (paste it: any change outside `"when"` is a finding), then
  `git checkout -- lab/results/forceload_tile.json`.
- Mutation: apply with the Edit tool (exact old/new below), run, expect the result named, then `git checkout -- <file>`;
  `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.
- Report for each real run: printed lines, `Ran`/`OK`/`FAILED`, the failing line, EXIT, java PIDs before and after,
  free MB before, the slot number, wall seconds.

## Fixed facts (read by Wilson on 81bd937)
- Worlds: `_lane` (bench_vanilla.py:17-40) boots once (:22, not counted), then loops while lane time < secs:
  `srv = server.reset(srv, root)` (:28) then `worlds += 1` (:29). A reset that raises skips :29, goes to `errs`
  (:32-33), and `measure` re-raises it after the joins (:56-57): no number is returned for a run with a failed reset.
  `worlds` = resets finished; the first world of each lane is not counted.
- Rate: per lane `elapsed` runs from after the first boot (:24) to after the last reset (:31), so it includes the
  overshoot of the last reset that starts before `secs` and ends after. `worlds_per_minute` = sum over lanes of
  `worlds_i / elapsed_i * 60` (:59). It is not over the wall time of `measure` (which also holds the first boot and the
  stops). The n=2 number 4.42 is a sum of two lane rates; the per-lane split is not saved. Arithmetic on the committed
  json: n=1 10 worlds at 3.07 -> lane elapsed 195.4 s; n=2 14 at 4.42 -> 190.0 s if the lanes are equal.
- RAM: `bench.peak_mb` (bench.py:35-50) returns `PeakWorkingSetSize` of one PID. Each reset makes a new java PID
  (server.py:142-145), so a lane's `peak` (:23, :27, :30) is the max over that lane's successive processes, not a sum.
  `peak_mb_total` (:60) = sum over lanes of those maxima, which may come from different moments (an upper bound on
  the concurrent total, not a sampled concurrent total). `mb_per_world` (:67) = `peak_mb_total / n` = mean peak MB per
  running server (one world each), as the contract defines it (lab-api.md:205). It is not RAM per generated world: the
  n=1 run generated 10 counted worlds and 812.2 is not divided by them. Committed json: 812.2/1 = 812.2,
  1609.2/2 = 804.6 (consistent).
- Concurrency: :51-55 start both threads, then join both. Nothing in the committed json records it: `when` (start of
  each `measure`) n=1 10:12:14, n=2 10:15:51; commit cc6077e 10:24:39, 528 s after the n=2 start, which leaves room
  for a sequential n=2 (about 2 x 195 s + boots). Concurrency of the committed run: unverified. 4.42 < 2 x 3.07 = 6.14
  is consistent with contention, not proof.
- `other_java` counts every java.exe at `measure` start (:46-47), including other agents' servers. The bound test
  asserts it only on the committed json (:53), not on the fresh run.
- Test :47-55 checks the committed json for keys, `other_java` 0, `worlds >= 1` and `not_run`. It never ties the values
  to `measure` or to each other (probe G0).
- Tile: rays cover 17 of the 25 tile chunks; unread at d <= 2: (-2,-1) (-2,1) (-1,-2) (-1,2) (1,-2) (1,2) (2,-1) (2,1)
  (offsets from (64, 64)); ring 3 read 8 of 24 (probe G2). `"ticket_held_at_stop": True` (test :57) is a literal,
  not measured.
- Guard: LO/HI (test :17-18) = (1024,0,1024)..(1039,255,1039) = chunk (64, 64) only, 16 x 16 x 256 = 65536
  positions. The test prints `not_full` (:45-46) but never asserts it; `window.box` on a missing or empty region dir
  returns 65536 None, and two such boxes have equal fingerprints (probe G1). An all-None pair passes.

## Harness H (pure; bench_vanilla through the real test file with fakes)
Script: `C:/Users/seal/AppData/Local/Temp/claude/C--Users-seal-AppData-Local-Claude-Data-claude-pzs8sxrjxfjjc-scratch-workspaces-4efb5d48-8914-40d5-958b-01186c779b92-becc5fed-0e4b-4c3d-be3e-3bf15fa39392-scratch-2026-11-01-42b70f/f708d1ce-97b8-4985-b4ab-75b219fa060b/scratchpad/h10.py`
(copy it to your scratchpad; run from the worktree root, no slot, no java). It sets SEALRUN_LAB to a temp dir, fakes
`server.boot` (0.2 s), `server.reset` (stop + 0.3 s + boot) and `bench.peak_mb` (800.0), uses real `make_scratch` and
`serverdir.remove`, and lists leftover scratch dirs. Modes: `bound` (the real test by name, `measure(1, 60)` shortened
to 2 s), `overlap` (`measure(2, 2)`, prints lane first-boot start offsets and `concurrent`), `fail` with
`FAIL_RESET=2` (n=1, 2nd reset raises), `fail2` with `FAIL_RESET=lane0` (n=2, lane 0 resets raise). Optional `MUT=<json
{old,new}>` applies a mutant in memory; residents instead Edit the file and run without MUT.
Original (Wilson): `bound OK`; overlap starts `[0.0, 0.0] concurrent True`, worlds_per_minute 240.0; fail
`raised RuntimeError('fake reset failed')`, `scratch left []`; fail2 the same.
Note: tasklist is real, so `other_java` in H output counts other agents' java (it read 1 during BA and BC).

## N2.G1.4.1 bench_vanilla (green cc6077e)
GREEN, 1 slot (measure(1, 60) runs one server at a time): `python .../slot.py python lab/tests/test_bench_vanilla.py
Lab.n_vanilla_servers_worlds_per_minute_and_ram_per_world` (resident 97.8 s). Expected `Ran 1 test`, `OK`. Add a
print-free check by pasting the java PID list before/after and `ls -A ~/sealrun-lab`.

Pure mutants (Wilson ran each through H; old/new in lab/bench_vanilla.py unless named):
- BA count a failed reset: old `            srv = server.reset(srv, root)\n            worlds += 1` new
  `            try:\n                srv = server.reset(srv, root)\n            except RuntimeError:\n                pass\n            worlds += 1`
  -> bound OK (SURVIVES the test); fail `returned {... 'worlds': 5 ...}`, fail2 `returned {... 'worlds': 11 ...}`
  (killed by H fail/fail2 only).
- BB threads not joined: old `    for t in threads:\n        t.join()` new `    pass` -> bound FAILED,
  `TypeError: 'NoneType' object is not subscriptable` (test :31, from bench_vanilla.py:58). Killed by the test. Do NOT
  boot it: the lane thread keeps a real server running after the test fails. (H lists a scratch dir as left because it
  reads before the unjoined fake thread ends; not a finding.)
- BC n=2 sequential: old `    for t in threads:\n        t.start()\n    for t in threads:\n        t.join()` new
  `    for t in threads:\n        t.start()\n        t.join()` -> bound OK (SURVIVES); overlap starts `[0.0, 2.24]
  concurrent False`, worlds_per_minute 239.11 vs 240.0 on the original. With fakes (no contention) the summed per-lane
  rate is the same sequential or concurrent: worlds_per_minute cannot tell. On real servers a sequential n=2 would
  read near 2 x n=1 (no contention), but nothing asserts it. Killed only by H overlap.
- BD scratch kept on an exception: old `            if scratch is not None:\n                serverdir.remove(scratch["dir"])`
  new `            if scratch is not None and not errs:\n                serverdir.remove(scratch["dir"])` -> bound OK
  (SURVIVES); fail `scratch left ['tmp...']`, fail2 two dirs left (killed by H fail/fail2 only).
- BH mb_per_world not divided: old `peak_total / n, 1)` new `peak_total, 1)` -> bound OK (SURVIVES: n=1); overlap
  `mb_per_world 1600.0`. No test reads the n=2 formula.
- BI first boot counted: old `        worlds = 0\n` new `        worlds = 1\n` -> bound OK (SURVIVES); overlap worlds 10
  vs 8.
- BJ no world counted: old `            worlds += 1` new `            worlds += 0` -> bound FAILED at test :34
  `AssertionError: 0 not greater than or equal to 1`. Killed.
- BK cap widened: old `CAP = (1, 2)` new `CAP = (1, 2, 3)` -> bound FAILED at test :42 `AssertionError: ValueError not
  raised`. Killed (boot and make_scratch are MagicMocks there, so no java even on a real run).
- BL rate over the longest lane: old `    per_minute = sum(o["worlds"] / o["elapsed"] for o in out) * 60` new
  `    per_minute = worlds / max(o["elapsed"] for o in out) * 60` -> bound OK, overlap 240.0 (SURVIVES; equal lanes).
  The definition of worlds_per_minute is not pinned by any test.
- BM lane error swallowed: old `    if errs:\n        raise errs[0]` new `    pass` -> bound OK (SURVIVES); fail and
  fail2 still raise, but `TypeError("'NoneType' object is not subscriptable")` instead of the reset's RuntimeError.
- G0 json not tied to measure (Wilson ran): in lab/results/worlds_vanilla.json set n=1 `mb_per_world` 1.0 and
  `worlds_per_minute` 999.0, n=2 `peak_mb_total` 5.0 -> H bound OK (SURVIVES). Removing the n=2 run fails at :50;
  `other_java` 1 fails at :53 (by reading). Restore with `git checkout -- lab/results/worlds_vanilla.json`.

Real mutant (1 boot run, 1 slot):
- BE current working set instead of peak, in lab/bench.py: old `        return c.PeakWorkingSetSize / MB` new
  `        return c.WorkingSetSize / MB`, then the GREEN command. Expected `OK` (SURVIVES) if the current working set of a
  booted 1.16.1 server is inside 200..2000 MB; a :35 failure means it is not. Paste the dict printed on failure.
  Outcome unverified. bench.py is shared: restore it before anything else.

Real probe V-C (concurrency on real servers; optional, both slots, about 90 s): save as `<scratchpad>/b10_vc.py`,
run from the worktree root with free RAM >= 2500:
```python
import sys, time, threading
from pathlib import Path
sys.path.insert(0, "lab")
import bench_vanilla, server
real_boot, log = server.boot, []
def boot(scratch, timeout=120.0):
    t0 = time.monotonic(); s = real_boot(scratch, timeout)
    log.append((threading.current_thread().name, round(t0, 1), round(time.monotonic(), 1), s.proc.pid)); return s
server.boot = boot
root = Path.home() / "sealrun-lab"
print(bench_vanilla.measure(2, 60, root))
t = min(a for _, a, _, _ in log)
for name, a, b, pid in sorted(log, key=lambda x: x[1]): print(name, a - t, b - t, pid)
```
Read: the two lanes' first boots start within a few seconds of each other = concurrent; the second lane's first boot
after the first lane's last = sequential (finding). Paste the dict and the per-boot lines. This does not re-measure
the committed 180 s numbers; whether those were produced by this code stays unverified.

## N2.G3.2.A1 forceload tile (green d908737)
GREEN, 1 boot: `python .../slot.py python lab/tests/test_forceload_tile.py
Lab.forceload_tile_full_at_0_to_2_and_not_saved_at_3` (resident 22.2 s). Expected `Ran 1 test`, `OK`, then the json
diff rule above.

Pure (Wilson ran G2): replaying test :64-67 over the committed rays passes. Decided by reading, no boot:
- TA range cut: old `DISTANCES = range(4)` new `DISTANCES = range(3)` -> SURVIVES (d 3 never asserted).
- TB rays cut: delete the four diagonal entries of RAYS (:26-29) -> SURVIVES (d 0..3 still match on the 4 axes).
- TC json after asserts: move :54-62 below the loop :64-67 -> SURVIVES on green; the contract's "writes before
  asserting" (lab-api.md:213) is not tested.
- TD no ticket: old `            self.assertTrue(orderrun.wait_loaded(srv, CENTRE[0], CENTRE[1]))` new `            pass`
  -> expected FAIL `None != 'full' : east d=0` (chunk (64, 64) is not on disk without a ticket: b8 far-chunk GREEN).
- TE remove + 60 s: insert `            srv.command("forceload remove 1024 1024")\n            time.sleep(60)` before
  `srv.command("save-all flush")` (:42) plus `import time` -> expected FAIL at a d 3 entry `'features' != None`
  (Finding n2-F2: after remove, 60 s and stop, d 3 is `features`).

Real mutant (1 boot): the lead-4 question.
- TF remove, stop at once: old `            srv.command("save-all flush")\n            srv.stop()` new
  `            srv.command("forceload remove 1024 1024")\n            srv.command("save-all flush")\n            srv.stop()`
  -> outcome unverified. `OK` means the test cannot tell a ticket held at stop from one removed just before stop,
  and the json still says `"ticket_held_at_stop": true` (a literal). A d 3 failure (`'features'` or other non-None)
  means the d 3 None assertion is what ties the test to the held ticket. Paste the full rays from the rewritten json
  before restoring it.

## N2.G3.C3 settle guard (green 295a8cb)
GREEN, 2 boots sequential, 1 slot: `python .../slot.py python lab/tests/test_guard_settle_invariance.py` (resident
112.4 s). Expected the two `fingerprint` lines with `positions 65536` AND `not_full 0` on both; `not_full 65536` on
both with `OK` is a vacuous pass: report it as a finding. Then `Ran 1 test`, `OK`.

Pure (Wilson ran G1): `window.box` over a missing region dir -> 65536 positions, 65536 None, fingerprints equal.
Decided by reading + G1, no boot, all SURVIVE:
- CA no load: old `            self.assertTrue(orderrun.wait_loaded(srv, 64, 64))` new `            pass` -> both boxes
  all None (chunk (64, 64) not on disk without a ticket), equal -> OK.
- CB region path: old `/ "world" / "region"` new `/ "world" / "regions"` -> both all None -> OK.
- CC no wait: old `                time.sleep(wait_s)` new `                time.sleep(0)` -> OK by construction (an
  equality guard cannot see that the wait did not happen; the test records no wait time).

Real positive control (2 boots, 1 slot):
- CP change during the wait: old `                time.sleep(wait_s)` new
  `                time.sleep(wait_s)\n                srv.command("setblock 1030 200 1030 minecraft:gold_block")`
  -> expected FAIL with `differing positions 1 changed 1 ...` and `pos (1030, 200, 1030) A 'minecraft:air' B
  'minecraft:gold_block'` (y 200 assumed air: unverified; any other A value still shows the read sees a change made
  after the wait). `OK` here means the guard cannot see changes made during the wait: finding.

Lead 3 (tile vs chunk): the guard proves equality for chunk (64, 64) only. The same read covers the tile with other
bounds: `window.box(region, (992, 0, 992), (1071, 255, 1071))` = chunks 62..66 x 62..66, 1,638,400 positions.
Probe G3 (Wilson, source world, chunks 6..10 x 10..14): 1,638,400 positions, 0 None, 14.3 s, tracemalloc peak 212 MB
per box. A tile guard needs no new reader, only new LO/HI (and two such boxes in memory, about 0.4 GB, or a
fingerprint per box before building the second). Whether 60 s changes blocks at d 1..2: unverified (not run).

## Real boots needed
GREEN: bench 1 run (1 slot, 1 + about 4 server processes), tile 1 boot, guard 2 boots. Mutants/probes: BE 1 run
(1 slot), TF 1 boot, CP 2 boots, V-C optional (both slots, 2 lanes). Total without V-C: 3 test runs GREEN + 3 mutant
runs, 1 slot each. Everything else is decided by H, G0-G3 or reading.
