# Verify r2 fixes eba8b85 (rcon) and 5ffabe1 (guard negation)

Main checkout C:/Users/seal/Documents/GitHub/sealrun, HEAD d096101 (both fixes are ancestors), Python 3.11.9.
Run each block in a fresh worktree: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree add ../sealrun-wt/verify-r2 d096101`,
then `cd /c/Users/seal/Documents/GitHub/sealrun-wt/verify-r2`. Never mutate the main checkout.
Tools: record every run with `mcp__uriel-house__house_test_run` {test: <name House bound>, status, secs,
covered_files: [absolute WORKTREE paths], need: "N2.G0"}; record the RED right after the red run, before restoring.
Bound test names: unverified (ask House). mlm tools: none apply (CPU-only unittest, no GPU, tensor or run ledger step).

## Fix 1: eba8b85, lab/rcon.py `_recv` (lines 55-65)
Covered files: lab/rcon.py, lab/tests/test_rcon_fake.py.
Note: the test methods have no `test_` prefix, so `python -m unittest discover` collects none of them; name them explicitly.
1. GREEN on the fix:
   `python lab/tests/test_rcon_fake.py Lab.malformed_reply_raises_value_error_fast 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, `EXIT=0`, test time under 1 s.
   Regression guard, same file: `python lab/tests/test_rcon_fake.py Lab.rcon_wrong_password_and_long_reply_against_fake 2>&1; echo EXIT=$?`
   Expect `OK`, `EXIT=0` (the `big` reply arrives in 1000-byte writes, test_rcon_fake.py:62-64, so partial packets must still be waited for).
   Also `python -m unittest lab/tests/test_rcon_packet.py 2>&1; echo EXIT=$?` expects `EXIT=0`.
2. Mutation (the fix is a 9-line hunk, not one line; restore the pre-fix file):
   `git show eba8b85^1:lab/rcon.py > lab/rcon.py`
   This brings back the `try: decode ... except ValueError: recv more` loop.
3. Expected RED, same command as step 1:
   `ERROR: malformed_reply_raises_value_error_fast`, traceback ending `TimeoutError: timed out`
   (socket timeout=5, test_rcon_fake.py:105), `FAILED (errors=1)`, `EXIT=1`, after about 5-10 s
   (5 s socket timeout plus the server thread join(5), test_rcon_fake.py:32).
   Reason: the garbled packet (test_rcon_fake.py:76-77, full length, terminator `XX`) stays at the head of `_buf`,
   `decode` raises `missing terminator` (rcon.py:22-23) on every pass, the old loop treats it as "need more bytes".
   Restore: `git checkout -- lab/rcon.py`, re-run step 1: `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Output that means the fix is wrong:
   - step 3 passes (test does not tell the fixed code from the old one);
   - step 1 fails on `assertLess` (ValueError raised but after >= 1 s) or raises TimeoutError/ConnectionError;
   - the `big` regression test fails or hangs (fix broke partial-packet reads).
   By reading, not covered by the bound test: a header with a huge length (e.g. 0x7fffffff) still makes the
   fixed `_recv` wait for 4+length bytes (rcon.py:59) and end in TimeoutError, not ValueError.

## Fix 2: 5ffabe1, lab/tests/test_guard_no_minecraft_in_repo.py:32
Covered files: lab/tests/test_guard_no_minecraft_in_repo.py, .gitignore.
Needs the server folder C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1 (or `SEALRUN_SERVER`); it exists.
1. GREEN on the fix:
   `python lab/tests/test_guard_no_minecraft_in_repo.py 2>&1; echo EXIT=$?` expects `Ran 1 test`, `OK`, `EXIT=0`.
2. Control: the current .gitignore has no `!` line (`grep -n '^!' .gitignore` prints nothing) and there is no
   core.excludesFile, so the mutation alone changes nothing. Add a negation in the worktree first:
   `printf '!eula.txt\n' >> .gitignore`
   With the fix, re-run step 1. Expect `FAIL: test_guard_no_minecraft_in_repo`, message
   `server files not ignored: ... server-1.16.1/eula.txt ... lab/scratch/eula.txt`, `FAILED (failures=1)`, `EXIT=1`.
   Check the raw line: `git check-ignore --no-index -v -n server-1.16.1/eula.txt` prints `.gitignore:19:!eula.txt<TAB>server-1.16.1/eula.txt`.
   Record this run RED (the guard sees the leak).
3. Mutation, one line, file lab/tests/test_guard_no_minecraft_in_repo.py line 32:
   old: `verdict[path] = source != "::" and not source.split(":", 2)[2].startswith("!")`
   new: `verdict[path] = source != "::"`
   Same command, negation still in place. Expect `OK`, `EXIT=0`: the reverted guard reports the negated file as
   ignored and misses the leak. Here the mutation shows as a wrong GREEN, not a RED; that is the discriminating output.
   Restore: `git checkout -- lab/tests/test_guard_no_minecraft_in_repo.py .gitignore`, re-run step 1:
   `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Output that means the fix is wrong:
   - with the fix and `!eula.txt` in place the test passes (negation not detected);
   - with no negation line the fixed test fails (false leak, e.g. `IndexError` from `split(":", 2)[2]`);
   - by reading: `split(":", 2)[2]` assumes the source has no drive colon. A negation in an excludes file named by
     an absolute Windows path (`C:/...:3:!x`) would yield `[2] == "3:!x"` and be missed. No such file is configured now
     (`git config --show-origin core.excludesFile` prints nothing); unverified for other machines.

## Report back
Per fix: each command, exit code, first failing line, wall seconds, and the house_test_run ids recorded.
Remove the worktree after: `git -C /c/Users/seal/Documents/GitHub/sealrun worktree remove ../sealrun-wt/verify-r2`.
