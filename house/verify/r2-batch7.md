# Verification plan, round 2 batch 7 (Wilson, 2026-11-01)

Read from: int/r2-b7 head f0d0293 = main ccadeb0 + res/N2.G1.2.5 262e437 (merge 85e40e1) + res/N2.G2.6 d74accc
(merge f0d0293). Contract: house/lab-api.md:162-171 ("Round 2, batch 7"),
plus the real-server facts :158 and server.py / serverdir.py as on f0d0293.
Pins: N2.G1.2.5 262e437, N2.G2.6 d74accc, int f0d0293. If `git rev-parse --short res/<gid>` or `int/r2-b7` differs
from the pin, stop and report. Note: `main` is now 724546d (moved after the int branch was cut from ccadeb0); verify on
f0d0293, not on main.
Already run by Wilson on f0d0293 (Python 3.11.9), pure only: the probes quoted below, and Mutation A of N2.G1.2.5
(fails before any boot). Real-server tests: not run by Wilson. `git status --short` empty after Wilson's probes.

## Rules for residents
- Git Bash. One worktree per goal: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add --detach
  /c/Users/seal/Documents/GitHub/sealrun-wt/v7-<gid> f0d0293`, work there, remove it when done.
- `export PYTHONDONTWRITEBYTECODE=1` first: importing `lab/*.py` otherwise leaves `?? lab/__pycache__/` (seen on
  f0d0293) and `git status --short` is not empty.
- Every run line ends `2>&1; echo EXIT=$?`. GREEN: `Ran 1 test`, `OK`, `EXIT=0`. Always pass the test name: without it
  both files print `Ran 0 tests`, `OK`, `EXIT=0` (Wilson ran both; the methods lack the `test_` prefix).
- Mutation: apply with the Edit tool (exact old/new below), run, expect the failure named, then
  `git checkout -- <file>` (every file the mutation touched), re-run to `OK` only where the plan says, and
  `git status --short` must print nothing.
- Residents NEVER call `house_test_run` or any `house_*` / `mcp__uriel-house__*` tool: paste the run output to House;
  only House records runs. Residents NEVER run `taskkill /IM`; a process is stopped only by its own PID.
- Real-server runs: ONE real boot at a time across ALL residents (the timing test boots twice in sequence, the anvil
  test once). Before each run:
  `python -c "import sys; sys.path.insert(0, 'lab'); import server; print(server.free_mb())"` must print >= 1500;
  below that, wait. Note the PIDs from `tasklist //FI "IMAGENAME eq java.exe"` before and after each real run; a java
  PID that appears and stays after the run ends is a defect to report (do not kill other residents' PIDs).
- Before and after each real run: `ls -A ~/sealrun-lab`. A folder present after and not before is a defect to report
  (Gaps: the timing test only checks the folder its wrapper saw). List it with `ls -la`, and if it holds
  `.sealrun-scratch` remove it with
  `python -c "import sys; from pathlib import Path; sys.path.insert(0, 'lab'); import serverdir; serverdir.remove(Path(r'<dir>'))"`.
- Report for each real run: the printed lines, the boot/reset numbers, and whether another real server was running
  (ask House) when it ran.

## N2.G1.2.5 timing bench (green 262e437)
Run: `python lab/tests/test_lab_timing.py Lab.lab_timing_records_boot_reset_and_peak_ram 2>&1; echo EXIT=$?`
(2 boots in sequence, ~40 s; the resident's commit message says 38.5 s). GREEN: `Ran 1 test`, `OK`, `EXIT=0`.
The test prints nothing on success. Do NOT run `python lab/bench.py`: it rewrites lab/results/lab_timing.json
(bench.py:85); the test only reads that file (test :44-51), it never writes it.
RED on main (by reading): `ModuleNotFoundError: No module named 'bench'` at test_lab_timing.py:10.
Mutation A (unit, pure, fails before any boot; Wilson ran it on a scratch copy): lab/bench.py:47 old
`        return c.PeakWorkingSetSize / MB` new `        return c.PeakWorkingSetSize / 1024` ->
`AssertionError: 27116.0 not less than 2000` (number varies, ~19000-28000) at test_lab_timing.py:22,
`FAILED (failures=1)`, `Ran 1 test in 0.00xs`; no java starts (tasklist before/after unchanged).
Mutation B (scratch folder left), 2 boots: lab/bench.py:68 old `        serverdir.remove(scratch["dir"])` new
`        pass` -> `AssertionError: True is not false : measure left its scratch folder C:\Users\seal\sealrun-lab\tmp...`
at test_lab_timing.py:42, `FAILED (failures=1)`. The folder stays with its marker: remove it with the
`serverdir.remove` line from the rules, then `ls -A ~/sealrun-lab` must not list it.
Mutation C (second scratch through make_scratch), 2 boots: after lab/bench.py:55
`    scratch = serverdir.make_scratch(SRC, root)` add a line `    serverdir.make_scratch(SRC, root)` ->
`AssertionError: 2 != 1` at test_lab_timing.py:41, `FAILED (failures=1)`. The extra folder (server.jar, eula.txt,
server.properties, marker) is left: remove it as in the rules.
Mutation D (second folder by another route; expected to SURVIVE, see Gaps), 2 boots: after lab/bench.py:55 add a
line `    __import__("tempfile").mkdtemp(dir=root)` -> expected `OK`; `ls -A ~/sealrun-lab` afterwards lists one empty
`tmp*` folder. Remove it with `rmdir` (it is empty; check with `ls -A` first). Report OK or not.
Mutation E (peak counter; expected to SURVIVE, lead 1), 2 boots: lab/bench.py:47 old
`        return c.PeakWorkingSetSize / MB` new `        return c.WorkingSetSize / MB` -> expected `OK`
(the resident reported 1/1 OK in 262e437's message). Report OK or not.
Mutation F (reset timing; expected to SURVIVE, see Gaps), 2 boots: lab/bench.py:63 old
`        reset_secs = time.monotonic() - t0` new `        reset_secs = srv.boot_secs` -> expected `OK` (the second
boot alone is inside 5-120 s). Report OK or not.
Mutation G (committed result), 2 boots: lab/results/lab_timing.json:8 old `  "runs": 1` new `  "runs": 2` ->
`AssertionError: 2 != 1` at test_lab_timing.py:51, `FAILED (failures=1)`.

## N2.G2.6 anvil live (green d74accc; test file only)
Run: `python lab/tests/test_anvil_live.py Lab.reader_matches_setblock_on_live_server 2>&1; echo EXIT=$?`
(1 boot, ~20 s). GREEN: five lines `setblock <x> <y> <z> minecraft:<name> -> '<reply with Changed the block>'`,
five lines `block_at <x> <y> <z> -> 'minecraft:<name>'` in the order gold, diamond, emerald, lapis, redstone,
`block_at 1 100 0 (next to gold) -> '<name, not gold_block>'`, `Ran 1 test`, `OK`, `EXIT=0`. Paste the exact
neighbour reply. RED: none real; the test passes on main's anvil.py (only the test file is new; the resident made RED
by a wrong expectation and restored it, per House's lead). The mutations below are the evidence that it can fail.
Mutation A1 (x/z swap in the section index), 1 boot: lab/anvil.py:67 old
`(y & 15) * 256 + (z & 15) * 16 + (x & 15)]` new `(y & 15) * 256 + (x & 15) * 16 + (z & 15)]` ->
`AssertionError: '<other name>' != 'minecraft:emerald_block'` at test_anvil_live.py:44, `FAILED (failures=1)`; the
gold and diamond `block_at` lines print the right names (x&15 == z&15), emerald is the first mismatch.
Mutation A2 (same swap, emerald removed), 1 boot: Mutation A1 plus lab/tests/test_anvil_live.py:18 old
`    "emerald_block": (-1, 70, 0),` + newline new (nothing: delete the line) ->
`AssertionError: '<other name>' != 'minecraft:lapis_block'` at :44 (the mutant reads (4, 5, 3)). Restore both files.
Mutation A3 (same swap, emerald and lapis removed), 1 boot: A2 plus delete :19 `    "lapis_block": (3, 5, 4),` ->
`AssertionError: 'minecraft:air' != 'minecraft:redstone_block'` at :44 (the mutant reads (9, 200, 7); `air` is
unverified, any non-redstone name confirms). Restore both files.
Mutation B (chunk x/z swap), 1 boot: lab/anvil.py:61 old `    level = _level(region_dir, x >> 4, z >> 4)` new
`    level = _level(region_dir, z >> 4, x >> 4)` -> `AssertionError: None != 'minecraft:emerald_block'` at :44
(chunk (0, -1) is read; expected not `full`, so None; a different block name is equally a pass for this mutation;
report which). Only emerald can catch this one: the other four sit in chunk (0, 0).
Mutation C (palette width; outcome unverified, probe), 1 boot: lab/anvil.py:38 old
`    bits = max(4, (len(palette) - 1).bit_length())` new `    bits = 4` -> report `OK` or the failure. `OK` means no
placed block sits in a section with more than 16 palette entries (see lead 4 and Gaps).

## Leads
1. WorkingSetSize mutant survives: TRUE. bench.py:47 reads `PeakWorkingSetSize`; the test checks own process 1-2000
   (test :20-22) and java 200-2000 (:37, :49). Probe on this box (3.11.9, this process): at start peak 19.0 MB,
   working set 19.0 MB (equal, so :20-22 cannot tell them apart); after `b = b"\x01" * (300 * MB)`: 319.0 / 319.0;
   after `del b`: peak 319.0, working set 19.0. Java is read right after `Done (` (bench.py:60) and right after the
   second boot (:64), when its working set is near its peak, so 800.2 MB either way. Smallest input that tells them
   apart: in the test process, allocate and free a written block of >= 100 MB before the call
   (`b = b"\x01" * (100 * bench.MB); del b`), then `bench.peak_mb(os.getpid()) >= 100 + <start value>`; the mutant
   returns the post-free working set (~19 MB in the probe). Pure, no server.
2. make_scratch wrapper: it cannot hide a leak of a scratch made through `serverdir.make_scratch`. bench.py:55 calls
   it as a module attribute, so `mock.patch.object(serverdir, ...)` (test :33) sees the call; `side_effect=record`
   calls the saved real function (:26, :29) and returns its dict. A second call fails :41 (`len(made) == 1`,
   Mutation C); a folder kept fails :42 (Mutation B). server.reset reuses `srv.scratch` (server.py:145) and
   `grep -n "make_scratch\|mkdtemp" lab/*.py` outside serverdir.py hits only bench.py:55, so f0d0293 has one scratch
   per measure. It CAN hide a folder made by any other route (`tempfile.mkdtemp`, `shutil.copytree`): nothing in the
   test lists ROOT (Mutation D, Gaps). Deviation from contract: the contract text :162-168 says "always stopped and
   `serverdir.remove`d" and has no "ROOT holds no tmp* folder" clause on f0d0293; the clause is in House's brief only
   (unverified from the repo).
3. lab_timing.json: measure() takes each number from a measurement: `free_mb_before` from `server.free_mb()`
   (bench.py:53, GlobalMemoryStatusEx, server.py:38-43); `when` from `datetime.now()` (:54); `boot_secs` from
   `srv.boot_secs`, monotonic from before Popen to the `Done (` line (server.py:102, :122); `reset_secs` monotonic
   around `server.reset` (bench.py:61-63: stop + delete_world + boot); `peak_mb` max of two reads (:60, :64). `xmx`
   and `runs` are constants, as the contract says. Whether the committed file came from `python lab/bench.py`:
   unverified; the test never compares it to a run (Gaps). Consistent with it: key order equals the dict
   (bench.py:69-77), blob is `json.dumps(indent=2)` + `\n` (git show 262e437:lab/results/lab_timing.json, LF; the
   working tree has CRLF through core.autocrlf=true), `when` 09:15:25 is after the contract commit 89e1b2a
   (09:13:52) and before 262e437 (09:21:36). Inflation: boot_secs 26.23 is outside the contract's alone figure
   "19.0-21.0 s alone" and near "27 s with a second boot running" (lab-api.md:158); reset_secs 17.45 (stop, delete
   and a full boot that regenerates the world) is 8.78 s shorter than the first boot alone. Cause unverified. The
   file records nothing about other servers: its seven keys hold no java count or concurrency field; only
   `free_mb_before` 5838 describes the machine.
4. x/z swap caught only by emerald: STRUCK as stated. The section-index swap (anvil.py:67) changes the cell for every
   block with x&15 != z&15: lapis local (3, 4) -> reads (4, 5, 3), index 1332 instead of 1347; redstone local (7, 9)
   -> reads (9, 200, 7). Gold (0, 0) and diamond (15, 15) are blind; emerald x=-1 -> local (15, 0) reads (-16, 70, 15).
   Emerald is the only one SEEN failing because the loop asserts in dict order (test :41-44) and stops at the first
   mismatch, emerald being third. Mutations A2/A3 show lapis and redstone each catch it alone. The chunk-coordinate
   swap (anvil.py:61, Mutation B) is the one only emerald catches. Sections: chunk (0, 0) gets lapis y=5 in section 0,
   diamond y=70 in section 4, gold y=100 in section 6, redstone y=200 in section 12; emerald is section 4 of chunk
   (-1, 0), which is also region r.-1.0.mca against r.0.0.mca. So y=5 and y=200 are distinct sections: TRUE. Distinct
   palette widths: unverified. Source world (server-1.16.1/world, seed 7, read only, 529 full chunks): section Y=0
   has more than 16 palette entries (5+ bits) in 67/529 chunks, Y=4 in 98/529, Y>=7 always a single entry
   (`minecraft:air` in chunk (-3, 1)). Chunks (0, 0) and (-1, 0) are not in that world (spawn 128, 63, 192), so their
   widths are unknown; Mutation C reports it. Redstone at y=200 lands in a one-entry air section that setblock grows to
   two entries (4 bits), by reading.
5. Shared state and cleanup. Each test runs in its own Python process; `server._servers` (server.py:21) and the
   3-server cap (:46-51) are per process, so the only cross-process gate is free RAM (:98). Ports come from
   `_free_port` (serverdir.py:179-182), bind-and-release, so two processes booting at once can race for a port
   (unverified; the one-boot rule excludes it). Both tests use ROOT `~/sealrun-lab` (bench.py:81 default,
   test_lab_timing.py:14, test_anvil_live.py:14). Cleanup: `serverdir.remove` (serverdir.py:156-176) skips the
   marker until every other child is gone and retries OSError for 10 s, so a held file no longer strips the marker
   first (batch 6 Finding 1 does not apply to these two tests). Java: anvil test stops in try (:38) and again in
   finally (:49-50; second call returns the cached `_code`, server.py:79-82); bench.measure stops the current `srv`
   in finally (:65-67); a failed boot stops its own proc (server.py:115-121, :125-127); a reset that fails after the
   first stop leaves `srv` pointing at the stopped server, and no second java exists unless boot succeeded. Not
   covered: `serverdir.remove` raising in a finally replaces the original exception (bench.py:68,
   test_anvil_live.py:51); `make_scratch` failing after `mkdtemp` (serverdir.py:186-189) leaves a folder without a
   marker, outside both try blocks (bench.py:55, test_anvil_live.py:27).

## Gaps (mutants that survive)
- test_lab_timing.py:20-22, :37, :49: `PeakWorkingSetSize` -> `WorkingSetSize` (bench.py:47) stays `OK`; at the
  moments read, peak and current are equal or near (probe: 19.0 / 19.0 at start). Lead 1 gives the input that
  separates them (allocate and free >= 100 MB, then read own peak).
- test_lab_timing.py:36: `reset_secs = srv.boot_secs` (bench.py:63) stays inside 5-120 s, so a reset timed without
  the stop and the delete passes (by reading; Mutation F confirms). Nothing ties reset_secs to boot_secs or to stop
  time.
- test_lab_timing.py:44-51: the committed lab_timing.json is checked only for its key set and the same ranges; any
  hand-typed values inside 5-120 / 200-2000 with `xmx` "1G" and `runs` 1 pass. `free_mb_before` and `when` are never
  checked in either dict (e.g. `"free_mb_before": 0` in bench.py:74 stays `OK`, by reading). Contract :168 "Numbers
  are measured, never typed in" is untested.
- test_lab_timing.py:33-42: a folder made under ROOT by any route other than `serverdir.make_scratch` is not seen
  (Mutation D); the test never lists ROOT.
- test_anvil_live.py: the chunk-coordinate swap (anvil.py:61) is caught by emerald alone (Mutation B); dropping the
  emerald line from PLACED would leave it uncaught. Whether any placed block sits in a section wider than 4 bits is
  unverified, so `bits = 4` (anvil.py:38) may survive (Mutation C reports it); the 5-7 bit cases rest on the pure
  tests, not on this live one.

## Findings
1. lab/results/lab_timing.json:2 `"boot_secs": 26.23`: the committed boot time is not a lone-boot number by the
   contract's own measurement (lab-api.md:158: 19.0-21.0 s alone, 27 s with a second boot running), and the same
   file's reset_secs 17.45 (:3), which includes a stop, a world delete and a full boot, is 8.78 s shorter. Input: the
   resident's one run at 2026-11-01T09:15:25+05:30 (:7) with, per House, another real server booting. Result: a
   boot figure ~25-38 % above the 19-21 s lone boot is recorded with `runs` 1 (:8) and no field saying another server
   ran; the file cannot tell a reader the number is inflated. Cause (concurrent boot, cold cache): unverified.
2. lab/bench.py:52-77 with test_lab_timing.py:44-51: the result file is never produced or compared by the test.
   Input: lab_timing.json edited by hand to `"boot_secs": 50.0, "reset_secs": 50.0, "peak_mb": 500.0` (keys
   unchanged). Result: the bound test stays `OK` (by reading: :47-51 are range checks only), so the contract's
   "measured, never typed in" (:168) holds only by the resident's word in 262e437's message.
