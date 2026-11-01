# Verification plan, round 2 batch 6 (Wilson, 2026-11-01)

Read from: int/r2-b6 head 640856f = main 44a378e + res/N2.G1.2.4 9a501ae (merge 31bc98b) + res/N2.G1.4.3 891432f
(merge 640856f; d2d7f5e adds the oneprocess_worlds contract bullet). Contract: house/lab-api.md:147-161 plus the
server.py bullets :29-34 and :113-124. Guard test file test_guard_reset_scope.py is f5b8685, already on main.
Pins: N2.G1.2.4 9a501ae, N2.G1.4.3 891432f, int 640856f. If `git rev-parse --short res/<gid>` or `int/r2-b6` differs
from the pin, stop and report.
Already run by Wilson on 640856f (Python 3.11.9): test_guard_reset_scope `Ran 1 test`, `OK`, `EXIT=0`;
test_one_process_worlds bound test `Ran 1 test`, `OK`, `EXIT=0`; `git status --short` empty. Every pure mutation below
was run by Wilson on a scratch copy of `lab/` outside the repo. Real-server tests: not run by Wilson.

## Rules for residents
- Git Bash. One worktree per goal: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v6-<gid> 640856f`, work there, remove it when done.
- Every run line ends `2>&1; echo EXIT=$?`. GREEN: `Ran 1 test`, `OK`, `EXIT=0`.
- Mutation: apply with the Edit tool (exact old/new below), run, expect the failure named, then
  `git checkout -- <file>`, re-run to `OK`, and `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool: paste the run output to House;
  only House records runs. Residents NEVER run `taskkill /IM`; a process is stopped only by its own PID.
- Real-server runs (test_server_reset and its mutations): ONE real boot at a time across ALL residents (the bound test
  boots twice, one after the other). Before each run:
  `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"` must print >= 1500;
  below that, wait. Note the PIDs from `tasklist //FI "IMAGENAME eq java.exe"` before and after each real run; a java
  PID that appears and stays after the run ends is a defect to report (do not kill other residents' PIDs).
- After each real run: `ls ~/sealrun-lab`. A `tmp*` folder left behind is a defect to report (see Findings 1): list
  its contents with `ls -la`, report them, and remove only the folder this run created.

## N2.G1.2.4 reset (green 9a501ae)
Run: `python lab/tests/test_server_reset.py Lab.reset_wipes_placed_block_and_leaves_no_java 2>&1; echo EXIT=$?`
GREEN: lines `before reset: 'execute if block 0 100 0 minecraft:gold_block' -> '<text with Test passed>'`,
`after reset: ... -> '<text without Test passed>'`, `reset_secs=<float> (stop + delete + boot)` (expect roughly
20-50 s: stop plus one boot of 19-21 s, contract :158), `Ran 1 test`, `OK`, `EXIT=0`. Two boots in sequence, ~1 GB
each, never both alive. RED on main (by reading): `AttributeError: module 'server' has no attribute 'reset'` at
test_server_reset.py:48, `FAILED (errors=1)`. Report the exact reply texts printed.
Mutation A (delete is what wipes the block), 2 boots: lab/server.py:139 old
`        shutil.rmtree(d / "world")` new `        pass` -> the world survives (Server.stop asks `stop`, which saves
chunks) -> `AssertionError: 'Test passed' unexpectedly found in '<after reply>'` at test_server_reset.py:55,
`FAILED (failures=1)`. Unverified until run: that the save on `stop` keeps the gold block (vanilla behaviour).
Mutation B (stop before delete), 1 boot: lab/server.py:143-144 old
`    srv.stop()` + newline + `    delete_world(srv.scratch["dir"], root)` new
`    delete_world(srv.scratch["dir"], root)` + newline + `    srv.stop()` -> rmtree runs while java holds
world/ files -> expected `PermissionError: [WinError 32] ...` raised at test_server_reset.py:48, `FAILED (errors=1)`;
the file named is unverified (session.lock or a region file). If no file is locked, the second boot on the same
ports fails instead: `RuntimeError: server exited with <code> before Done` or `no Done within 120.0 s`; report which.
The `finally` (:61-64) stops the first java either way; check no new java PID stays.

## N2.G1.C2 guard reset scope (red f5b8685 on main, green on int)
Run: `python lab/tests/test_guard_reset_scope.py 2>&1; echo EXIT=$?` (pure, temp dirs, no server).
RED (Wilson, main's server.py 44a378e in a scratch copy): five subtests each
`AttributeError: module 'server' has no attribute 'delete_world'`, `FAILED (errors=5)`.
GREEN on int (Wilson): `Ran 1 test`, `OK`, `EXIT=0`.
Mutation A (marker): lab/server.py:136 old
`    if not d.is_relative_to(r) or d == r or not (d / serverdir.MARKER).is_file():` new
`    if not d.is_relative_to(r) or d == r:` -> subtest `[b: folder inside root without marker is refused]`
`AssertionError: ValueError not raised` (test :45 via :31), `FAILED (failures=1)`.
Mutation B (resolve): lab/server.py:134 old `    d = Path(scratch_dir).resolve()` new `    d = Path(scratch_dir)`
-> subtest `[d: escape path through root is refused]` `AssertionError: ValueError not raised` (test :55 via :31),
`FAILED (failures=1)`; the unresolved `root/s4/../../outside_d` passes the lexical `is_relative_to` and its world is
deleted.
Mutation C (inside root): lab/server.py:136 old `    if not d.is_relative_to(r) or d == r or` new
`    if d == r or` -> subtests c and d `AssertionError: ValueError not raised`, `FAILED (failures=2)`.
Surviving (gap, see below): dropping ` or d == r` (:136) and dropping the `if (d / "world").exists():` guard (:138)
each stay `OK`.

## N2.G1.4.3 one-process worlds (green 891432f)
Run: `python lab/tests/test_one_process_worlds.py Lab.one_process_many_worlds_measured_or_blocked_with_reason 2>&1;
echo EXIT=$?` (pure). GREEN (Wilson on 640856f): `Ran 1 test`, `OK`, `EXIT=0`. RED on main (by reading):
`ModuleNotFoundError: No module named 'oneprocess_worlds'` at test :9. Do NOT run `python lab/oneprocess_worlds.py`
(it rewrites lab/results/worlds_one_process.json). The real `.minecraft` has `versions/1.16.1` only and an empty
`mods/` (ls), which matches the committed `fabric_loader: [], mods: []`.
Mutation A: lab/oneprocess_worlds.py:12 old `    status = "not run" if loader and mods else "blocked"` new
`    status = "blocked"` -> `AssertionError: 'blocked' != 'not run'` at test :33, `FAILED (failures=1)`.
Mutation B: lab/oneprocess_worlds.py:16 old `            "file list not approved by the owner (house/permissions-6h.md row 15); "`
new `            "file list pending by the owner (house/permissions-6h.md row 15); "` ->
`AssertionError: 'not approved' not found in 'file list pending by the owner (house/permissions-6h.md row 15);
fabric_loader: [], mods: []'` at test :22, `FAILED (failures=1)`.
Mutation C (network import): after lab/oneprocess_worlds.py:1 `import json` add a line `import socket` ->
`AssertionError: <re.Match object; span=(12, 25), match='import socket'> is not None : oneprocess_worlds imports
socket` at test :39, `FAILED (failures=1)`.
Mutation D (committed result): lab/results/worlds_one_process.json:2 old `  "status": "blocked",` new
`  "status": "not run",` -> `AssertionError: 'not run' != 'blocked'` at test :47, `FAILED (failures=1)`.
Surviving (gap, see below): the resident's mutant `"not run" if mods else "blocked"` and `import json, socket` each
stay `OK` (Wilson ran both).

## Leads
1. Leftover tmpqe4qkscz. The folder no longer exists (`ls ~/sealrun-lab/tmpqe4qkscz`: No such file or directory;
   `~/sealrun-lab` is empty), so its contents are unverified. By reading, after Server.stop returns nothing in the
   Python process holds boot.out: the parent's handle closes when `with open(log, "wb")` exits (server.py:103-111);
   Popen closes its child-side duplicates after CreateProcess (Lib/subprocess.py:1553-1555, 3.11.9) and restricts
   inheritance to the three std handles (:1488-1495); the unclosed `proc.stdin` (the ResourceWarning) is a pipe
   handle, not a file in the scratch. procs.stop returns only from `proc.wait()` (procs.py:8 or :11), so java has
   exited. What held boot.out after that: unverified (outside this process; java children, antivirus or indexer are
   candidates, none shown). The listing House reports is not what one failing rmtree pass leaves: on this box
   `os.scandir` lists `.sealrun-scratch, banned-ips.json, banned-players.json, boot.out, eula.txt, logs, ops.json,
   server.jar, server.properties, usercache.json, whitelist.json, world` (probe, same names), and `_rmtree_unsafe`
   stops at the first failure, so a pass failing at boot.out leaves world/ intact. How world/ went: unverified.
   Verified: the marker sorts first, so any partial pass deletes it first (Findings 1). Same cleanup pattern:
   test_server_boot.py:21-32 is identical; test_guard_no_orphan_server.py:39-41 `drop_scratch` uses
   `ignore_errors=True` (deletes what it can, marker included, raises nothing) and `rmtree_within` (:27-36) also
   stops each pass at the first failure.
2. reset after a failed stop: FALSE that delete_world runs with java alive. server.py:143 `srv.stop()` raising
   (e.g. OSError from `subprocess.run(["taskkill", ...])`, procs.py:10, or KeyboardInterrupt in `proc.wait`) leaves
   reset before :144; `_code` stays None (:79-80) so a later stop retries. A normal return means `proc.wait()`
   returned, i.e. java exited. Not covered: a process java itself started (taskkill /T runs only on timeout,
   procs.py:10); none expected, unverified. Risk, unverified: delete_world's one rmtree (:139) has no retry, so a
   post-stop hold like lead 1 on a world/ file makes reset raise OSError with world/ part-deleted and no new server.
3. delete_world: TRUE. Both paths resolved (:134-135), then lexical `is_relative_to` and `d == r` (:136); `d == r`
   refuses the root even with a marker. Junctions (probe on this box, temp dir): `world` as a junction to an outside
   folder -> `OSError: Cannot call rmtree on a symbolic link`, outside file kept; the scratch dir itself a junction to
   a marked outside folder -> ValueError (resolve follows it), outside world kept. A missing world is not an error:
   TRUE, :138 `exists()` guard. Neither the `d == r` clause nor the missing-world clause is tested (Gaps).
4. world_nether / world_the_end: STRUCK. `server-1.16.1/` holds no world_nether or world_the_end; `world/` holds
   `DIM-1`, `DIM1`, `data`, `datapacks`, `level.dat`, `level.dat_old`, `playerdata`, `poi`, `region`, `session.lock`
   (ls, read only). server.properties:36 `level-name=world`, so removing `world/` removes all three dimensions.
   server.properties:45 `level-seed=7`: the reset world regenerates the same terrain, which the test tolerates
   (a gold block never generates).
5. Shared state: `_servers` (server.py:21) is module-level and append-only (:129); `running_count` (:51) counts only
   live procs, so a stopped Server never leaks into a later test. A Server left alive by a failed stop makes every
   later `running_count() == 0` assert fail (test_server_reset.py:60, test_server_boot.py:45,
   test_guard_no_orphan_server.py:51) and takes a cap slot. The bound tests cannot share a process by default: their
   methods lack the `test_` prefix, so `python -m unittest discover` does not collect them; it does collect
   test_guard_no_orphan_server (two real boots). interrupt_during_boot_stops_the_process raises before :129, so it
   adds nothing to `_servers`. Same ports on reboot (reset reuses `srv.scratch`): a bind failure on the second boot
   is unverified; the bound test shows it.

## Gaps (mutants that survive)
- test_guard_reset_scope.py: no subtest passes `root` itself; deleting ` or d == r` (server.py:136) stays `OK`.
  No subtest has a marked folder without `world/`; deleting the `exists()` guard (:138) stays `OK`, and the bound
  test always has a world. Contract :149 "a missing world is not an error" is untested.
- test_one_process_worlds.py: the resident's mutant `"not run" if mods else "blocked"` is NOT equivalent. Input:
  an mc_dir with `mods/a.jar` and no `versions/fabric-loader-*`; contract :152-153 says `blocked` ("no Fabric loader or
  no mods"); int code gives `blocked` (probe), the mutant gives `not run` (probe). The test only feeds "neither"
  (:21) and "both" (:33), so this is a test gap. The loader-only case (`loader and loader` style mutants) is
  likewise untested; int code gives `blocked` for it (probe).
- test_one_process_worlds.py:38-42: the regex needs the network name right after `import`/`from`, so
  `import json, socket` stays `OK`. It reads only the module's own source; after `import oneprocess_worlds`,
  `sys.modules` holds `urllib` and `urllib.parse` (loaded by the stdlib, not by a line of the module; which stdlib
  module: unverified). Whether contract :157 "imports no network library (no urllib ...)" means direct imports
  only: unverified.

## Findings
1. lab/tests/test_server_reset.py:19-30 (same text in test_server_boot.py:21-32): `remove_scratch` returns at once
   when `.sealrun-scratch` is missing, and `shutil.rmtree` deletes `.sealrun-scratch` first (it sorts before every
   server file; scandir probe above) and stops at the first locked file. Input: any file in the scratch still held
   when cleanup runs (House's RED run). Result: the marker is gone, the rest (server.jar ~38 MB, logs, properties)
   stays under `~/sealrun-lab`, every later call skips it, and delete_world refuses it too (no marker); nothing in
   the lab can remove it. test_guard_no_orphan_server.py:39-41 `drop_scratch(..., ignore_errors=True)` reaches the
   same state with no error at all.
2. lab/oneprocess_worlds.py:15-18: the reason is the same text for both statuses. Input: an mc_dir with a
   `versions/fabric-loader-x` folder and `mods/speedrunner.jar` (the test's staged dir). Result: `status "not run"`
   with reason `file list not approved by the owner (house/permissions-6h.md row 15); fabric_loader:
   ['fabric-loader-x'], mods: ['speedrunner.jar']`, i.e. a run that is only not yet measured reports an unapproved
   file list. Contract :155 writes `{"status": "not run", ...}` and does not fix the reason, so this is a defect of
   meaning, not a contract breach.
