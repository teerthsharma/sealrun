# Verification plan, round 2 batch 9 (Wilson, 2026-11-01)

Read from: int/r2-b9 head fd54573 = main 6efed06 + res/N2.G3.2.4 c514ad6 (merge fd54573). `git diff --stat 6efed06
fd54573`: 2 files changed, 50 insertions (lab/orderrun.py +20: `run_order` at :21-34; lab/tests/test_run_order.py
new, 30 lines). Contract: house/lab-api.md:187-194 (Finding n2-F1, the 5x5 tile, and the run_order bullet).
Pins: N2.G3.2.4 c514ad6, int fd54573, main 6efed06. If `git rev-parse --short res/N2.G3.2.4` or `int/r2-b9` differs,
stop and report.
Already run by Wilson on fd54573 (Python 3.11.9), pure only: the probes quoted below; `python
lab/tests/test_run_order.py` with no name (`Ran 0 tests in 0.000s`, `OK`). Real-server tests: not run by Wilson.
`git status --short` empty after Wilson's probes (plan file aside). Free RAM at plan time: 4518 MB.

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v9-N2.G3.2.4 fd54573`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- Every real-server run goes through the slot holder, at most 2 real servers across ALL agents:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <test or probe> <name> > <your scratchpad>/<run>.txt 2>&1; echo EXIT=$?`
  then paste `grep -nE "slot.py|->|^Ran|^OK|FAILED|Error|line [0-9]+" <your scratchpad>/<run>.txt` and
  `head -c 600` of any AssertionError line. Redirect is required: `assertNotIn(None, blocks.values())` (test :22)
  prints the full repr of 131072 values when it fails (unittest `safe_repr`, short=False), megabytes of output.
- Before each real run: `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"`
  must print >= 1500; below that, wait. Java PIDs before and after:
  `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears and stays after the run is a
  defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- Before and after each real run: `ls -A ~/sealrun-lab`. A `tmp*` folder present after and not before is a defect to
  report; if it holds `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- Always pass the test name: the method lacks the `test_` prefix, and without it the file prints `Ran 0 tests`, `OK`,
  EXIT=0 (Wilson ran it). Name: `Lab.run_order_returns_window_for_two_chunks`.
- Mutation: apply with the Edit tool (exact old/new below, all in lab/orderrun.py unless named), run, expect the
  failure named, then `git checkout -- lab/orderrun.py`, and `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.
- Report for each real run: printed lines, `Ran`/`OK`/`FAILED` lines, the failing line, EXIT, java PIDs before and
  after, free MB before, the slot number, wall seconds.

## Fixed facts the mutations rest on (pure probes by Wilson on fd54573)
- Order [(64, 64), (65, 64)] (test :20): mocked boot, empty region dir -> `len 131072`, min key `(1024, 0, 1024)`, max
  key `(1055, 255, 1039)`, commands sent in order `forceload add 1024 1024`, `execute if block 1024 0 1024
  minecraft:bedrock`, `save-all flush`, `forceload add 1040 1024`, `execute if block 1040 0 1024 minecraft:bedrock`,
  `save-all flush`, `stop` called once. 131072 = 2 chunks x 16 x 16 x 256.
- `len(blocks)` does not depend on disk: window.box (window.py:21-29) writes every (x, y, z) of the box whether the
  chunk is present or not. So every mutant that changes only the box size is decided by the pure probe below; a
  boot adds nothing.
- window.box None semantics (probe; source world read only, C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1/world/region):
  box over full chunk (8, 12) -> 0 None of 65536; absent chunk (30, 30) -> 65536 None of 65536; chunks 19..20 at
  z 12 (19 full, 20 absent) -> 65536 None of 131072; `anvil._level` patched to `{"Status": "features"}` -> 65536 of
  65536 None; patched to `{"Status": "full"}` with no Sections -> 0 None, every value `'minecraft:air'`.
- Scratch worlds are generated fresh: `serverdir.make_scratch` copies only server.jar and eula.txt and writes
  server.properties (serverdir.py:42-58); no world folder is copied. Source server.properties: `level-seed=7`,
  `view-distance=4`, `level-type=default`.
- Mocked `wait_loaded` returning False (snippet M below) on the original: `RuntimeError('chunk (64, 64) did not load')`,
  `stops 1`.

Pure mock snippet M (run from the worktree root, no server, no slot):
```
python -c "
import sys, tempfile; from pathlib import Path; sys.path.insert(0, 'lab')
import orderrun
class S:
    stops = 0
    def command(self, t): return 'Test passed'
    def stop(self, grace=30.0): S.stops += 1; return 0
orderrun.server.boot = lambda s: S()
orderrun.wait_loaded = lambda c, cx, cz: False
with tempfile.TemporaryDirectory() as d:
    try: print('returned', len(orderrun.run_order({'dir': Path(d)}, [(64, 64), (65, 64)])))
    except RuntimeError as e: print(repr(e))
print('stops', S.stops)
"
```
Pure size snippet Z (same, but with `orderrun.wait_loaded = lambda c, cx, cz: True` and printing
`len(...)`): original prints `returned 131072`.

## N2.G3.2.4 run_order (green c514ad6)
Run GREEN, 1 boot: `python .../slot.py python lab/tests/test_run_order.py Lab.run_order_returns_window_for_two_chunks`
(resident 28.7 s). Expected: three lines `(1024, 0, 1024) -> 'minecraft:bedrock'` (y 0 is what wait_loaded probes,
orderrun.py:13), `(1040, 64, 1024) -> '<name>'`, `(1055, 255, 1039) -> '<name>'` (names other than bedrock
unverified: paste them), `Ran 1 test`, `OK`.

Pure mutants (no boot; Wilson ran each in memory on a copy of the source text, results below; residents re-run with
Edit + snippet M or Z, then restore):
- R-A (no stop on error): old
  `    try:\n        for cx, cz in order:\n            if not wait_loaded(srv, cx, cz):\n                raise RuntimeError(f"chunk ({cx}, {cz}) did not load")\n            srv.command("save-all flush")\n    finally:\n        srv.stop()`
  new
  `    for cx, cz in order:\n        if not wait_loaded(srv, cx, cz):\n            raise RuntimeError(f"chunk ({cx}, {cz}) did not load")\n        srv.command("save-all flush")\n    srv.stop()`
  -> M prints `RuntimeError('chunk (64, 64) did not load')`, `stops 0` (killed by M). The bound test SURVIVES: on
  the success path R-A is identical (len 131072, 6 commands, 1 stop).
- R-B (no RuntimeError): old `            if not wait_loaded(srv, cx, cz):\n                raise RuntimeError(f"chunk ({cx}, {cz}) did not load")`
  new `            wait_loaded(srv, cx, cz)` -> M prints `returned 131072`, `stops 1` (killed by M). Bound test SURVIVES.
- R-C x end +16: old `max(xs) * 16 + 15` new `max(xs) * 16 + 16` -> Z `returned 135168`; bound test fails
  `AssertionError: 135168 != 131072` at test_run_order.py:21. R-C2 `+ 14` -> 126976, same line.
- R-D z end: old `max(zs) * 16 + 15` new `max(zs) * 16 + 16` -> 139264; `+ 14` -> 122880; both fail at :21.
- R-E y range: old `15, 255, max` new `15, 256, max` -> 131584; `15, 254, max` -> 130560; old `min(xs) * 16, 0, min`
  new `min(xs) * 16, 1, min` -> 130560; all fail at :21.
- R-F x min/max swap: old `lo = (min(xs) * 16, 0, min(zs) * 16)\n    hi = (max(xs) * 16 + 15` new
  `lo = (max(xs) * 16, 0, min(zs) * 16)\n    hi = (min(xs) * 16 + 15` -> 0; fails `0 != 131072` at :21.
- R-F2 z min/max swap: old `0, min(zs) * 16)\n    hi = (max(xs) * 16 + 15, 255, max(zs)` new
  `0, max(zs) * 16)\n    hi = (max(xs) * 16 + 15, 255, min(zs)` -> 131072; SURVIVES by arithmetic (both z are 64).
  No boot.
- R-H region path: old `/ "world" / "region"` new `/ "world" / "regions"` -> no such dir, `anvil._level` returns None
  for every chunk (anvil.py:48-50), so every value is None; bound test fails at :22. Decided by reading; no boot.

Real-server mutants:
- R-M (no tickets; the live check that :22 can fail on real data), 1 boot: old `        for cx, cz in order:` new
  `        for cx, cz in []:` -> expected `AssertionError: None unexpectedly found in dict_values(...` at :22 (chunk
  (64, 64) is 56 chunks from spawn and not on disk without a ticket: b8 far-chunk GREEN `before chunk (64, 64) -> None`).
  `OK` here would mean the scratch world already holds (64, 64): report it.
- R-I (no flush; expected to SURVIVE), 1 boot: delete orderrun.py:27 `            srv.command("save-all flush")` ->
  expected `OK` (`stop` saves: b8 source latest.log:39-46).
- R-K (read while java runs; probe, outcome unverified), 1 boot: old
  `            srv.command("save-all flush")\n    finally:` new
  `            srv.command("save-all flush")\n        xs = [cx for cx, _ in order]\n        zs = [cz for _, cz in order]\n        return window.box(Path(scratch["dir"]) / "world" / "region", (min(xs) * 16, 0, min(zs) * 16), (max(xs) * 16 + 15, 255, max(zs) * 16 + 15))\n    finally:`
  -> report `OK`, a :22 failure, or an ERROR. A `PermissionError` traceback in anvil.py:9 or :19 is the Windows
  sharing answer; `OK` means a read after `save-all flush` sees both chunks full without a stop.
- R-G (x/z lists swapped; expected to SURVIVE, probe of the tile in +z), 1 boot: old
  `    xs = [cx for cx, _ in order]\n    zs = [cz for _, cz in order]` new
  `    xs = [cz for _, cz in order]\n    zs = [cx for cx, _ in order]` -> box becomes chunks (64, 64) and (64, 65), still
  131072 (pure probe). (64, 65) is never ticketed; it is at +z distance 1, a direction n2-F1 never measured (rays +x,
  -z, +x+z). Expected `OK`; a :22 failure is a finding that the tile is not symmetric.
- R-L2 (last ticket only; expected to SURVIVE, probe of the tile in -x), 1 boot: old `        for cx, cz in order:`
  new `        for cx, cz in order[-1:]:` -> only (65, 64) ticketed; (64, 64) is at -x distance 1, unmeasured. Expected
  `OK`; a :22 failure is a finding. The `order[:1]` variant (+x distance 1, measured full in n2-F1) SURVIVES by
  that measurement; not booted.

Control V1 (noise floor for this window; input to lead 2), 2 boots: save as `<your scratchpad>/b9_repeat.py`, run
from the worktree root twice, each as `python .../slot.py python <your scratchpad>/b9_repeat.py > <scratchpad>/v1_<n>.txt 2>&1; echo EXIT=$?`:
```python
import sys, json, time
from pathlib import Path
sys.path.insert(0, "lab")
import orderrun, serverdir, window

SRC = Path("C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1")
ROOT = Path.home() / "sealrun-lab"
scratch = serverdir.make_scratch(SRC, ROOT)
try:
    t0 = time.monotonic()
    blocks = orderrun.run_order(scratch, [(64, 64), (65, 64)])
    print("secs", round(time.monotonic() - t0, 1), "nones", sum(v is None for v in blocks.values()))
    print("fingerprint", window.fingerprint(blocks))
    out = Path(sys.argv[0]).with_name(f"v1_{int(time.time())}.json")
    out.write_text(json.dumps({f"{x} {y} {z}": n for (x, y, z), n in blocks.items()}))
    print("saved", out)
finally:
    serverdir.remove(scratch["dir"])
```
Read V1 as: equal fingerprints = no run-to-run difference in this window at this run length (one pair, not a rate).
Different = a non-generation difference exists; paste the count of differing keys and up to 10 `pos old new` lines
(compare the two saved json files with a one-line python dict comparison). Delete the json files after.

## Leads
1. Mutations. The bound test kills: every box-size error (R-C, R-D, R-E, R-F x swap) at :21, decided purely because
   len does not read disk; a wrong region path (R-H) and no tickets (R-M) at :22. It does NOT kill: missing stop on
   error (R-A) and no RuntimeError (R-B), since both chunks load in the bound run (the error path never runs); snippet
   M kills both without a server. It does NOT kill: z min/max swap (R-F2, both z = 64), x/z list swap (R-G, expected:
   (64, 65) full), a dropped flush (R-I, expected: stop saves), dropping every ticket but one (R-L, R-L2, expected:
   the tile). Read before stop (R-K) is a probe. Real boots for this lead: R-M, R-I, R-K, R-G, R-L2.
2. Downstream (N2.G3.C6, N2.G3.4.A3: the 4 chunks of `orders.square(cx, cz)` in different orders):
   - Verified by reading: every chunk of a 2x2 square is at Chebyshev distance <= 1 from every other, so under n2-F1
     (d <= 2 full, lab-api.md:187-189) the FIRST ticket makes all four window chunks full and the other three tickets
     build nothing inside the window. Orders of one square therefore differ inside the window only through which
     chunk is first; that is the basis of "4 first-chunk classes". Directions -x, +z, -x-z, +x-z, -x+z of the tile are
     unmeasured (R-G, R-L2 probe two of them).
   - Verified by reading: the bounding box of a full 2x2 square is exactly the 4 listed chunks (orderrun.py:30-34;
     pure probe: (-64, 64) and (64, -64) squares give 262144 positions, min/max keys at the square corners). Each is
     ticketed, so each is full by the end; "window includes chunks that are not full" does not arise for a full
     square. For a non-rectangular order list it does: the box covers unlisted chunks (orderrun.py:32-33).
   - Verified by reading: every order sends the same number of commands (one forceload, >= 1 bedrock poll, one
     `save-all flush` per chunk) and ends with all four tickets held; nothing is removed before stop
     (orderrun.py:24-29). Flushes between tickets change timing only; whether `save-all flush` alters block content:
     unverified (server internals).
   - Verified by reading: run_order never deletes the world (orderrun.py:21-34). Two runs on ONE scratch differ for a
     non-generation reason (the second finds the chunks already on disk). Each run needs its own make_scratch.
   - Unverified: block changes from ticking between the first load and stop (fluid flow from springs, falling
     blocks, random ticks if forceloaded chunks get them without a player in 1.16.1, weather). Elapsed time per run
     is not fixed (wait_loaded polls 0.5 s up to 30 s, orderrun.py:8-18). V1 separates this from order: a non-zero
     repeat diff is the noise floor that verdict.py requires (`control.repeat_diff`, test_guard_noise_floor_first.py).
   - Unverified: whether generation of chunks outside the first tile by later tickets can write into window chunks
     (feature placement across chunk borders; server internals, not in the repo). Under the 3x3 feature-write rule
     from memory it cannot, since window chunks' neighbours are all within the first tile; not checked here.
   - Verified by reading: `Server.stop` waits 30 s, then `taskkill /PID /T /F` (procs.py:7-11); run_order ignores the
     exit code (orderrun.py:29). A killed stop after the last flush loses nothing flushed; data written after it is
     unverified.
3. window.box returns None exactly for positions in chunks that are not on disk or whose `Status` is not `"full"`
   (window.py:23-25, :29), and for all 65536 positions of such a chunk at once (probes above). A full chunk with a
   missing section gives `'minecraft:air'`, never None. So `assertNotIn(None, ...)` (test :22) is meaningful as
   "every chunk in the box is on disk and full after stop"; it says nothing about which blocks are there. R-M and R-H
   are the mutants it alone kills.

## Gaps (mutants that survive)
- The error path (orderrun.py:25-26) and the always-stop path (:28-29) are never run by the bound test; snippet M is
  the only check, and it is not a committed test.
- Order [(64, 64), (65, 64)] has equal z, so a z min/max swap survives; chunk (64, 64) to (65, 64) along +x only, so
  an x/z list swap survives if (64, 65) is full (R-G).
- Block content is printed (test :23-24), never asserted; any mutant that reads a different full chunk of the right
  size passes.
- A dropped flush is hidden by `stop` saving (R-I expected); only one ticket per tile matters, so dropping all but one
  ticket survives (R-L, R-L2 expected).
- `srv.stop()`'s return value is never checked (orderrun.py:29).

## Findings
1. lab/orderrun.py:21-34 matches the contract bullet lab-api.md:190-194 on every point read: boot, per chunk
   wait_loaded with RuntimeError naming the chunk (:25-26, M output `RuntimeError('chunk (64, 64) did not load')`),
   `save-all flush` (:27), stop in `finally` (:28-29, M output `stops 1`), box over the listed chunks y 0..255 (:30-34,
   pure probe min `(1024, 0, 1024)` max `(1055, 255, 1039)`, 131072 positions).
2. lab/tests/test_run_order.py:16: method lacks `test_`; `python lab/tests/test_run_order.py` prints `Ran 0 tests in
   0.000s`, `OK`. A plain discover does not collect it (same as b8's far-chunk and neighbour files).
3. lab/tests/test_run_order.py:22: on failure the assertion message carries the repr of all 131072 values; any log
   that captures it unfiltered gets megabytes.

## Real boots this plan needs
GREEN 1 + R-M, R-I, R-K, R-G, R-L2 (5) + V1 2 = 8 boots, each through slot.py (2 slots). Zero-boot items: R-A, R-B
(snippet M), R-C..R-F2 (snippet Z / arithmetic), R-H and R-L (reading).
