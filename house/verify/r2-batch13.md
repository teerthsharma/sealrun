# Verification plan, round 2 batch 13 (Wilson, 2026-11-01)

Read from: int/r2-b13 head 2153c16 = main 41a6e3f + res/N2.G1.4.4 (one commit, 2153c16). `git diff --stat 41a6e3f
2153c16`: 3 files, 102 insertions (lab/choice.py 33, lab/tests/test_world_route.py 62, lab/results/world_route.json 7).
lab/results/worlds_vanilla.json is unchanged in that range (last touched by cc6077e). Contract: house/lab-api.md:247-258.
Pins: 2153c16. If `git rev-parse --short int/r2-b13` differs (other than this plan's own commit), stop and report.
Already run by Wilson on 2153c16 (Python 3.11.9), pure only, no server, no java: the test by name (GREEN below), harness
H13 on the original and on mutants WA..WN, a regeneration of the json (probe R). `git status --short` empty after each.

## Rules for residents
- Git Bash. Worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v13-<gid> 2153c16`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first, or `?? lab/__pycache__/` appears.
- No slot, no java, no RAM gate: everything in this batch is pure.
- Always pass the test name (the method lacks `test_`; without it the file prints `Ran 0 tests`, `OK`, EXIT=0; Wilson
  ran both): `python lab/tests/test_world_route.py Lab.route_choice_picks_more_worlds_per_gb_and_falls_back`.
  `python -m unittest lab.tests.test_world_route` also prints `Ran 0 tests`, `OK`.
- `python lab/choice.py` rewrites the tracked lab/results/world_route.json. After any run of it:
  `git diff lab/results/world_route.json` (paste it: any change outside `"when"` is a finding), then
  `git checkout -- lab/results/world_route.json`.
- Mutation: apply with the Edit tool (exact old/new below, in lab/choice.py), run the test by name, expect the result
  named, then `git checkout -- lab/choice.py`; `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool; paste the output to House.
- Report for each run: `Ran`/`OK`/`FAILED`, the failing test line, the last AssertionError line, EXIT.

## Fixed facts (read by Wilson on 2153c16)
- `per_gb` (choice.py:8-9) = `worlds_per_minute / (peak_mb_total / 1024)`, as the contract (lab-api.md:248).
- `pick` (choice.py:12-22): best = `max(vanilla_runs, key=per_gb)` (:13); None -> vanilla `"missing"` (:15-16); a
  "blocked" key -> vanilla with `other["blocked"]` (:17-18), checked before any per_gb of other, so a blocked other
  needs no numbers; strict `>` (:19) -> in_process with `vanilla_best_n` of the best vanilla run (:20-21); else vanilla
  `"in_process not more worlds per GB"` (:22). The two non-contract "why" strings (:21, :22) are not fixed by the
  contract (lab-api.md:251-252 names only "missing" and the blocked reason).
- Committed numbers: 3.07 / (812.2 / 1024) = 3.8705737503078055, 4.42 / (1609.2 / 1024) = 2.812627392493164
  (python, printed by Wilson), so `vanilla_best_n` 1, as the contract says (lab-api.md:256-257).
- `when` (choice.py:28) = `datetime.now().astimezone().isoformat(timespec="seconds")`: carries the local offset. The
  committed value is `"2026-11-01T11:06:34+05:30"` (offset present), 16 s before the commit time of 2153c16
  (11:06:50 +0530). The test checks `when` only for presence and truthiness (test :55-57), not for an offset (WM).
- Probe R (Wilson): `python lab/choice.py` on 2153c16 rewrote world_route.json with only `"when"` changed
  (`11:06:34+05:30` -> `11:07:58+05:30`); route vanilla, 3.8705737503078055, vanilla_best_n 1 and the blocked "why"
  byte-identical. The committed json is consistent with `python lab/choice.py` on the committed worlds_vanilla.json;
  that it was produced by that command (rather than written by hand with the same bytes) is unverified.
- The test never calls `choice.main` (its only `main(` is `unittest.main()`); main is tested only through the committed json
  (test :49-58). Mutants of main survive unless the json is regenerated (WM, WN).
- Not covered by contract or test: `pick([], ...)` raises `ValueError` from `max` (:13); `peak_mb_total` 0 raises
  `ZeroDivisionError` (:9). Read only, not run.

## Contract clauses vs test (lab-api.md:247-258)
| Clause | Asserted | Where |
|---|---|---|
| per_gb formula | yes | test :25-26 (WC killed) |
| best vanilla run by per_gb | yes | test :30, :50 (WD killed) |
| other better -> in_process, per_gb of other, vanilla_best_n of vanilla | yes | test :34-36 (WH, WI, WL killed) |
| other worse -> vanilla | yes (route, number) | test :39-40 (WJ killed); its "why" not asserted (WG survives) |
| other equal -> vanilla (strict) | yes | test :43 (WA killed) |
| other None -> vanilla "missing" | yes | test :29-31 (WE, WK killed) |
| other blocked but better -> vanilla, why quotes reason | yes | test :46-47 (WB killed) |
| result keys exactly {route, worlds_per_minute_per_gb, vanilla_best_n, why} | partly | only via saved == pick (:58), not a key-set check |
| committed vanilla_best_n is 1 | yes | test :50 |
| committed world_route.json == pick(runs, blocked) ignoring "when" | yes | test :52-58 |
| main reads worlds_vanilla.json, writes world_route.json, adds "when" | no | main never called (WM, WN survive) |
| "when" has a timezone offset | no (not in contract either) | committed value has +05:30; WM survives |

## GREEN (Wilson ran)
`python lab/tests/test_world_route.py Lab.route_choice_picks_more_worlds_per_gb_and_falls_back` -> `Ran 1 test`, `OK`.
Without the name: `Ran 0 tests`, `OK`. Resident's lead "RED ModuleNotFoundError before choice.py": not re-run by Wilson
(unverified); `import choice` at test :8 makes it the expected RED.

## Harness H13 (pure)
Script: `C:/Users/seal/AppData/Local/Temp/claude/C--Users-seal-AppData-Local-Claude-Data-claude-pzs8sxrjxfjjc-scratch-workspaces-4efb5d48-8914-40d5-958b-01186c779b92-becc5fed-0e4b-4c3d-be3e-3bf15fa39392-scratch-2026-11-01-42b70f/f708d1ce-97b8-4985-b4ab-75b219fa060b/scratchpad/h13.py`.
Run from the worktree root: `python -B h13.py [WX]`. It applies the mutant to choice.py source in memory, registers it
as module `choice`, loads the real test file and runs the named method. Original: `ORIG OK`.

## Mutants (old/new in lab/choice.py; outcome observed by Wilson through H13)
- WA strict to non-strict: old `    if per_gb(other) > per_gb(best):` new `    if per_gb(other) >= per_gb(best):`
  -> FAILED at test :43 (equal case returns in_process). Killed. Matches the resident's lead.
- WB blocked ignored: old `    if "blocked" in other:` new `    if False:` -> FAILED at test :46 (route in_process,
  9.0). Killed.
- WC no /1024: old `(run["peak_mb_total"] / 1024)` new `run["peak_mb_total"]` -> FAILED at test :25. Killed.
- WD worst vanilla: old `best = max(vanilla_runs, key=per_gb)` new `best = min(vanilla_runs, key=per_gb)` -> FAILED
  at test :30 `2 != 1`. Killed.
- WE missing word: old `"why": "missing"` new `"why": "absent"` -> FAILED at test :31. Killed.
- WF in_process why: old `"why": "in_process has more worlds per GB"` new `"why": "x"` -> OK (SURVIVES; string not in
  the contract).
- WG vanilla-better why: old `"why": "in_process not more worlds per GB"` new `"why": "x"` -> OK (SURVIVES; string not
  in the contract, worse/equal "why" never asserted).
- WH in_process number from vanilla: old `"worlds_per_minute_per_gb": per_gb(other), "vanilla_best_n": best["n"]` new
  `"worlds_per_minute_per_gb": per_gb(best), "vanilla_best_n": best["n"]` -> FAILED at test :35. Killed.
- WI in_process best_n from other: same old, new `"worlds_per_minute_per_gb": per_gb(other), "vanilla_best_n":
  other.get("n")` -> FAILED at test :36 `None != 1`. Killed.
- WJ worse case reports other's number: old `    return {**vanilla, "why": "in_process not more worlds per GB"}` new
  `    return {**vanilla, "worlds_per_minute_per_gb": per_gb(other), "why": "in_process not more worlds per GB"}`
  -> FAILED at test :40 `1.0 != 3.87...`. Killed.
- WK no None branch: delete `    if other is None:\n        return {**vanilla, "why": "missing"}\n` -> ERROR at test :28
  `TypeError: argument of type 'NoneType' is not iterable`. Killed.
- WL wrong route label: old `{"route": "in_process", "worlds_per_minute_per_gb"` new `{"route": "vanilla",
  "worlds_per_minute_per_gb"` -> FAILED at test :34. Killed.
- WM naive when: old `datetime.now().astimezone().isoformat` new `datetime.now().isoformat` -> test OK on the
  committed json (SURVIVES). Wilson also ran the mutated main: `"when": "2026-11-01T11:09:07"` (no offset), then the
  test by name -> `OK` (SURVIVES even after regeneration). Restored with `git checkout`.
- WN main ignores the blocked input: old `    out = pick(runs, {"route": "in_process", "blocked":` new
  `    out = pick(runs, None) or pick(runs, {"route": "in_process", "blocked":` -> test OK on the committed json
  (SURVIVES: main not called). After regenerating with the mutated main (`"why": "missing"`), the test FAILED at :58.
  Killed only by regeneration.

Nothing left undecided: every mutant above has an observed outcome. No real boots needed for this batch.

## Defects
None in choice.py against lab-api.md:247-258 (every clause checked above holds on 2153c16). Test gaps, not code
defects: test :55-57 checks `when` only for truthiness (WM); main is not exercised by the test (WN); worse/equal "why"
unasserted (WG).
