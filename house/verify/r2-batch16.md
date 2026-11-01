# Verification plan, round 2 batch 16 (Wilson, 2026-11-01)

Read from: int/r2-b16 head 6b869f2 = main 60db6b7 + res/N2.G4.1.6 1ab5a37 + res/N2.G4.1.3 a88adab + res/N2.G4.C3
1c7c00b + res/N2.G3.4.A3 0d4dc18. `git diff --stat 60db6b7 6b869f2`: 6 files, 2115 insertions. Contract:
house/lab-api.md "Round 2, batch 16" (line 332 on 60db6b7). Pin: 6b869f2; if `git rev-parse --short int/r2-b16` differs,
stop and report. Done by House (not repeated): GREEN of all four tests; seed7 HALF 32->33, grid.rs `0 => Tile::Air`
-> Goal, state.rs:70 in_bounds -> `nx >= 0 && ny >= 0` (all FAIL). Wilson ran pure mutants below on 6b869f2
(worktree sealrun-wt/w16, CARGO_BUILD_JOBS=2); `git status --short` empty after each. Pending merge: N2.G4.C2.

## Rules for residents
- Git Bash; `git worktree add --detach /c/Users/seal/Documents/GitHub/sealrun-wt/v16-<gid> 6b869f2`; remove it and its
  `target/` when done. `export PYTHONDONTWRITEBYTECODE=1 CARGO_BUILD_JOBS=2`. Package is `sealrun-route`.
- Python methods lack `test_`: pass `Lab.<method>` by name (else `Ran 0 tests`, `OK`).
- Mutation: Edit tool, run, `git checkout -- <file>`, `git status --short` must print nothing.
- Real boots (lane 4 only): free_mb >= 1500, through slot.py, java PIDs and `ls -A ~/sealrun-lab` before/after, kill
  only your own PID, never `taskkill /IM`. Never call `house_*` / `mcp__uriel-house__*`; paste output to House.

## Lane 1: seed7_area (N2.G4.1.6, pure, done)
Command: `python lab/tests/test_seed7_script.py Lab.area_script_turns_window_into_grid_bytes` -> `OK` (observed).
| id | change | expected | observed |
|---|---|---|---|
| S-W | replace `    gridfile.write(path, rows(blocks, spawn))` with `    pass` in lab/seed7_area.py:15 | FAIL | FileNotFoundError at test :46 (killed; closes batch 15 GF gap) |
| S-T | replace `    return flatten.grid(blocks, sx - HALF, sz - HALF, SIZE, SIZE)` with `    return [list(r) for r in zip(*flatten.grid(blocks, sx - HALF, sz - HALF, SIZE, SIZE))]` in :11 (transpose) | SURVIVE | OK |
| S-C | replace `half=HALF` with `half=48` in :19 | SURVIVE | OK (`capture` not run by the test) |
Open items: both marked cells sit on the diagonal (offsets (2,2), (22,22), test :31-32), so x/z transposition is
untested (S-T); `capture` is untested (S-C, per contract).

## Lane 2: real_grid_contract (N2.G4.1.3, pure, done)
Command: `cargo test -p sealrun-route --test real_grid_contract` -> `1 passed` (observed).
| id | change in crates/world/src/grid.rs | expected | observed |
|---|---|---|---|
| G-LEN | replace `if body.len() as u64 != w as u64 * h as u64` with `if (body.len() as u64) < w as u64 * h as u64` (:74) | SURVIVE | ok |
| G-HDR | replace `        if bytes.len() < HEADER {` with `        if bytes.len() <= HEADER {` (:68) | SURVIVE | ok |
| G-WH | swap `[bytes[0], bytes[1], bytes[2], bytes[3]]` and `[bytes[4], bytes[5], bytes[6], bytes[7]]` (:71-72) | FAIL (w 3 != 4, test :19) | not run (reading) |
Open items: a file with trailing bytes is never tried, so `!=` vs `<` is untested (G-LEN); an 8-byte header-only
input (w 0, h 0) is never tried (G-HDR), nor w 0 from Python `to_bytes([[]])` (batch 15 open item stays open).

## Lane 3: guard_crop_edge_wall (N2.G4.C3, pure, done)
Command: `cargo test -p sealrun-route --test guard_crop_edge_wall` -> `1 passed` (observed).
| id | change in crates/route/src/state.rs | expected | observed |
|---|---|---|---|
| C-DIAG | replace `(0, -1), (0, 1)];` with `(0, -1), (1, 1)];` in DIRS (:43) | FAIL | panicked :29, left `[(1, 0), (1, 1)]` (killed) |
| C-TREE | change hand-dig ticks of Tree in metric `dig` from 60 to 61 | FAIL (test :38 wants 60) | not run (reading; resident pins the exact old string in crates/route/src/metric.rs) |
Open items: the 3x3 grid is all Air, so no `Mine` move is produced and the Mine half of the bounds assert (:13) is
vacuous; Mine shares `near` (state.rs:67-72) with Walk, so it is covered only by sharing, not by a case.

## Lane 4: four_first_chunk_classes (N2.G3.4.A3, real, 4 boots per run; House re-running GREEN)
Command: `python lab/tests/test_order_first_chunk.py Lab.four_first_chunk_classes_tallied` via slot.py.
Committed lab/results/order_square.json (0d4dc18): differing_blocks per class 0, 30, 43, 41; by_chunk sums match
(12+6+12+0, 26+3+14+0, 7+3+17+14); none_cells 0 x4; 24 rows, 4 measured; `when` 2026-11-01T12:19:40+05:30.
What the test asserts (:81-87): none_cells all 0, class 0 differing 0, 24 rows, 4 measured, 6 rows per class, file
exists. What it cannot see: class 0 differing 0 is `diff(worlds[0], worlds[0])` (:44), a self-comparison, not a
control; nothing asserts classes 1-3 differ or not (by contract); `differing_blocks`, `ores`, `inferred_from` in rows
and the ores tally are unasserted; there is no second build of any order, so run-to-run noise is unmeasured.
One boot-mutant (4 boots, only if House wants it observed): replace `blockdiff.diff(worlds[0], world)` with
`blockdiff.diff(world, world)` in :44 -> SURVIVE (all differ 0, every assert holds), proving the differ numbers are
printed, not checked. Decided by reading, no boot: replace `"n2-F6"` with `None` in :69 -> SURVIVE.

## Lane 5: guard_block_names (N2.G4.C2, PENDING MERGE, contract text only)
Command: `cargo test -p sealrun-route --test guard_block_names`. Pass line: `test guard_block_names ... ok`.
- B1 replace `5 => Tile::Goal,` with `5 => return Err(GridError::UnknownTile(b)),` in grid.rs:89 -> FAIL (b=5 must be Ok).
- B2 add `6 => Tile::Goal,` before `_ =>` in grid.rs:90 -> FAIL (b=6 must be Err).
- B3 make `is_open` accept Water (grid.rs:13-14) -> FAIL (Walk((1,0)) appears on [Air, Water, Air]).
Open items: lava in lab/flatten.py `_tile` becomes air or stone (contract "Known gap"); untested by this leaf.

## Boots
Lane 4 only (4 per run, ~92 s); at most the one boot-mutant above. Lanes 1-3 done; lane 5 pure once merged.
