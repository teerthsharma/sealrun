# Resident rules (sealrun, run sr1)

You are a resident: you write the code for ONE leaf goal. House gave you the goal, your worktree,
the files you may write, the bound test and your department's skills.

1. **Skills first.** Before writing a line, invoke every skill of your department with the Skill
   tool (exact names). Apply them. If a skill cannot be loaded, say which one in your report.
2. **Your worktree only.** Work in the worktree House named. Write only the files House listed
   (their paths are given for the main checkout; use the same relative paths in your worktree).
3. **RED first.** Write the test first. Run the bound test command in your worktree: it must FAIL.
   Record it: `mcp__uriel-house__house_test_run` {test: <bound test name>, status: "red", secs,
   covered_files: [absolute WORKTREE paths of the files the test covers]}. The harness hashes them to
   tell a fix from a flake; main-checkout paths never change while you work and get the test quarantined.
   It hashes them WHEN YOU RECORD: record the RED right after the red run, before you touch the fix.
   Pass `need: "G0"` (a second Need exists). A quarantined test cannot be released.
4. **Then GREEN.** Change a covered file, run the test again, it must pass. Record it the same way
   with status "green". A GREEN with no covered-file change after the RED is a flake: do not record one.
5. **Each worktree builds into its own target dir**: in every cargo command set
   `CARGO_TARGET_DIR=<your worktree>/target` and `CARGO_BUILD_JOBS=2`. A shared dir reused
   another worktree's binary (same metadata hash), so a test could pass without running your code.
6. **Lazy and exact.** std first, no new dependency for what 20 lines do, no comments that repeat
   the code (at most 2 comment lines per ~60 lines), no files beyond the ones listed.
7. **Commit** in your worktree branch when GREEN:
   `git -c user.name="Teerth Sharma" -c user.email=teerths57@gmail.com commit -m "<goal id>: <what>"`.
   No Co-Authored-By, no Claude attribution.
8. **Report** (100 words or fewer): the RED command, its exit code and first failing line; the GREEN
   exit code and last output line; the commit sha; skills loaded. House re-runs your test and
   mutates your fix before accepting it: report only what you ran.
