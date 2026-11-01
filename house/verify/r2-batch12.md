# Verification plan, round 2 batch 12 (Wilson, 2026-11-01)

Read from: int/r2-b12 head 60b6675 = main f2eda1c + contract 07c1a1e (house/lab-api.md:232-245) + res/N2.G3.5.2
60b6675. `git diff --stat f2eda1c 60b6675`: 3 files, 357 insertions (house/lab-api.md 15, lab/results/order_edit.json
228, lab/tests/test_order_edit.py 114). Pins: contract 07c1a1e, res 60b6675, int 60b6675. If
`git rev-parse --short int/r2-b12` differs, stop and report.
Already run by Wilson on 60b6675 (Python 3.11.9), pure only: `python lab/tests/test_order_edit.py` with no name
(`Ran 0 tests`, `OK`); probes P1-P3 below; the probe scripts through the fake driver F (no java). Real servers: none
booted by Wilson. At plan time: free RAM 1718 MB, one java.exe (PID 32540, not Wilson's), `~/sealrun-lab` holds
`.slot1` and `tmpteim1925` (not Wilson's).

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v12-<gid> 60b6675`, work there, run everything from its root, remove it
  when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- Every real-server run goes through the slot holder, at most 2 real servers across ALL agents, one server per run:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python <test or probe> <args> > <your scratchpad>/<run>.txt 2>&1; echo EXIT=$?`
  Paste `grep -nE "slot.py|fingerprint|^arm|^diff|^Ran|^OK|FAILED|Error|line [0-9]+" <run>.txt` and `head -c 600` of
  any AssertionError line.
- The effect under test is timing. Run the probes of one resident one after another, never two of yours at once.
  Every probe line records `other_java` (java.exe count at its start); a run with `other_java` > 0 is still valid but
  say so next to its result.
- Free RAM before each real run: `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"`
  must print >= 1500; below that, wait (server.py:98 refuses the boot anyway).
- Java PIDs before and after: `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears
  and stays after the run is a defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- `ls -A ~/sealrun-lab` before and after. A `tmp*` folder present after and not before is a defect to report; if it
  holds `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- The test method lacks `test_` (test :63): always pass `Lab.edits_before_neighbour_change_cells_outside_edit`.
  Without it the file prints `Ran 0 tests`, `OK`, EXIT=0 (Wilson ran it).
- The test rewrites the tracked `lab/results/order_edit.json` (test :84-100) on every run. After each test run:
  `git diff --stat lab/results/order_edit.json`, paste `python -c "import json;d=json.load(open('lab/results/order_edit.json'));print({k:v for k,v in d.items() if k!='examples_outside'})"`,
  then `git checkout -- lab/results/order_edit.json`.
- Mutation: apply with the Edit tool (exact old/new below), run, expect the result named, then `git checkout -- <file>`;
  `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.
- Report for each real run: printed lines, `Ran`/`OK`/`FAILED`, the failing line, EXIT, java PIDs before and after,
  free MB before, the slot number, wall seconds.

## Fixed facts (read by Wilson on 60b6675)
- Arms (test :39-59): both arms boot a fresh scratch copy, `wait_loaded(A)` (:44), edited arm only the 64 lines of
  `edits.commands(EDIT, A_TILE)` (:46-50), `wait_loaded(B)` (:51), `save-all flush` (:53), stop (:54), `window.box`
  (:55). The plain arm sends 5 RCON commands before stop, the edited arm 69 (driver F counts 5 and 69). Nothing waits
  between A's bedrock answer and B's `forceload add` except, in the edited arm, the 64 setblock round trips; no
  `save-all flush` and no tile check after A, unlike `orderrun.run_order` (orderrun.py:24-28: flush after each wait).
  The arms differ in two things at once: the edit and the A-to-B delay. The test cannot separate them.
- `wait_loaded` (orderrun.py:8-18) adds a forceload ticket at the chunk origin and polls
  `execute if block <x> 0 <z> minecraft:bedrock` until `Test passed`: it checks chunk A only, not A's 5x5 tile.
- Edit: 64 cells x 1068..1071, y 30..33, z 1024..1027, all in chunk (66, 64) (P1), inside A_TILE (62..66 x 62..66).
  `edits.commands` raises `ValueError chunk (68, 64) is not loaded` for a cell outside the tile before any command (P2).
- Window: lo (1024, 0, 1024) hi (1103, 255, 1039) = chunks 64..68 of row z 64, 327680 cells (P1). B (68, 64) tile is
  66..70 x 62..66; chunk 66 is at Chebyshev d 2 from both A and B, 67 at d 3 from A and d 1 from B.
- Asserts (test :108-110): `not_full == [0, 0]`, every edit cell `minecraft:air` in the edited world, json written.
  No assert reads `landed`, `inside_changed`, `outside_changed`, `positions` or the plain arm's blocks beyond not_full.
- Committed json (lab/results/order_edit.json, `when` 10:43:43+05:30): positions 327680, inside 64, outside 48,
  added 0, removed 0, by_chunk_outside {66,64: 34, 67,64: 8, 68,64: 6}, edit_before {stone 55, granite 9} (no air,
  so a setblock that did not land leaves a non-air edit cell and fails :109), not_full [0, 0], fingerprints plain
  e41da4c0...08102721, edited 2e736215...bcbf862ce. The 20 examples are all in chunk (66, 64), x 1059..1063, pairs
  andesite->diorite and dirt->iron_ore only (P3). The examples are the first 20 by sorted position, so they never show
  the 67 and 68 cells.
- Resident run 1 (plain 48e170...5447, outside 18: 66: 4, 67: 8, 68: 6; edited 2e7362...c862ce): in no committed file.
  Unverified. Only run 2 is committed.
- Prior measurements on main: order_control.json 2 runs of [(64,64),(65,64)], 131072 positions, changed 0, both
  fingerprints 1252bed1...b451361ad; order_pair.json AB fingerprint is the same 1252bed1..., so 3 committed AB boots
  agree. "4 boots" (House's lead): the 4th is not in a committed file, unverified. order_pair AB vs BA changed 18
  (64,64: 12, 65,64: 6). forceload_tile.json (int/r2-b10): ring d 3 `null` with the ticket held at stop.
- House's timing lead and the contract's lead (lab-api.md:244-245, 0 outside expected) are both unverified; the runs
  below decide them.

## Probe scripts (Wilson wrote and dry-ran them; run from the worktree root)
- Arm: `C:/Users/seal/AppData/Local/Temp/claude/C--Users-seal-AppData-Local-Claude-Data-claude-pzs8sxrjxfjjc-scratch-workspaces-4efb5d48-8914-40d5-958b-01186c779b92-becc5fed-0e4b-4c3d-be3e-3bf15fa39392-scratch-2026-11-01-42b70f/f708d1ce-97b8-4985-b4ab-75b219fa060b/scratchpad/b12_arm.py`
  `<plain|edited|readonly> <rush|settle> <out.json.gz>`, 1 boot. It imports the test's constants (SRC, ROOT, A, B,
  A_TILE, EDIT, LO, HI) and the same modules. `rush` = the test's steps exactly (`plain rush` = test plain arm,
  `edited rush` = test edited arm). `readonly` sends 64 `execute if block <x> <y> <z> minecraft:air` at the 64 edit
  cells in place of the setblocks (same count, same cells, same chunk, no write). It prints one `arm {...}` line:
  other_java, loop_s (wall time of the 64-command loop), changed_replies, reply_kinds, gap_a_to_b_s (A's bedrock
  answer to just before B's `forceload add`), settle times, positions, not_full, edit_cells_air, fingerprint; and saves
  the window cells to `<out.json.gz>`.
- `settle` adds, in every arm, the same settledness check at three points: after A (before the loop), after the loop
  (before B), and after B (before the final flush, over B's tile 66..70 x 62..66). Check = for each of the 25 tile
  chunks in order, poll `execute if block <cx*16> 0 <cz*16> minecraft:bedrock` every 0.5 s until `Test passed`
  (the same test `wait_loaded` uses, 120 s budget, a timeout raises with the chunk and its reply); then
  `save-all flush` (as run_order does); then 10 s sleep. What it does not check: ring d 3 status (no command reads it)
  and pending generation work after all 25 answer. Bedrock at y 0 of every tile chunk origin: assumed, a timeout will
  name the chunk.
- Diff (pure): `.../scratchpad/b12_diff.py <a.json.gz> <b.json.gz>` prints both fingerprints, `diff {...}` (changed,
  inside, outside, added, removed, by_chunk_outside), the block pairs of outside cells, 10 examples.
- Fake driver F (pure, no java): `.../scratchpad/b12_fake.py <arm> <mode> <out>`. Wilson's dry runs: plain rush 5
  commands, edited rush 69 with changed_replies 64, readonly settle 147, all three files diff 0 (all None, no region).

## N2.G3.5.2 order edit (green 60b6675)
Runs (each line = one probe or test run, one slot; files go to your scratchpad):
1. GREEN, 2 boots: `python .../slot.py python lab/tests/test_order_edit.py Lab.edits_before_neighbour_change_cells_outside_edit`.
   Expected `setblock Changed the block replies 64 of 64`, `not_full [0, 0]`, `Ran 1 test`, `OK`. Paste both
   fingerprints and `by_chunk_outside`; then the json rule. An edited fingerprint other than 2e736215...bcbf862ce is a
   finding.
2. Plain-vs-plain control, 2 boots: `b12_arm.py plain rush pr1.json.gz`, `b12_arm.py plain rush pr2.json.gz`, then
   `b12_diff.py pr1.json.gz pr2.json.gz`. Decides whether the test's plain arm is deterministic: diff changed 0 and
   equal fingerprints = deterministic (then also compare both fingerprints to GREEN's plain); changed > 0 = the plain
   arm varies run to run and `outside_changed` mixes the edit with plain-arm noise. Paste both `arm` lines (gap_a_to_b_s).
3. Timing-matched arm, 3 boots: `b12_arm.py readonly rush ro1.json.gz`, `b12_arm.py readonly rush ro2.json.gz`,
   `b12_arm.py edited rush er1.json.gz`; diff ro1 ro2, ro1 er1, ro2 er1, and pr1 er1. Matched only if each readonly
   loop_s is within 0.5x..2x of er1's loop_s (paste all three); otherwise report the ratio and do not read the pair.
   Readout: ro vs er outside 0 and pr vs er outside > 0 = the outside cells come from the delay, not the edit;
   ro vs er outside > 0 with ro1 == ro2 = the edit itself changes cells outside; ro1 != ro2 = undecided, report.
   er1's fingerprint vs 2e736215...bcbf862ce: equal or not, say which.
4. Quiescent, 4 boots: `b12_arm.py plain settle ps1.json.gz`, `... plain settle ps2.json.gz`,
   `... edited settle es1.json.gz`, `... edited settle es2.json.gz`; diff ps1 ps2, es1 es2, ps1 es1.
   Readout: ps1 == ps2 and es1 == es2 required to read ps1 vs es1; then ps1 vs es1 outside 0 = with A's tile settled
   the edit changes nothing outside; outside > 0 = it does (paste by_chunk_outside and pairs). Any settle timeout:
   paste it, the run is void. Paste all settle_*_loaded_s values.
The `.../slot.py` and `.../scratchpad/` prefixes are the full paths above; the arm and diff scripts take the output
path as given, so pass `<your scratchpad>/<name>`.

Pure mutants of test_order_edit.py, decided by reading (no boot):
- EA no edit: old `            for line in edits.commands(EDIT, A_TILE):` new `            for line in []:` -> FAIL at
  :109 (edit_before is stone 55 + granite 9, no air). Killed.
- EB place instead of break: old `EDIT = [("break", x, y, z, None)` new `EDIT = [("place", x, y, z, "minecraft:stone")`
  -> FAIL at :109 (cells stone). Killed.
- EC region path: old `/ "world" / "region", LO, HI)` new `/ "world" / "regions", LO, HI)` -> `window.box` returns all
  None (batch 10 probe G1), not_full [327680, 327680], FAIL at :108. Killed.
- ED no B: old `        if not orderrun.wait_loaded(srv, *B):\n            raise RuntimeError(f"chunk {B} did not load")\n        srv.command("save-all flush")`
  new `        srv.command("save-all flush")` -> chunk 67 is d 3 from A, `null` in forceload_tile.json with the ticket held
  -> not_full > 0, FAIL at :108. Killed.
- EE edit outside the tile: old `for x in range(1068, 1072)` new `for x in range(1088, 1092)` -> `ValueError chunk
  (68, 64) is not loaded` from edits.py:6 before any command (P2), test ERROR. Killed.
- EF both arms edited: old `        plain, _ = run_fresh(False)` new `        plain, _ = run_fresh(True)` -> asserts read
  only edited cells and not_full: OK. SURVIVES (inside_changed would be 0; nothing asserts 64).
- EG edit on air: old `for y in range(30, 34)` new `for y in range(200, 204)` -> setblock air leaves air whatever the
  cell held: OK. SURVIVES (edit_before would be air; not asserted).
- EH window cut: old `HI = (1103, 255, 1039)` new `HI = (1087, 255, 1039)` -> OK. SURVIVES (positions not asserted).
- EI split inverted: old `inside = [c for c in d["changed"] if c[0] in EDIT_CELLS]` new
  `inside = [c for c in d["changed"] if c[0] not in EDIT_CELLS]` -> OK. SURVIVES (by construction: "any value valid",
  lab-api.md:243).
- EJ json after asserts: move the `OUT.write_text(...)` block (:84-100) below :109 -> OK on green. SURVIVES; the
  contract's "before asserting" is not tested.

Real mutant (2 boots, outcome unverified):
- EK no flush: old `        srv.command("save-all flush")\n        srv.stop()\n        return window.box` new
  `        srv.stop()\n        return window.box`, then the GREEN command. `OK` with the same edited fingerprint
  2e736215...bcbf862ce = the `stop` save alone writes the window and the flush is not what the result depends on; a
  :108/:109 failure = the flush is load-bearing. Paste both fingerprints. Restore the test before anything else.

## Probes run by Wilson (pure)
- P1: `edits.commands(EDIT, A_TILE)` -> 64 lines, first `setblock 1068 30 1024 minecraft:air`, last
  `setblock 1071 33 1027 minecraft:air`; edit chunks {(66, 64)}; window cell count 327680.
- P2: `edits.commands([("break", 1088, 30, 1024, None)], A_TILE)` -> `ValueError chunk (68, 64) is not loaded`.
- P3: committed json summary as in Fixed facts (keys, counts, example chunks and pairs).

## Real boots needed
GREEN 2; run 2 plain control 2; run 3 timing-matched 3; run 4 quiescent 4; real mutant EK 2. Total 13 boots: 9 probe
invocations of 1 boot plus 2 test runs of 2 boots (GREEN, EK), one slot per invocation, never more than 1 server per
resident at a time. Everything else is decided by reading or by P1-P3 and F.
