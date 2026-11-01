# Verification plan, round 2 batch 15 (Wilson, 2026-11-01)

Read from: int/r2-b15 head 89fdba9 = main b872be0 + res/N2.G4.1.2 c804b4b (merge cd37a87) + res/N2.G4.1.A1 f4d96f5
(merge 14aaef5) + res/N2.G4.2.1 26d4466 (merge 89fdba9). `git diff --stat b872be0 89fdba9`: 7 files, 172 insertions
(lab/gridfile.py 19, lab/tests/test_gridfile.py 28, crates/route/tests/fixtures/contract_4x3.grid 20 bytes,
lab/spawn_area.py 23, lab/tests/test_spawn_area.py 39, crates/route/tests/common/mod.rs 23,
crates/route/tests/real_setup.rs 40). Contract: house/lab-api.md "Round 2, batch 15" (lines 289-330 on b872be0).
Pins: 89fdba9. If `git rev-parse --short int/r2-b15` differs, stop and report.
Already run by Wilson on 89fdba9 (Python 3.11.9, cargo, CARGO_BUILD_JOBS=2), pure only, no server, no java: gridfile
GREEN + mutants GA..GF + edge probe; real_setup GREEN + mutants R1..R6. `git status --short` empty after each.
Pending merge: res/N2.G4.2.2 (real_trap.rs) and res/N2.G4.C1 (guard_real_rules.rs); lanes from contract text only.

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v15-<gid> 89fdba9` (pending lanes: the int head that holds the leaf),
  work there, remove it when done (and its `target/`).
- `export PYTHONDONTWRITEBYTECODE=1 CARGO_BUILD_JOBS=2` first.
- Cargo package is `sealrun-route` (crates/route/Cargo.toml:2); `-p route` names no package.
- test_gridfile.py: the method lacks `test_`, so pass it by name; without the name the file prints `Ran 0 tests`,
  `OK` (Wilson ran it: it does). test_spawn_area.py: the method is `test_...`, run the file whole.
- Real-server run (spawn_area only): free RAM first,
  `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"` must print >= 1500.
  At most 2 real servers across ALL agents; the run goes through the slot holder:
  `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py python lab/tests/test_spawn_area.py > <scratch>/sa15.txt 2>&1; echo EXIT=$?`
  Paste `grep -nE "slot.py|spawn|None cells|^tile|^Ran|^OK|FAILED|Error|line [0-9]+" <scratch>/sa15.txt`.
- Java PIDs before and after: `MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq java.exe" /NH`. A java PID that appears
  and stays is a defect to report. Kill only a PID your own run started; NEVER `taskkill /IM`.
- `ls -A ~/sealrun-lab` before and after; a new `tmp*` folder after is a defect to report (remove with
  `serverdir.remove`, as batch 14).
- Mutation: apply with the Edit tool (exact old/new below, each old string occurs once), run, then
  `git checkout -- <file>`; `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.

## Lane 1: gridfile (N2.G4.1.2, pure, done by Wilson)
Command: `python lab/tests/test_gridfile.py Lab.gridfile_matches_committed_contract_bytes`
Pass line: `Ran 1 test`, `OK` (observed).
Fixed facts: fixture is 20 bytes `04000000 03000000 00010203 04050001 02030405` (xxd), equal to HAND (test :11) and to
to_bytes(SAMPLE). flatten.TILES values are 0..5 (flatten.py:1). gridfile.py:12 checks `v not in TILES.values()`.

| id | old (lab/gridfile.py) | new | expected | observed |
|---|---|---|---|---|
| GA | `struct.pack("<II"` | `struct.pack(">II"` | FAIL | FAILED :16 header `00000004` (killed) |
| GB | `struct.pack("<II", w, len(rows))` | `struct.pack("<II", len(rows), w)` | FAIL | FAILED :16 header `03..04..` (killed) |
| GC | `    if any(len(r) != w for r in rows):` | `    if False:` | FAIL | FAILED :21 `ValueError not raised` (killed) |
| GD | `v not in TILES.values()` | `v > 6` | FAIL | FAILED :23 `ValueError not raised` (killed) |
| GE | `v not in TILES.values()` | `not 0 <= v <= 5` | survive (equivalent for ints) | OK |
| GF | `        f.write(to_bytes(rows))` | `        pass` | survive | OK (`write` is never called by the test) |

Edge probe (Wilson, original gridfile.py): `to_bytes([[]])` returns 8 bytes `00000000 01000000` (w 0, h 1), no
ValueError; `to_bytes([[True, False]])` returns `02000000 01000000 01 00`; `[[-1]]` raises ValueError;
`[[1.0]]` passes the TILES check (1.0 == 1) and raises TypeError from `bytes()`, not ValueError.
Open items (not fixes): `write` untested (GF); the fixture is compared to HAND, not produced by `write`; `[[]]`
(zero-width) is accepted, and whether Rust `Grid::from_bytes` accepts w 0 is unverified (N2.G4.1.3).

## Lane 2: start_finish (N2.G4.2.1, pure, done by Wilson)
Command: `cargo test -p sealrun-route --test real_setup`
Pass line: `test start_and_finish_picked_on_hand_grid ... ok`, `test result: ok. 1 passed` (observed).
Fixed facts (hand-checked): grid `tie` (real_setup.rs:26) has Air (2,0) and (1,1) both at distance 2 from centre (2,2);
key (d, y, x) picks (2,0). Irons (4,1) and (1,2) both at distance 3 from (2,0); key (d, y, x) picks (4,1), whose only
open neighbour is (4,0). So one grid tests each sort key separately. `walled` (:29): nearest iron (2,4) at d 2 has
no open neighbour, next (0,3) gives (1,3). is_open = Air | Goal (crates/world/src/grid.rs:13-14).
Start key alone and iron key alone (the batch 14 tie-order mutant changed both together; R1 and R2 isolate them):

| id | old (crates/route/tests/common/mod.rs) | new | expected | observed |
|---|---|---|---|---|
| R1 start key only, :9 | `abs(), y, x))?;` | `abs(), x, y))?;` | FAIL | FAILED :27 left `Some(((1, 1), (1, 1)))` (killed) |
| R2 iron key only, :12 | `abs(), y, x));` | `abs(), x, y));` | FAIL | FAILED :27 left `Some(((2, 0), (1, 1)))` (killed) |
| R3 no skip, :13 | `irons.iter().find_map(\|&(x, y)\| open_neighbour(grid, x, y))?` | `irons.first().and_then(\|&(x, y)\| open_neighbour(grid, x, y))?` | FAIL | FAILED :30 left `None` (killed) |
| R6 iron distance to centre, :12 | `(x as i64 - sx).abs() + (y as i64 - sy).abs()` | `(x as i64 - cx).abs() + (y as i64 - cy).abs()` | FAIL | FAILED :27 left `Some(((2, 0), (1, 1)))` (killed) |
| R4 neighbour order, :19 | `[(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]` | `[(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]` | survive | OK |
| R5 centre rounding, :6 | `((w / 2) as i64, (h / 2) as i64)` | `(((w - 1) / 2) as i64, ((h - 1) / 2) as i64)` | survive | OK |

Open items (not fixes): every iron in the hand grids that has an open neighbour has exactly one, so neighbour order
is untested (R4); every hand grid has odd w and h (5x5, 5x1, 3x1), so integer w/2 vs (w-1)/2 is untested (R5);
`from_rows` has no Goal character, so start = Air only (not Goal) and a Goal neighbour as finish are untested.
Contract asks for "a 5x5 with the answer computed by hand" and a tie case; the test covers both with one grid
(`tie`), not two.

## Lane 3: spawn_area (N2.G4.1.A1, one real boot, resident)
Command: the slot command above (1 slot, 1 boot). Pass line: `Ran 1 test`, `OK`, `None cells 0`, `tile tree N`,
`tile stone N`, `tile iron N` with each N >= 1, and the printed `cells` = 97 * 97 * 256 = 2408704 (half 48).
Fewer than one of a kind is a finding, reported, never bent (do not widen `half`).
Fixed facts: spawn_area.py:10-14 boots, sends only `save-all flush`, stops in `finally`; :16-17 reads SpawnX/SpawnZ
from level.dat after stop (test_far_chunk.py:35 reads it while running; same nbt call); :18-22 `window.box` over
x, z spawn +-half, y 0..255. window.box (window.py:19-30) sets a cell to None unless its chunk status is "full".
flatten "stone" is a ground step >= 2 (flatten.py:36-38), "iron" is iron_ore within 7 blocks at or below ground
(:34-35), "tree" is a `_log` ground block (:30-31).
Mutants decided by reading (no boot needed; run one only if House wants it observed, 1 boot each):
- SM-1 old `(spawn_x + half, 255, spawn_z + half)` new `(spawn_x + half - 1, 255, spawn_z + half)` in
  lab/spawn_area.py:21 -> must FAIL: flatten.grid raises `ValueError: no ground block at (spawn_x+48, ...)`
  (flatten.py:50-52) at test :28.
- SM-2 add `        srv.command("forceload add 0 0")` after `        srv.command("save-all flush")` (:12) -> survives:
  the test does not check which commands were sent (contract "no other command" is unchecked).
- SM-3 old `def read(scratch, half=48):` new `def read(scratch, half=8):` (:9) -> survives: the test passes
  `half=HALF` explicitly.
Open items: the test does not assert `len(blocks)` or that spawn is read from the right keys (a SpawnZ-for-both
mutant's outcome depends on terrain: unverified); "only save-all flush" is untested (SM-2). Whether all 49 chunks of
the window are "full" after one boot with no forceload is unverified until the run.

## Lane 4: real_trap (N2.G4.2.2, PENDING MERGE, contract text only)
Command: `cargo test -p sealrun-route --test real_trap`. Pass line: `test planner_beats_move_counter_on_wall_trap ... ok`.
Contract numbers re-added by Wilson: plan 4x60 + 20 + 20 + 3x23 + 20 + 8x12 + 20 = 485, moves 4+1+1+3+1+8+1 = 19;
bfs 4x60 + 20 + 20 + 11x23 + 20 + 20 = 573, moves 19; 573 - 485 = 88 = 8 x (23 - 12). Consistent.
Mutants (exact old strings to be pinned by the resident from the merged file; each must FAIL):
- T1 done condition: replace `inv.pick >= Tool::Stone` with `inv.pick >= Tool::Wood` in the done closure ->
  ticks change (no stone pick needed), assert on 485/573 fails.
- T2 replace the expected bfs ticks literal `573` with `572` -> FAIL (pins the number is asserted, not printed).
- T3 replace the summed-ticks replay check (sum of `state::moves` ticks == reported ticks) with `true`, or delete it
  -> must FAIL only if the test has a separate assert on the reported value; if OK, the replay clause is
  unasserted (finding).
Open items: unverified until merge: that both routes are replayed through `state::moves` (not only plan's), and
that the map is exactly Tree, Air start, Stone with goal_pos (1,0) and `Inv::EMPTY`.

## Lane 5: guard_real_rules (N2.G4.C1, PENDING MERGE, contract text only)
Command: `cargo test -p sealrun-route --test guard_real_rules`. Pass line: `test guard_real_rules ... ok`.
First check: `grep -nE "state::moves|metric::dig|use sealrun_route::(state|metric)" crates/route/tests/guard_real_rules.rs`
must print nothing for `moves`/`dig` (independence clause).
Mutants in the checker inside the test file (each must FAIL):
- C1 iron pick gate: replace the iron requirement `Tool::Stone` with `Tool::Wood` -> the wood-pick hand route is Ok,
  the `"stone pickaxe"` Err assert fails.
- C2 walk cost: replace the walk ticks `5` with `4` -> plan's ticks differ from check's, the equality assert fails.
- C3 stone-pick stone ticks: replace `12` (stone with stone pick) with `13` -> the real_trap 3x1 replay is no longer
  485 (8 stone x 1 = 493), assert fails. This is the 12-tick branch House flagged at 12:05.
- C4 walk into stone allowed: make the walk target check accept Stone -> the walk-into-stone Err assert fails.
Open items: unverified until merge: smelt (200 ticks) is exercised by any asserted route (the real_trap and
iron_ore routes need no smelt as read from the contract, so a smelt-cost mutant likely survives); the crafts table
copied from state.rs `crafts` could drift from it with no test linking them.

## Boots
Lane 3 only: 1 boot, 1 slot. Lanes 1, 2 done; lanes 4, 5 pure (cargo) once merged.

## Defects
- None in gridfile.py against the contract (GA..GD killed). Test gaps: `write` (GF), zero-width row accepted.
- None in common/mod.rs against the contract (R1, R2, R3, R6 killed). Test gaps: neighbour order (R4), even-size
  centre rounding (R5), Goal tiles.
- spawn_area: none by reading; run pending (lane 3).
