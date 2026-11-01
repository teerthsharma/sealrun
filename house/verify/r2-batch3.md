# Verification plan, round 2 batch 3 (Wilson, 2026-11-01)

Read from: main d096101 (contract house/lab-api.md:61-86). Every branch has merge-base d096101.
Pins: G2.4 9c2c7de/7da77e5, G3.2.1 dc95676/4d2eef8, G3.5.1 2b4d601/282ac5c, G3.6.1 82f2132/54562d7,
G3.7.1 e2e0572/c6f4651, C2 f4ea1bb, C1 362697b then 87fba8e (C1 tip moved during reading; if
`git rev-parse res/N2.G3.C1` is not 87fba8e, stop and report).

## Rules for residents
- Git Bash. Run commands exactly; paste full output. Never write in main or in the res worktrees.
- Fresh folder per goal: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach /c/Users/seal/Documents/GitHub/sealrun-wt/v3-<gid> <red sha>`
  then `cd` there. RED = run at the red sha; `git checkout --detach <green sha>`; GREEN = run again.
- Every run line ends `2>&1; echo EXIT=$?`. RED: traceback named below, last line `EXIT=1`. GREEN: `Ran 1 test`, `OK`, `EXIT=0`.
- Mutation: Edit tool, exact old/new text (each old text occurs once), run, expect the failure named, then
  `git checkout -- <file>`, re-run must give `OK` / `EXIT=0`, `git status --short` empty.
- After recording: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree remove /c/Users/seal/Documents/GitHub/sealrun-wt/v3-<gid>`.
- Record each RED and GREEN with `house_test_run(test=..., status="red"|"green", covered_files=[...], secs=...)`.

## N2.G2.4 anvil.block_at / chunk_status (red 9c2c7de, green 7da77e5)
Run: `python lab/tests/test_anvil_block_at.py Lab.block_at_negative_coords_status_and_missing_chunk`
RED: `AttributeError: module 'anvil' has no attribute 'block_at'`, `FAILED (errors=1)`. Reads real files under
`C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1/world/region` (read only).
Mutation lab/anvil.py:49 old `if not path.is_file():` new `if False:` -> `FileNotFoundError` naming `r.-7.0.mca`, `FAILED (errors=1)`.
Record: test `block_at_negative_coords_status_and_missing_chunk`, covered_files
`["C:/Users/seal/Documents/GitHub/sealrun/lab/anvil.py"]`.

## N2.G3.2.1 orderrun.wait_loaded (red dc95676, green 4d2eef8)
Run: `python lab/tests/test_wait_loaded.py Lab.wait_loaded_polls_bedrock_probe_until_loaded`
RED: `ModuleNotFoundError: No module named 'orderrun'` (import at module load).
Mutation lab/orderrun.py:6 old `client.command(f"forceload add {x} {z}")` new `pass` ->
`AssertionError: 'execute if block -48 0 80 minecraft:bedrock' != 'forceload add -48 80'`, `FAILED (failures=1)`.
Record: test `wait_loaded_polls_bedrock_probe_until_loaded`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/orderrun.py"]`.

## N2.G3.5.1 edits.commands (red 2b4d601, green 282ac5c)
Run: `python lab/tests/test_edits.py Lab.edit_commands_stay_inside_loaded_chunks`
RED: `ModuleNotFoundError: No module named 'edits'`.
Mutation lab/edits.py:5 old `if cell not in loaded:` new `if False:` -> `AssertionError: ValueError not raised`.
Record: test `edit_commands_stay_inside_loaded_chunks`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/edits.py"]`.

## N2.G3.6.1 aim.best_order (red 82f2132, green 54562d7)
Run: `python lab/tests/test_aim_pure.py Lab.best_order_picks_max_or_says_no_lever`
RED: `ModuleNotFoundError: No module named 'aim'`.
Mutation lab/aim.py:7 old `if min(counts) == top:` new `if False:` -> `AssertionError` on the all-equal dict
(got `'lever': True ... 'mean': 4.0`), `FAILED (failures=1)`.
Record: test `best_order_picks_max_or_says_no_lever`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/aim.py"]`.

## N2.G3.7.1 verdict.statements (red e2e0572, green c6f4651)
Run: `python lab/tests/test_verdict.py Lab.verdict_states_bound_and_reroute`
RED: `ModuleNotFoundError: No module named 'verdict'`.
Mutation lab/verdict.py:19 old `s += ", noise floor not measured"` new `pass` ->
`AssertionError: 'noise floor not measured' not found in ...`. Do NOT use verdict.py:21 (the "shaky" line) as the
mutation: the test stays GREEN without it (see Vacuous assertions).
Record: test `verdict_states_bound_and_reroute`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/verdict.py"]`.

## N2.G3.C2 guard noise_floor_first (f4ea1bb, test only)
Run at f4ea1bb: `python lab/tests/test_guard_noise_floor_first.py` -> `ModuleNotFoundError: No module named 'verdict'`.
Record red: test `test_guard_noise_floor_first`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/verdict.py"]`.
GREEN and its mutation run on the integration branch (below).

## N2.G3.C1 guard diff_blocks_only (87fba8e, test only)
Run at 87fba8e: `python lab/tests/test_guard_diff_blocks_only.py` -> `ModuleNotFoundError: No module named 'window'`
(import at :44, inside the test), `FAILED (errors=1)`.
Record red: test `test_guard_diff_blocks_only`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/window.py"]`.
No GREEN possible: window.py (N2.G2.5) exists on no branch. 87fba8e fixed a KeyError in 362697b: the first present
chunk of r.0.0.mca, local (0, 1), has Sections[0] Y=-1 with no Palette (read from the file). Control edit at :62
flips section Y=0 block 0 from minecraft:bedrock to minecraft:stone (read from the file), so it is a real change.

## Contract check (lab-api.md:61-86)
- anvil.py:64-68: no section with Palette at `y >> 4` returns `"minecraft:air"`; contract does not state this case.
- anvil.py:57: chunk_status also returns None for a Level without Status; contract names only missing file or chunk.
- orderrun.py:7,11-14: timeout is the sum of `poll` values handed to `sleep`, not elapsed wall time; command
  round-trip time is not counted. Whether the contract means wall time: unverified.
- edits.py:7: any op other than "break" is emitted as a place; contract names two ops and no unknown-op error.
- aim.py:9-10: `"order"` is the order list of the first max row; contract text reads `<first row with the max>`.
  The test (test_aim_pure.py) expects the list. Which the contract means: unverified.
- verdict.py:5,22: when repeat_diff is not None, statements add "order lever alive/dead/not run"; beyond the
  contract, not against it. Otherwise verdict.py matches (NEXT_ROUTE string at :4 equals the contract text).
- No other differences found.

## Integration
Files are disjoint (from `git diff --stat main...res/<gid>`): anvil.py + test_anvil_block_at.py; orderrun.py +
test_wait_loaded.py; edits.py + test_edits.py; aim.py + test_aim_pure.py; verdict.py + test_verdict.py;
test_guard_noise_floor_first.py; test_guard_diff_blocks_only.py. orderrun, edits, aim, verdict are new files.
```
git -C /c/Users/seal/Documents/GitHub/sealrun worktree add -b int/r2-batch3 /c/Users/seal/Documents/GitHub/sealrun-wt/int-r2b3 main
cd /c/Users/seal/Documents/GitHub/sealrun-wt/int-r2b3
for b in N2.G2.4 N2.G3.2.1 N2.G3.5.1 N2.G3.6.1 N2.G3.7.1 N2.G3.C2 N2.G3.C1; do git merge --no-ff --no-edit res/$b || break; done
python lab/tests/test_anvil_block_at.py Lab.block_at_negative_coords_status_and_missing_chunk 2>&1; echo EXIT=$?
python lab/tests/test_wait_loaded.py Lab.wait_loaded_polls_bedrock_probe_until_loaded 2>&1; echo EXIT=$?
python lab/tests/test_edits.py Lab.edit_commands_stay_inside_loaded_chunks 2>&1; echo EXIT=$?
python lab/tests/test_aim_pure.py Lab.best_order_picks_max_or_says_no_lever 2>&1; echo EXIT=$?
python lab/tests/test_verdict.py Lab.verdict_states_bound_and_reroute 2>&1; echo EXIT=$?
python lab/tests/test_guard_chunk_status_full.py 2>&1; echo EXIT=$?
python lab/tests/test_guard_noise_floor_first.py 2>&1; echo EXIT=$?
python lab/tests/test_guard_diff_blocks_only.py 2>&1; echo EXIT=$?
python -m unittest discover -s lab/tests -p "test_*.py" 2>&1; echo EXIT=$?
```
Expected by reading: the five bound tests GREEN. Flip RED -> GREEN: test_guard_chunk_status_full (anvil has no
chunk_status on main; :76-81 hold against anvil.py:47-68) and test_guard_noise_floor_first (verdict.py lands).
Stays RED: test_guard_diff_blocks_only (`import window` at :44; window.py not built). So discover ends
`FAILED (errors>=1)` while C1 is merged; other main tests' state under discover: unverified.
Discover runs only methods named `test*`: the five bound methods (and main's non-`test` methods) are not run by it.
Guard C2 mutation on int: verdict.py:19 old `s += ", noise floor not measured"` new `pass` ->
`AssertionError: 'noise floor not measured' not found`; record green: test `test_guard_noise_floor_first`.
Record green: test `test_guard_chunk_status_full`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/anvil.py"]`.

## Vacuous assertions
- test_verdict.py:38-40: file named `order_shaky.json`; every statement starts with the file name
  (verdict.py:17), so `assertIn("shaky", s)` passes with verdict.py:21 deleted.
- test_guard_noise_floor_first.py:27,40: same, case file `order_shaky.json`.
- test_verdict.py:36: `assertNotIn("matter", s)`; verdict.py never emits "matter", its claim wording is
  "order lever ..." (verdict.py:5), so this cannot catch the claim. (The C2 guard checks "lever", :36-37.)
- test_anvil_block_at.py:20-27: every None case is a missing chunk (read from the files: (0,0), (-1,0), (-1,-1)
  absent; r.-7.0.mca absent), so the `Status != "full"` gate at anvil.py:62 is not exercised by this test; the
  name says "status". test_guard_chunk_status_full.py:79 does exercise it.
