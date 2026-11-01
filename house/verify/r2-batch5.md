# Verification plan, round 2 batch 5 (Wilson, 2026-11-01)

Read from: int/r2-b5 head b1ac6ff (merge-base with main = main = d4dad17; contract house/lab-api.md:112-146 plus the
server.py bullets :29-33 and the rcon bullet :54-57). All five branches fork from 620bcc1 (ancestor of d4dad17).
Pins: N2.G1.2.3 a58a45c, N2.G1.C1 61189ce, N2.G3.7.3 eed3aff, N2.G4.1.1 290189f, N2.G5.3 1c09bfa, int b1ac6ff.
If `git rev-parse --short res/<gid>` or `int/r2-b5` differs from the pin, stop and report.
Already run by Wilson on b1ac6ff (Python 3.11.9, node v25.8.1): lever, guard lever, flatten, r2 page, both rcon fake
tests: each `OK`, `EXIT=0`, `git status --short` empty. Real-server tests: not run by Wilson.

## Rules for residents
- Git Bash. One worktree per goal: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v5-<gid> b1ac6ff`, work there, remove it when done.
- Every run line ends `2>&1; echo EXIT=$?`. GREEN: `Ran 1 test` (rcon fake: `Ran 2 tests`), `OK`, `EXIT=0`.
- Mutation: apply with the Edit tool (exact old/new below), run, expect the failure named, then
  `git checkout -- <file>`, re-run to `OK`, and `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool: paste the run output to House;
  only House records runs. Residents NEVER run `taskkill /IM`; a process is stopped only by its own PID.
- Real-server tests (test_server_boot, test_guard_no_orphan_server): at most 2 boots at once across ALL residents
  (test_server_boot = 1 boot, the guard = 2 boots one after the other). Before each run:
  `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"` must print >= 1500;
  below that, wait. Note the PIDs from `tasklist //FI "IMAGENAME eq java.exe"` before and after each real-server run;
  a java PID that appears and stays after the run ends is a defect to report (do not kill other residents' PIDs).

## N2.G1.2.3 server.boot (green a58a45c)
Run: `python lab/tests/test_server_boot.py Lab.server_boots_to_done_and_answers_list 2>&1; echo EXIT=$?`
GREEN: a line `boot_secs=<float> list='There are 0 of a max of 4 players online: '` (commit a58a45c reports
boot_secs=19.02, 20.3 s wall), `Ran 1 test`, `OK`, `EXIT=0`. One boot, ~1 GB.
Mutation A (registry), no orphan: lab/server.py:49 old `    return sum(1 for s in _servers if s.proc.poll() is None)`
new `    return len(_servers)` -> `AssertionError: 1 != 0` at test_server_boot.py:41, `FAILED (failures=1)`; java was
already stopped by `__exit__` (server.py:91-92) before :41.
Mutation B (lead 1, real-server half): lab/rcon.py:43-44 old
`        self._sock.sendall(encode(n, COMMAND, text))` + newline + `        parts = [self._recv()[2]]` + newline +
`        self._sock.sendall(encode(n + 1, RESPONSE, ""))` new
`        self._sock.sendall(encode(n, COMMAND, text) + encode(n + 1, RESPONSE, ""))` + newline + `        parts = []`
(the d4dad17 text). Expected per a58a45c's message: `ConnectionError: rcon connection closed` (rcon.py:65) at
test_server_boot.py:37, `FAILED (errors=1)`; if it is `TimeoutError: timed out` instead, report that text (the EOF
claim is then false). Server.stop still runs (`_ask_stop` swallows OSError, server.py:85), procs.stop waits 30 s then
kills by PID: allow ~60 s. Check no new java PID remains.

## N2.G1.C1 guard no orphan (red 61189ce, green on int)
Run: `python lab/tests/test_guard_no_orphan_server.py 2>&1; echo EXIT=$?`
RED at 61189ce (by reading): `ModuleNotFoundError: No module named 'server'` (import :10), `FAILED (errors=1)`.
GREEN on int: `Ran 1 test`, `OK`, `EXIT=0`. Two boots, sequential; the second is killed at ~0.5-1 s.
Mutation A, no orphan: same as N2.G1.2.3 A (server.py:49) -> `AssertionError: 1 != 0 : running_count is not zero` at
:99 (called from :114), `FAILED (failures=1)`.
Mutation B (lead 2, zero boots): lab/server.py:44 old
`def start_allowed(free_mb: int, running: int, need_mb: int = 1500, cap: int = 3) -> bool:` new
`def start_allowed(free_mb: int, running: int, need_mb: int = 10**9, cap: int = 3) -> bool:` ->
`AssertionError: unexpectedly None : boot did not start a server` at :112, `FAILED (failures=1)`. No java starts.
Mutation C (stuck case bites; the kill is delayed, not removed, so no orphan): lab/server.py:60 old
`    procs.stop(proc, grace=0.0)` new
`    __import__("threading").Timer(15, procs.stop, (proc,), {"grace": 0.0}).start()` -> crash case passes (~20 s), stuck
case fails with `AssertionError: False is not true : scratch folder locked: server still running` at :102 (from :119),
or `... : game port still listening` at :100 if java bound its port within ~0.6 s; `FAILED (failures=1)`. The timer
kills the java ~15 s after it started; the interpreter waits for it before exit. Then check no new java PID, and
remove only the leftover `~/sealrun-lab/tmp*` folder that this run created (it holds `.sealrun-scratch`).

## N2.G3.7.3 lever (green eed3aff)
Run: `python lab/tests/test_lever.py Lab.lever_marks_admin_steps_lab_only 2>&1; echo EXIT=$?` and
`python lab/tests/test_guard_lever_player_legal.py 2>&1; echo EXIT=$?` (goal N2.G3.C4, RED recorded in batch 4:
`ModuleNotFoundError: No module named 'lever'`). GREEN: each `Ran 1 test`, `OK`, `EXIT=0` (Wilson saw both).
Mutation A (slash, per-word loop): lab/lever.py:15 old `    return words[0].removeprefix("/") if words else ""` new
`    return words[0] if words else ""` -> test_lever `FAILED (failures=29)`: 28 subTests (`step='/forceload'` ...
`step='/give 1 2 3'`, `AssertionError: Lists differ: ['player'] != ['admin']`) plus :30 (mixed). Guard:
`AssertionError: Lists differ: ['player', 'admin'] != ['admin', 'admin']` at :12, `FAILED (failures=1)`.
Mutation B (player side): lab/lever.py:6 old `if _word(step) in ADMIN else` new
`if any(_word(step).startswith(a) for a in ADMIN) else` -> `FAILED (failures=8)`: subTests `timer 5`, `kills`,
`stopper`, `giver`, `fills`, `times`, `teleporting` plus :30. Guard stays `OK` (its player steps are walk/break).
Mutation C: lever.py:2 add `, "op"` after `"give"` -> `AssertionError: 15 != 14` at :16, `FAILED (failures=1)`.
(A, B, C were run by Wilson on scratch copies; residents re-run them in the worktree.)

## N2.G4.1.1 flatten (green 290189f)
Run: `python lab/tests/test_flatten.py Lab.flatten_marks_tree_water_iron_and_cliff 2>&1; echo EXIT=$?`
GREEN: `Ran 1 test`, `OK`, `EXIT=0`. TILES (flatten.py:1) equals crates/world/src/grid.rs:3-10 `Tile` bytes.
Mutation A (poppy in PASS): lab/flatten.py:7 old `"dandelion", "poppy", "blue_orchid", "allium",` new
`"dandelion", "blue_orchid", "allium",` -> `AssertionError: Lists differ: [[1, 1, 3, 2], [4, 1, 0, 0], [0, 1, 0, 0]]
!= [[1, 1, 3, 2], [4, 0, 0, 0], [0, 0, 0, 0]]`, `FAILED (failures=1)`.
Mutation B (iron window ground-6): flatten.py:34 old `range(y - 6, y + 1)` new `range(y - 7, y + 1)` -> actual
`[[1, 1, 3, 2], [4, 0, 4, 0], [0, 0, 0, 0]]`, `FAILED (failures=1)`.
Mutation C (cliff >= 2): flatten.py:37 old `abs(ground[(nx, nz)][0] - y) >= 2` new `abs(ground[(nx, nz)][0] - y) > 2`
-> actual `[[0, 0, 3, 2], [4, 0, 0, 0], [0, 0, 0, 0]]`, `FAILED (failures=1)`.
(A, B, C run by Wilson on scratch copies.)

## N2.G5.3 r2 page (green 1c09bfa)
Run: `python site/tests/test_r2_page.py Lab.page_reads_r2_json_and_draws_cards_and_bars 2>&1; echo EXIT=$?`
GREEN: `Ran 1 test`, `OK`, `EXIT=0` (needs node on PATH).
Mutation A: site/r2.html:104 old `    : '<p class="none">not run yet</p>';` new `    : '<p class="none"></p>';` ->
`AssertionError: 'not run yet' not found in 'sealrun round 2 ...'`, `FAILED (failures=1)`.
Mutation B: r2.html:98 old `  const bars = Array.isArray(data.orders)` new `  const bars = true` ->
`AssertionError: node render failed: ... TypeError: Cannot read properties of undefined (reading 'map')`.

## Leads
1. rcon.py split write. TRUE that the loop still collects a multi-packet reply: rcon.py:44 takes the first packet,
   :46-51 append every later id-n packet until id n+1; test_rcon_fake.py:74-75 sends 3 packets, :94 asserts all 8292
   chars; both fake tests `OK` on b1ac6ff. TRUE that the fake tests do NOT cover the change: the d4dad17 combined
   write, monkeypatched in a scratch probe against the same FakeServer, gives `Ran 2 tests`, 0 failures, 0 errors
   (the fake decodes both packets from one buffer, test_rcon_fake.py:56-61). Real-server EOF and the marker reply
   text "Unknown request 0": unverified (claimed in a58a45c's message; the body is discarded at rcon.py:48-51 and the
   bound test prints only the list reply); N2.G1.2.3 Mutation B tests the EOF half. New: rcon.py:44 drops the id
   check for the first packet (see Findings 2).
2. Orphan guard. Stuck case false-GREEN: TRUE. server.py:96-97 raises RuntimeError before Popen when the RAM gate
   refuses; test_guard_no_orphan_server.py:117-118 accepts any RuntimeError and :119's checks then hold with no process.
   Crash case masks a refusal: FALSE. A boot RuntimeError leaves `srv` None and :112 fails (Mutation B shows it).
   Parent closes its boot.out handle: TRUE, server.py:101 `with open(log, "wb") as out:` exits after Popen (:102-109);
   the child keeps its own inherited handle, which is what makes :102's rmtree fail while java lives.
3. Lever per-word loop not shown to bite: TRUE as stated (a removed word trips :16 first; unittest stops at the first
   failing assertion). By scratch run, Mutation A bites 28 subTests in the loop and Mutation B bites 7 PLAYER_STEPS.
4. Flatten. One raise, flatten.py:22-24, covers both a column of all None and a column of only PASS/leaves names:
   the second case is beyond contract :139 ("no non-None block"): TRUE. "Neighbours outside the box are ignored":
   TRUE if the box is the `blocks` dict (:37 `(nx, nz) in ground`, ground built from every column of blocks);
   neighbours outside the w x h rect but inside blocks ARE used; which "box" contract :138 means: unverified.
   Also beyond contract: a column outside the rect raises (probe: all-None column (9, 9), grid(...,0,0,1,1) ->
   `ValueError: no ground block at (9, 9)`).
5. Server. stop idempotent: TRUE, server.py:77-80 (`_code` cached, procs.stop and close run once). `__exit__` on
   error: TRUE, :91-92 calls stop and returns None, so the error propagates. Failed boot never registered: TRUE,
   `_servers.append` only at :123, after Done and RCON; :112/:114 (via `_fail` :60) and :120 stop the process first.
   Consequence: a server between Popen (:102) and :123 is not in running_count, so the cap of 3 does not count
   in-flight boots (contract :114 "counts Servers", so this matches it). RCON listener opening only after the
   `Done (` line (boot connects once, no retry, :118): unverified; a58a45c's message reports ConnectionRefusedError
   when the Done wait is removed.

## Vacuous assertions
- test_r2_page.py: no assertion reads card text or bar height. Run by Wilson on scratch copies, each still `OK`:
  r2.html:101 height -> fixed `height:160px`; r2.html:92 `<h3>${esc(g.title)}</h3>` deleted; r2.html:91
  `data-status="${esc(g.status)}"` -> `data-status="pending"`. Contract :141-143 (title, plain, status, department;
  height by diff; colour by status) is not checked.
- test_flatten.py:56-57 assert only the exception type; the "(x, z)" in the message (contract :139) is unchecked.
- test_guard_no_orphan_server.py:117-119: see lead 2.

## Findings
1. lab/server.py:110-115: the Done wait has no try/except; an exception raised there, e.g. KeyboardInterrupt (Ctrl-C)
   during the ~19 s boot, propagates with the java from :102 still running, never stopped and never in `_servers`
   (running_count() == 0) while it holds both ports. :117-121 guards the same window after Done with
   `except BaseException`; the wait loop does not.
2. lab/rcon.py:44 (changed in a58a45c): the first packet is taken as the reply without checking its id. Input: a
   command that times out (scratch probe, client timeout=1.0, server answers "slow" after 1.5 s), then the same client
   sends `list`. Result: `command("list")` returns `'SLOW REPLYLIST REPLY'`; the d4dad17 loop filtered by id and would
   drop the stale packet. Server.stop reuses the client (`_ask_stop`, server.py:84) after any command error.
3. lab/flatten.py:29: a column inside the grid rect with no entry in `blocks` raises `KeyError: (1, 0)` (probe:
   blocks = one column at (0, 0), `grid(blocks, 0, 0, 2, 1)`), not the ValueError naming (x, z) that contract :139
   asks for a column with no non-None block.
