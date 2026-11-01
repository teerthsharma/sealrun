# Verification plan, round 2 batch 8 (Wilson, 2026-11-01)

Read from: int/r2-b8 head 2ad4f55 = main 253c0f0 + res/N2.G2.C2 b6028ae (merge 8800168) + res/N2.G3.2.2 e1aff04
(merge 6a8ff8a) + res/N2.G3.2.3 df0e59b (merge 2ad4f55). `git diff --stat 253c0f0 2ad4f55`: 4 files, all new
(lab/tests/test_guard_setblock_edges.py, lab/tests/test_far_chunk.py, lab/tests/test_neighbour_partial.py,
lab/results/neighbour_status.json); lab/*.py unchanged. Contract: house/lab-api.md:177-186 ("Round 2, batch 8").
Pins: N2.G2.C2 b6028ae, N2.G3.2.2 e1aff04, N2.G3.2.3 df0e59b, int 2ad4f55. If `git rev-parse --short res/<gid>` or
`int/r2-b8` differs from the pin, stop and report.
Already run by Wilson on 2ad4f55 (Python 3.11.9), pure only: the probes quoted below; the pure guard
test_guard_chunk_status_full.py (`OK`); `python lab/tests/test_far_chunk.py` with no name (`Ran 0 tests`, `OK`).
Real-server tests: not run by Wilson. `git status --short` empty after Wilson's probes (plan file aside).

## Rules for residents
- Git Bash. One worktree per goal: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v8-<gid> 2ad4f55`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- Every real-server run goes through the slot holder, at most 2 real servers across ALL agents:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <test> <name> 2>&1; echo EXIT=$?`.
  slot.py waits up to 1200 s for one of `~/sealrun-lab/.slot1|.slot2` and prints `slot.py: holding .slotN`.
- Before each real run: `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"`
  must print >= 1500 (Wilson saw 5777 at plan time); below that, wait. Java PIDs before and after:
  `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears and stays after the run is
  a defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- Before and after each real run: `ls -A ~/sealrun-lab`. A `tmp*` folder present after and not before is a defect
  to report; if it holds `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- Always pass the test name for the far-chunk and neighbour files: their methods lack the `test_` prefix, and without
  the name they print `Ran 0 tests`, `OK`, `EXIT=0` (Wilson ran the far-chunk file). The setblock-edges method is
  `test_setblock_edges_read_back`, so that file runs without a name.
- test_neighbour_partial.py rewrites lab/results/neighbour_status.json on every run (test :62-63). After each run:
  `git diff lab/results/neighbour_status.json` (paste it), then `git checkout -- lab/results/neighbour_status.json`.
  The blob is LF, the working tree CRLF (core.autocrlf=true); git diff normalises, so only real changes show.
- Mutation: apply with the Edit tool (exact old/new below), run, expect the failure named, then
  `git checkout -- <every file touched>`, and `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.
- Report for each real run: printed lines, `Ran`/`OK`/`FAILED` lines, the failing line, EXIT, java PIDs before and
  after, free MB before, the slot number.

## Fixed facts the mutations rest on (pure probes by Wilson on 2ad4f55)
- Placed blocks (test_guard_setblock_edges.py:16-24), computed with anvil's own arithmetic:
  gold (15,80,3) chunk (0,0) sec 5 local x15 y0 z3 idx 63; diamond (16,80,3) chunk (1,0) idx 48; emerald (3,80,-1)
  chunk (0,-1), region r.0.-1 idx 243; lapis (3,80,0) chunk (0,0) idx 3; redstone (-17,64,-33) chunk (-2,-3),
  region r.-1.-1, sec 4, local x15 y0 z15 idx 255; iron (5,0,5) sec 0 idx 85; coal (5,255,5) sec 15, local y15,
  idx 3925. Six of seven have `y & 15 == 0`; only coal has a non-zero in-section y.
- `x >> 4 == x // 16`, `x & 15 == x % 16`, `x >> 5 == x // 32`, `x & 31 == x % 32` for every x in -5000..4999
  (probe printed True). Python's `//` and `%` floor, so those four mutants are equivalent: no boot.
- Truncating division differs on the negatives used: `int(-17/16) = -1` (floor -2), `int(-33/16) = -2` (floor -3),
  `int(-1/16) = 0` (floor -1); `abs(-17) & 15 = abs(-33) & 15 = abs(-1) & 15 = 1` (floor-mod 15).
- Far chunk (64,64): region (2,2), local (0,0) under both `& 31` and `& 15`; x == z.
- Source world, READ ONLY (C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1/world, seed 7, spawn 128 63 192):
  529 chunks on disk, all `"full"`, exactly x -3..19 by z 1..23 (23 x 23 around spawn chunk (8,12)); no other status
  on disk. Region files: r.0.0 3489792 B / 460 chunks, r.-1.0 434176 B / 69 chunks, and r.-1.-1, r.-1.1, r.0.-1,
  r.0.1 all 0 bytes / 0 chunks. Section order in a full chunk: Y -1 (no Palette), then 0..15 (all with Palette).
  logs/latest.log:37-46: `Done (9.966s)` then at once `Stopping server`, `Saving worlds`, `Saving chunks for level
  ...overworld`, `All chunks are saved` (so `stop` saves; the run had no `save-all`).
- anvil reads a 0-byte region file as empty: `present` reads `b""` (no cells), `chunk_data` gets offset 0 -> None.

## N2.G2.C2 setblock edges (green b6028ae)
Run: `python .../slot.py python lab/tests/test_guard_setblock_edges.py 2>&1; echo EXIT=$?` (1 boot; resident 24.9 s).
GREEN: seven `setblock ... -> '<reply with Changed the block>'` lines, seven `block_at <x> <y> <z> ->
'minecraft:<name>'` lines in the order gold, diamond, emerald, lapis, redstone, iron, coal, `Ran 1 test`, `OK`.
The loop stops at the first mismatch (:46-48), so each kill names only the first failing block.
Mutation S-A (x/z swap in the cell index), 1 boot: lab/anvil.py:67 old
`(y & 15) * 256 + (z & 15) * 16 + (x & 15)]` new `(y & 15) * 256 + (x & 15) * 16 + (z & 15)]` ->
`AssertionError: '<name>' != 'minecraft:gold_block'` at test_guard_setblock_edges.py:48 (reads idx 243 = world
(3,80,15)). Killers alone: gold, diamond, emerald, lapis. Blind: redstone (15,15), iron and coal (5,5).
Mutation S-B (chunk x/z swap), 1 boot: lab/anvil.py:61 old `    level = _level(region_dir, x >> 4, z >> 4)` new
`    level = _level(region_dir, z >> 4, x >> 4)` -> gold line correct, then
`AssertionError: '<name>' != 'minecraft:diamond_block'` at :48 (reads chunk (0,1), inside the source world's full
square, so a name is expected; `None` is equally a kill: report which). Killers alone: diamond, emerald, redstone.
Mutation S-C, S-E (`x >> 4` -> `x // 16` at :61; `& 15` -> `% 16` at :67; `>> 5`/`& 31` at :48/:51): equivalent by
the probe above. No boot. They SURVIVE by construction; listed so nobody spends a boot on them.
Mutation S-D (truncating chunk division), 1 boot: lab/anvil.py:61 old `x >> 4, z >> 4)` new
`int(x / 16), int(z / 16))` -> gold, diamond correct, then `AssertionError: '<name>' != 'minecraft:emerald_block'`
at :48 (chunk (0,0) instead of (0,-1)).
Mutation S-D2 (same, emerald removed), 1 boot: S-D plus delete lab/tests/test_guard_setblock_edges.py:19
`    (3, 80, -1, "emerald_block"),` -> `AssertionError: <None or a name> != 'minecraft:redstone_block'` at :48
(reads chunk (-1,-2)); only the negative-coordinate block can catch this alone. Restore both files.
Mutation S-F (floor-mod replaced on negatives), 1 boot: lab/anvil.py:67 old `(z & 15) * 16` new
`(abs(z) & 15) * 16` -> `AssertionError: '<name>' != 'minecraft:emerald_block'` at :48 (local z 1, not 15).
Killers alone: emerald (z -1), redstone (z -33).
Mutation S-G (in-section y stride), 1 boot: lab/anvil.py:67 old `(y & 15) * 256` new `(y & 15) * 16` -> six
correct `block_at` lines, then `AssertionError: '<name>' != 'minecraft:coal_block'` at :48 (idx 325 = world
(5,1,4)). Only coal (y 255) catches any change to the y-within-section term.
Mutation S-H1 (top section dropped), 1 boot: lab/anvil.py:64 old `    for section in level.get("Sections", []):` new
`    for section in level.get("Sections", [])[:-1]:` -> `AssertionError: 'minecraft:air' != 'minecraft:coal_block'`
at :48 after six correct lines (rests on the section order -1..15 seen in the source world; order in the scratch
world unverified: report).
Mutation S-H2 (bottom block section dropped), 1 boot: same line, new `    for section in level.get("Sections", [])[2:]:`
-> `AssertionError: 'minecraft:air' != 'minecraft:iron_block'` at :48 after five correct lines (Y -1 and Y 0
skipped). Variant `[1:]` (skips only the palette-less Y -1) is expected to SURVIVE; not booted.
Mutation S-I (status check removed; expected to SURVIVE), 1 boot: lab/anvil.py:62 old
`    if level is None or level.get("Status") != "full":` new `    if level is None:` -> expected `OK` (all four
loaded chunks are full). Report OK or not. The pure guard test_guard_chunk_status_full.py:79 covers this branch.
Mutation S-J (flush removed; expected to SURVIVE), 1 boot: delete lab/tests/test_guard_setblock_edges.py:40
`            srv.command("save-all flush")` -> expected `OK` (`stop` saves: source latest.log:39-46).
Mutation S-K (read while the server runs; probe, outcome unverified), 1 boot: delete :41 `            srv.stop()`
(finally :50-51 still stops) -> report `OK`, a mismatch, or an ERROR. A `PermissionError` traceback in
anvil.py:9 or :19 means Windows sharing refuses the read while java holds the file; `OK` means a reader after
`save-all flush` sees every block without a stop.
Mutation S-L (no wait for load; probe, outcome unverified), 1 boot: lab/orderrun.py:75 old `    waited = 0.0` new
`    return True` -> expected `AssertionError: 'Changed the block' not found in '<reply>'` at :39 on gold (chunk
(0,0) lies outside the 23 x 23 spawn square); report the reply text verbatim.
Not booted, SURVIVES by reading: removing `and "Palette" in section` (anvil.py:65), since no placed y has
`y >> 4` in {-1, 16}; `srv.stop()`'s exit code is never checked (:41), so a stop that hits the 30 s grace and is
killed (procs.py:8-11) still reads whatever was flushed.

## N2.G3.2.2 far chunk (green e1aff04)
Run: `python .../slot.py python lab/tests/test_far_chunk.py Lab.far_chunk_absent_before_and_full_after_forceload
2>&1; echo EXIT=$?` (1 boot; resident 21.7 s). GREEN: `before chunk (64, 64) -> None`,
`spawn (128, 192) distance 56 chunks`, `after chunk (64, 64) -> 'full'`, `Ran 1 test`, `OK`.
Mutation F-A (forceload before the "before" read; also the open-file read probe), 1 boot: lab/tests/test_far_chunk.py:30-31 old
`            srv.command("save-all flush")` + newline + `            before = anvil.chunk_status(region, cx, cz)` new
`            self.assertTrue(orderrun.wait_loaded(srv, cx, cz))` + newline + the two old lines ->
`AssertionError: 'full' is not None` at :34. This reads r.2.2.mca while java holds it: a `PermissionError` traceback
instead is the sharing answer to lead 3 (report which).
Mutation F-B (region name), 1 boot: lab/anvil.py:48 old `f"r.{cx >> 5}.{cz >> 5}.mca"` new
`f"r.{cx >> 4}.{cz >> 4}.mca"` -> `before ... None` (passes), then `AssertionError: None != 'full'` at :47.
Mutation F-C (forceload removed), 1 boot: delete lab/orderrun.py:74 `    client.command(f"forceload add {x} {z}")` ->
after ~30 s, `AssertionError: False is not true` at :41.
Mutation F-D (no wait; probe, outcome unverified), 1 boot: lab/orderrun.py:75 old `    waited = 0.0` new
`    return True` -> report the `after` line verbatim (None, a partial status, or 'full'); also input to lead 4.
Mutation F-E (flush before stop removed; expected to SURVIVE), 1 boot: delete :42 `            srv.command("save-all flush")`
-> expected `OK`.
Not booted, SURVIVE by arithmetic or reading (Gaps): any x/z swap (anvil.py:48, :51, :56, :61; x == z == 64);
`cx & 31` -> `cx & 15` at :51 and `lx + 32 * lz` -> `32 * lx + lz` at :20 (local (0,0) either way);
`spawn_x >> 4` -> `spawn_x` at test :37 (896 >= 50) and `max` -> `min` (52 >= 50); `chunk_status` returning the
constant "full" for any present chunk (anvil.py:57; before is None from the file test, after is "full"). That last
mutant IS killed by the pure guard: Wilson patched `anvil.chunk_status` to return "full" for any present chunk and
ran test_guard_chunk_status_full.py -> `AssertionError: 'full' != 'features'` at :78, `FAILED (failures=1)`.

## N2.G3.2.3 neighbour status (RED df0e59b; verify the measurement, not the assertion)
Run V1 (re-measure), 1 boot: `python .../slot.py python lab/tests/test_neighbour_partial.py
Lab.neighbour_of_full_chunk_is_not_yet_full 2>&1; echo EXIT=$?`. Expected: 39 `<label> d=<d> ...` lines,
`AssertionError: 'full' == 'full'` at test_neighbour_partial.py:66, `FAILED (failures=1)`, EXIT=1;
`git diff lab/results/neighbour_status.json` shows only the `"when"` line. Any other changed line is a
non-reproduction: paste it. Restore the file.
Run V2 / V3 (wait 0 s and 60 s, lead 4), 1 boot each: lab/tests/test_neighbour_partial.py:20 old `WAIT_SECS = 10`
new `WAIT_SECS = 0` (V2), `WAIT_SECS = 60` (V3). Paste the 39 lines and the json diff of each. Restore the file and
the json after each.
Run V4 (diagnostic, leads 2 and 3), 1 boot: save this as `<your scratchpad>/b8_probe.py` (outside the repo), run from
the worktree root as `python .../slot.py python <your scratchpad>/b8_probe.py 2>&1; echo EXIT=$?`:

```python
import sys, time
from pathlib import Path
sys.path.insert(0, "lab")
import anvil, orderrun, server, serverdir

SRC = Path("C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1")
ROOT = Path.home() / "sealrun-lab"

def show(tag, region):
    for f in sorted(region.glob("*.mca")):
        try:
            cells = anvil.present(f)
            rx, rz = map(int, f.name.split(".")[1:3])
            st = {}
            for lx, lz in cells:
                s = anvil.chunk_status(region, rx * 32 + lx, rz * 32 + lz)
                st[s] = st.get(s, 0) + 1
            print(tag, f.name, f.stat().st_size, len(cells), st)
        except OSError as e:
            print(tag, f.name, "ERROR", repr(e))

scratch = serverdir.make_scratch(SRC, ROOT)
srv = None
try:
    srv = server.boot(scratch)
    region = scratch["dir"] / "world" / "region"
    srv.command("save-all flush")
    show("boot", region)
    print("loaded", orderrun.wait_loaded(srv, 64, 64))
    time.sleep(10)
    srv.command("save-all flush")
    show("flush", region)
    print("remove", repr(srv.command("forceload remove 1024 1024")))
    time.sleep(60)
    srv.command("save-all flush")
    srv.stop()
    show("stop", region)
    print("east", [anvil.chunk_status(region, 64 + d, 64) for d in range(13)])
finally:
    if srv is not None:
        srv.stop()
    serverdir.remove(scratch["dir"])
```
Read V4 as: `boot` lines say whether r.2.2.mca exists (and its size) before any forceload, the exact state the
far-chunk "before" read sees (lead 3). `flush` lines are read while java holds the files: any `ERROR` line is a
sharing refusal; none means reads work while it runs. Paste the chunk count and statuses of r.2.2, r.2.1, r.1.2,
r.1.1 from `flush`: 25 full chunks around (64,64) matches the committed rays (d <= 2), any other count is the tile
the rays did not show. `stop`
after the ticket is gone: any status other than `full` on disk, or `east` d >= 3 not None, means those chunks were
generated and are written on unload but not by `save-all flush` (lead 2 separated, "not saved"). `east` still None
at d >= 3 with only `full` on disk does NOT separate the two.

## Leads
1. Mutations killed / surviving. Setblock edges kills: index x/z swap (S-A, four killers), chunk x/z swap (S-B,
   three killers), truncating division (S-D: emerald; S-D2: redstone alone), abs-mod (S-F: emerald, redstone), the
   in-section y term (S-G, coal alone), top or bottom section skipped (S-H1 coal, S-H2 iron). It does NOT kill: `//`
   and `% 16` (equivalent, probe), the status check (S-I), the Palette guard, a dropped flush (S-J). Read-before-stop
   (S-K) and no-wait (S-L) are probes. Far chunk kills: forceload before the before read (F-A), region name (F-B),
   no forceload (F-C). It does NOT kill any x/z swap, any local-index error, the status string (pure guard does),
   a dropped flush (F-E), or a distance computed in blocks. Its only distinctive coverage over the setblock test is
   region file r.2.2 at a far coordinate and the absent-before branch.
2. "None at distance 3" means not on disk after `save-all flush` + `stop` (anvil.py:47-52: no file, or header
   offset 0). It is NOT evidence the chunk was never generated. Verified evidence from the source world (read only):
   a boot+stop with no save-all left 0-byte region files r.0.-1, r.0.1, r.-1.-1, r.-1.1 (the server opened regions
   beyond the 23 x 23 full square, z <= -1 and z >= 32) and saved only `"full"` chunks; so on this server the stop
   path wrote nothing but full chunks even where it touched region files. Why (which chunks are generated as partial
   chunks, and whether flush or unload writes them): unverified, server internals, not in the repo. The separating
   probe with vanilla commands only is V4: `forceload remove 1024 1024`, wait 60 s, `save-all flush`, `stop`; a
   non-full status on disk then shows "generated, not saved by flush". It separates in one direction only: if nothing
   new appears, unload may also skip partial chunks (unverified). No vanilla command in the repo reads a non-full
   chunk: `execute if block` is used only for a loaded one (orderrun.py:77).
3. The far-chunk "before" read cannot be a Windows-sharing artefact. It calls chunk_status -> _level, which first
   checks `path.is_file()` on r.2.2.mca (anvil.py:48-50) and opens it read-only only if present (:19). A sharing
   refusal would raise `PermissionError` (test ERROR), never return None; a 0-byte or chunk-less file returns None
   from the header (:21-23). So None means "r.2.2.mca absent, empty, or no offset for local (0,0)" at that moment.
   Which of the three: unverified; V4's `boot` lines show it. Whether java's open of r.2.2.mca lets Python read it
   while running: unverified; F-A, S-K and V4 `flush` each test it.
4. The 10 s wait: unverified whether load-bearing. wait_loaded returns as soon as `execute if block 1024 0 1024
   minecraft:bedrock` passes (orderrun.py:77), i.e. the centre is loaded; the 10 s then runs (test :33), then flush
   and stop, and stop itself saves (source latest.log:41-46), so the effective window is 10 s + stop. V2 (0 s) and
   V3 (60 s) answer it, each 1 boot. Same tile at 0, 10 and 60 = not load-bearing.

## Gaps (mutants that survive)
- test_guard_setblock_edges.py: the status check (anvil.py:62) and the Palette guard (:65) are never exercised (all
  chunks full; no y in sections -1 or 16); a missing `save-all flush` (:40) is hidden by `stop` saving; the exit
  code of `srv.stop()` (:41) is not checked. The in-section y term is guarded by coal alone and section 0 by iron
  alone; dropping either line from PLACED leaves S-G or S-H2 alive.
- test_far_chunk.py: chunk (64,64) is x/z-symmetric and region-local (0,0), so every x/z swap and every local-index
  or header-offset mutant in anvil.py:20, :48, :51, :56 survives (arithmetic above). The status is read only as
  "full" or None; `chunk_status` returning "full" for any present chunk survives here (the pure guard :78 kills it).
  `distance >= 50` (:39) also holds for a distance computed in blocks or with `min`.
- test_far_chunk.py:30-33: the "before" assertion shows only that nothing is on disk for (64,64); it does not show
  the chunk is ungenerated, and nothing records whether r.2.2.mca existed.
- test_neighbour_partial.py: rays only (+x, -z, +x+z), 13 points each; the 5 x 5 tile is inferred, not read; chunks
  west and south of (64,64) are never read. `"ticket"` in the json (:6) is the constant TICKET typed in the test
  (:19), not read back from the server (it matches wait_loaded's `forceload add 1024 1024` by arithmetic,
  orderrun.py:73-74).

## Findings
1. lab/results/neighbour_status.json with test_neighbour_partial.py:65-66: on 2ad4f55's data, chunks at Chebyshev
   distance 0, 1, 2 from forceloaded (64,64) are `"full"` on all three rays and 3..12 are null (not on disk). Input:
   one run at 2026-11-01T09:30:05+05:30 (:8), wait 10 s. Result: the bound "distance 1 is not full" (:66) is refuted
   by the data; leap n2-L1's distance 1 and 2 = full matches, its distance 3 "not full" is consistent but null is
   "not on disk", not a status (lead 2). The tile `full` at d <= 2 is the measured fact to bind.
2. Provenance count: df0e59b's message says the json is the "second of two runs"; the brief to Wilson says three
   identical runs. The file holds one `when` and nothing on how many runs agreed. Which is right: unverified; V1
   adds one independent run.
3. lab/tests/test_neighbour_partial.py is merged into int/r2-b8 RED by design (contract lab-api.md:183: a finding,
   never bent). Input: the resident's runs (df0e59b message: fails at the assertNotEqual for (65,64)). Result: it
   fails at :66 while the data stand, so any run of all lab tests
   on this branch carries one known failure; the method lacks `test_`, so a plain `python -m unittest discover`
   does not collect it (unverified for the House harness).

## Real boots this plan needs
Setblock edges: GREEN 1 + S-A, S-B, S-D, S-D2, S-F, S-G, S-H1, S-H2, S-I, S-J, S-K, S-L = 13.
Far chunk: GREEN 1 + F-A, F-B, F-C, F-D, F-E = 6. Neighbour: V1, V2, V3, V4 = 4. Total 23 boots, each through
slot.py (2 slots). Zero-boot items: S-C/S-E equivalents, Palette guard, far-chunk arithmetic survivors, status
constant (pure guard, already run by Wilson).
