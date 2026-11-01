# Verification plan, round 2 batch 4 (Wilson, 2026-11-01)

Read from: main e1b96a4 (contract house/lab-api.md:87-108). Every branch has merge-base e1b96a4.
Pins: G2.5 302937c/e9be643, G5.1 716b517/c30d1d5, G5.A1 5a89793/8d25395, G7.1 ef9edc1/60745be, C4 be82c7b,
C5 e5af722, G5.C1 5c875a3, G5.C2 61d2fcf. If `git rev-parse --short res/<gid>` differs from the pin, stop and report.

## Rules for residents
Same as house/verify/r2-batch3.md "Rules for residents", with folder `sealrun-wt/v4-<gid>`. Git Bash, every run line
ends `2>&1; echo EXIT=$?`. RED: error named below, `EXIT=1`. GREEN: `Ran 1 test`, `OK`, `EXIT=0`. Mutation with the
Edit tool, run, expect the failure, `git checkout -- <file>`, re-run `OK`, `git status --short` empty.
Record each run: `house_test_run(test=..., status="red"|"green", covered_files=[...], secs=...)`.

## N2.G2.5 window.box / fingerprint (red 302937c, green e9be643)
Run: `python lab/tests/test_window.py Lab.window_box_and_digest_are_stable`
RED: `ModuleNotFoundError: No module named 'window'` (import at test_window.py:9, module load).
Mutation lab/window.py:35 old `for pos, name in sorted(blocks.items()):` new `for pos, name in blocks.items():` ->
`AssertionError` at test_window.py:31 (reversed dict digest differs), `FAILED (failures=1)`.
Record: test `window_box_and_digest_are_stable`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/window.py"]`.
Data read (anvil.chunk_status on main, read only): chunk (0,1) `full`, (0,0) None; block_at x 0..4, y 0, z 16 = bedrock.

## N2.G5.1 build_r2 (red 716b517, green c30d1d5)
Run: `python site/tests/test_build_r2.py Lab.build_r2_merges_charts_by_id`
RED: `ModuleNotFoundError: No module named 'build_r2'` (test_build_r2.py:9).
Mutation site/build_r2.py:35 old `g["status"] = status.get(gid, "pending")` new `g["status"] = "pending"` ->
`AssertionError: 'pending' != 'reached'`, `FAILED (failures=1)`.
Extra at green: `python site/build_r2.py; git status --short` -> prints `r2.json: 99 goals, status file missing, all
pending`, status empty (read: build(site/charts/r2, {}) dumped with indent=1 equals the committed r2.json).
Record: test `build_r2_merges_charts_by_id`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/site/build_r2.py"]`.

## N2.G5.A1 r2_numbers (red 5a89793, green 8d25395)
Run: `python site/tests/test_r2_numbers.py` (one method, `test_numbers_read_live_missing_is_not_run`).
RED: `ModuleNotFoundError: No module named 'r2_numbers'` (test_r2_numbers.py:8).
Mutation site/r2_numbers.py:15 old `else "not run"` new `else 0` -> `AssertionError: 0 != 'not run'`.
Record: test `test_numbers_read_live_missing_is_not_run`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/site/r2_numbers.py"]`.

## N2.G7.1 fractal (red ef9edc1, green 60745be; branch tip read at 60745be)
Run: `python lab/tests/test_fractal.py Lab.variogram_slope_recovers_h_half`
RED: `ModuleNotFoundError: No module named 'fractal'` (test_fractal.py:7). Needs Python >= 3.10
(`statistics.linear_regression`, fractal.py:21); box has 3.11.9.
Mutation lab/fractal.py:24 old `return fit.slope / 2` new `return fit.slope` -> `AssertionError` with message
`rough H=...` (value unverified), `FAILED (failures=1)`. Do NOT use fractal.py:15 `/ 2` (see Vacuous assertions).
Record: test `variogram_slope_recovers_h_half`, covered_files `["C:/Users/seal/Documents/GitHub/sealrun/lab/fractal.py"]`.

## Guards, red records (test only)
- C4 at be82c7b: `python lab/tests/test_guard_lever_player_legal.py` -> `ModuleNotFoundError: No module named 'lever'`
  (module load, :6). Record red `test_guard_lever_player_legal`, `[".../sealrun/lab/lever.py"]`.
- C5 at e5af722: `python lab/tests/test_guard_lift_needs_replay.py` -> `AttributeError: module 'aim' has no attribute
  'accept'` in each of 5 subTests, `FAILED (errors=5)` (count by reading). Record red `test_guard_lift_needs_replay`,
  `[".../sealrun/lab/aim.py"]`.
- G5.C1 at 5c875a3: `python site/tests/test_guard_site_numbers_from_files.py` -> `ModuleNotFoundError: No module
  named 'r2_numbers'` (import inside test, :13), `FAILED (errors=1)`. Record red, `[".../sealrun/site/r2_numbers.py"]`.
- G5.C2 at 61d2fcf: `python site/tests/test_guard_route_marked_unplayed.py` -> `ModuleNotFoundError: No module named
  'build_r2'` (:16), `FAILED (errors=1)`. Record red, `[".../sealrun/site/build_r2.py"]`.
`.../sealrun/` = `C:/Users/seal/Documents/GitHub/sealrun/`.

## Contract check (lab-api.md:87-108)
- build_r2.py:14-22 department: exact listed id first (:15-17), else the first department in file order holding any
  goal with the same Gk (:18-21), else None. Contract :99-100 says "by its Gk part, never from N2" and gives no
  tie-break. Real site/charts/r2/departments.json shares G1 (neurology, immunology), G3 (neurology, surgery,
  immunology), G4 (surgery, immunology, oncology). In committed r2.json: N2.G3.6.1-.4 and N2.G3.6.A1 -> neurology
  (parent N2.G3.6 is listed under surgery); N2.G4.1 -> surgery (N2.G4.1.1/.2/.4/.5/.6/.A1 listed under immunology);
  N2.G1.1.x, N2.G1.2.x -> neurology (N2.G1.1, N2.G1.2 listed under immunology); N2.G6.1-3 -> None (no G6 listed).
  "Never from N2" holds. Whether file-order tie-break is the intended rule: unverified (contract silent).
- build_r2.py:11,37: route is a constant; contract :101-102 says "until a played result file exists". No file is
  checked; the contract names no played result file.
- build_r2.py:41-42: main() reads status from site/r2_status.json (absent on main), not in the contract; committed
  r2.json has 99/99 goals `pending`, including goals merged in batches 1-3.
- r2_numbers.py:4-8: 11 expected names; contract :103-105 lists none. git grep on main finds no writer of any of
  them; lab/results on main holds fabric_probe.json and order_squares_more.json, neither in NAMES. Invalid JSON in
  a present file raises (:15); contract silent.
- window.py:36 fingerprint hashes `"{x} {y} {z} {name}\n"` per sorted item (None as `None`); contract :67-68 says
  "sha256 of the sorted items" with no encoding. window.py:24,29 match block_at (anvil.py:62,68): None unless
  `full`, air where no Palette section. Palette-less section skipped (:10-11) as :89-90 requires.
- fractal.py:13-14 raises ValueError for a lag with no pairs; a zero gamma makes math.log raise (:22). Contract silent.
- Chart wording: chase N2.G5.C1 card says "not measured"; contract :104 and the guard use "not run".
- test_guard_site_numbers_from_files agrees with r2_numbers' keys: it hardcodes no name, takes `next(iter(...))`
  (:23) = `order_control.json` (r2_numbers.py:5). index.html and serve.py reference neither r2.json nor r2_numbers
  (grep, main); the batch 4 contract does not require it.

## Integration
Files disjoint (`git diff --stat main...res/<gid>`); all eight branch from e1b96a4.
```
git -C /c/Users/seal/Documents/GitHub/sealrun worktree add -b int/r2-batch4 /c/Users/seal/Documents/GitHub/sealrun-wt/int-r2b4 main
cd /c/Users/seal/Documents/GitHub/sealrun-wt/int-r2b4
for b in N2.G2.5 N2.G5.A1 N2.G5.1 N2.G7.1 N2.G5.C1 N2.G5.C2 N2.G3.C4 N2.G3.C5; do git merge --no-ff --no-edit res/$b || break; done
python lab/tests/test_window.py Lab.window_box_and_digest_are_stable 2>&1; echo EXIT=$?
python site/tests/test_build_r2.py Lab.build_r2_merges_charts_by_id 2>&1; echo EXIT=$?
python site/tests/test_r2_numbers.py 2>&1; echo EXIT=$?
python lab/tests/test_fractal.py Lab.variogram_slope_recovers_h_half 2>&1; echo EXIT=$?
for t in lab/tests/test_guard_diff_blocks_only.py site/tests/test_guard_site_numbers_from_files.py site/tests/test_guard_route_marked_unplayed.py lab/tests/test_guard_lever_player_legal.py lab/tests/test_guard_lift_needs_replay.py; do python $t 2>&1; echo EXIT=$?; done
python -m unittest discover -s lab/tests -p "test_*.py" 2>&1; echo EXIT=$?
python -m unittest discover -s site/tests -p "test_*.py" 2>&1; echo EXIT=$?
```
Expected by reading: four bound tests GREEN. Flip RED -> GREEN: test_guard_diff_blocks_only (on main, `import
window` :44; window.py lands), test_guard_site_numbers_from_files (r2_numbers lands), test_guard_route_marked_unplayed
(build_r2 lands; ROUTE build_r2.py:11). Stay RED: test_guard_lever_player_legal (no branch adds lab/lever.py;
contract :91 "no leaf writes it yet"), test_guard_lift_needs_replay (aim.py on main :1-10 has only best_order;
N2.G3.6.3 has no commit in `git log --all`). lab discover therefore ends FAILED while C4/C5 are merged; state of other
main tests under discover: unverified. Discover runs only `test*` methods: the window, build_r2, fractal bound methods
are not run by it.
Guard mutations on int (each reverted after):
- C1 lab: lab/window.py:14 old `enumerate(anvil.section_blocks(names, section["BlockStates"]))` new `enumerate(names)`
  -> AssertionError at test_guard_diff_blocks_only.py:62. Record green `test_guard_diff_blocks_only`, `[.../lab/window.py]`.
- G5.C1: site/r2_numbers.py:15 old `else "not run"` new `else 0` -> AssertionError at :21. Record green, `[.../site/r2_numbers.py]`.
- G5.C2: site/build_r2.py:11 old `{"played": False,` new `{"played": True,` -> `AssertionError: True is not False`
  at :30. Record green, `[.../site/build_r2.py]`.

## Vacuous assertions
- test_window.py:39 `len(blocks) <= 65536`: holds for any chunk_blocks output from <= 16 sections.
- test_window.py:19-31 read only chunk (0,1), status `full`: window.py:24 `== "full"` deleted, all pass; box's None
  branch is not exercised.
- test_build_r2.py:41 passes with build_r2.py:15-17 deleted (fallback also gives neurology, first dept with G3).
- test_build_r2.py:43 passes with build_r2.py:18 `[1:2]` changed to `[0:1]` (the N2 part): neurology is also the
  first dept with an N2 goal. No batch 4 test checks "never from N2"; guard G5.C2 asserts no department.
- test_build_r2.py:37-38: no key appears in two N2.G3.2 cards, so first-wins (:33 setdefault) is not exercised.
- test_guard_site_numbers_from_files.py:33-34 cannot fail once :32 passes; :35-36 cannot fail once :21 passes
  (same names, all "not run" again after the unlink at :30).
- test_fractal.py:33-34 pass with fractal.py:15 `/ 2` removed (constant factor; slope of log gamma unchanged).
  Whether they pass with fractal.py:10 reduced to x pairs only: unverified.
