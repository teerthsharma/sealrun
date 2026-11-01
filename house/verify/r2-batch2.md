# Verification plan, round 2 batch 2 (Wilson, 2026-11-01)

Read from: main 13f802d and branches res/<goal> at 0777a16 (G1.1.2), 2436d04 (G3.1.1), ab86b30 (G3.1.2),
1a7acd8 (G3.4.1), d2ec9fc (G3.4.A1), 10e069b (G2.C3). Python 3.11.9 (`python --version`).

## Rules for residents
- Use the Bash tool (Git Bash). Run every command exactly as written; paste full output verbatim.
- Each goal runs only in its own folder. No step writes in main (C:/Users/seal/Documents/GitHub/sealrun).
  The anvil.py mutation runs in the N2.G2.3 worktree, the rcon.py mutation in the N2.G1.1.2 worktree,
  so no two goals touch one file in one folder; the seven goals can run in parallel.
- Mutation edits use the Edit tool with the exact old and new text below (each old text occurs once).
- After every mutation: `git checkout -- <file>`, the re-run must print `OK` and `EXIT=0` again, and
  `git status --short` must print nothing. If any expected line differs, stop and report the output.
- Read the branch diffs with three dots: `git diff main...res/<goal>`. The two-dot `git diff main res/<goal>`
  shows lab/anvil.py and lab/tests/test_anvil_section.py as deleted on every unmerged branch only because the
  branches start at 0b98c3d, before the N2.G2.3 merge; the three-dot diffs touch only the files named below.

---

## N2.G2.3 anvil.section_blocks (merged)
1. Claim: lab/anvil.py:34-40 decodes a 1.16 section with `bits = max(4, ...)`, `64 // bits` values per long,
   no value spanning two longs, signed longs masked. Most likely wrong: decoding with the pre-1.16 spanning
   layout (value i at bit i*bits). Spanning and padded agree at 4, 8, 16 bits, differ at 5, 6, 9.
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun):
   `cd /c/Users/seal/Documents/GitHub/sealrun && python lab/tests/test_anvil_section.py Lab.padded_packing_5_and_6_bits_not_spanning 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, last line `EXIT=0`.
3. Mutation (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G2.3; its anvil.py equals main's, `git diff main` is empty):
   file lab/anvil.py
   old: `states[i // per] & 0xFFFFFFFFFFFFFFFF) >> ((i % per) * bits)`
   new: `states[i * bits // 64] & 0xFFFFFFFFFFFFFFFF) >> ((i * bits) % 64)`
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G2.3 && python lab/tests/test_anvil_section.py Lab.padded_packing_5_and_6_bits_not_spanning 2>&1; echo EXIT=$?`
   Expect three `FAIL: padded_packing_5_and_6_bits_not_spanning` blocks, subtests `(palette=17)`, `(palette=33)`,
   `(palette=300)`, each at test_anvil_section.py line 43; palette=16 passes; `FAILED (failures=3)`; `EXIT=1`.
   Then `git checkout -- lab/anvil.py`, same command again: `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Extra (earns it: the only check against real game bytes; the bound test checks section_blocks against the
   test's own `pack`). Read-only on the real world. Folder main:
   `cd /c/Users/seal/Documents/GitHub/sealrun && python lab/tests/test_anvil_section.py Lab.real_region_sections_match_padded_layout 2>&1; echo EXIT=$?`
   Expect a line `real sections checked=<N> bit widths={...}` with N > 0, `OK`, `EXIT=0`. Record the bit
   widths verbatim. Line 61 (`len(states) == ceil(4096 / per)`) separates padded from spanning only for a
   width other than 4, 8, 16; if the printed widths hold only those, the real data did not discriminate the layouts.
5. Defects by reading:
   - lab/tests/test_anvil_section.py:36: bound palettes are 16, 17, 33, 300, so `(len(palette) - 1).bit_length()`
     is already >= 4; the `max(4, ...)` floor at lab/anvil.py:35 is not exercised by the bound test. See it: delete
     `max(4, ` and its `)` at anvil.py:35 in the worktree; the bound test still passes (only the real-region
     method, line 58, would catch it).
   - lab/tests/test_anvil_section.py:42 asserts the length of `states` built by the test's own `pack`; it does
     not read anvil.py.

## N2.G1.1.2 rcon.Client vs fake server
1. Claim: lab/rcon.py:27-64 logs in (id -1 raises PermissionError, line 34-35), and `command` sends the command
   (id n) plus a type-0 marker (id n+1, line 43), joining every id-n body until the marker reply (lines 44-50).
   Most likely wrong: returning after the first reply packet, which truncates a long reply the server sends as
   several packets. The fake (lab/tests/test_rcon_fake.py:74-75) answers `big` with three packets in 1000-byte
   writes (line 62-64).
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G1.1.2):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G1.1.2 && python lab/tests/test_rcon_fake.py Lab.rcon_wrong_password_and_long_reply_against_fake 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, last line `EXIT=0`.
3. Mutation: file lab/rcon.py
   old: `parts.append(body)`
   new: `return body`
   Same command. Expect `FAIL: rcon_wrong_password_and_long_reply_against_fake`, `AssertionError` at
   test_rcon_fake.py line 92 (`big` equals only the 4096 a's), `FAILED (failures=1)`, `EXIT=1`. It may take up to
   about 10 s (server thread waits on its 5 s recv timeout, line 47, and join(5), line 32).
   Then `git checkout -- lab/rcon.py`, same command: `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Extra: none. The real server's answer to the type-0 marker ("Unknown request 0") is a hypothesis from memory
   (house/lab-api.md) and belongs to N2.G1.2.3, which boots the server.
5. Defects by reading:
   - lab/rcon.py:58-63: `_recv` catches every ValueError from `decode` as "need more bytes". `decode` also raises
     ValueError for a complete but bad packet (line 18 length < 10, line 22 missing terminator, line 23
     UnicodeDecodeError is a ValueError subclass). Such a packet stays in `_buf` and the client blocks in
     `recv` until the socket timeout, so a malformed reply surfaces as TimeoutError after `timeout` seconds,
     not as ValueError. See it (folder N2.G1.1.2):
     ```
     cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G1.1.2 && python - <<'EOF'
     import socket, sys, threading, time
     sys.path.insert(0, "lab")
     import rcon
     s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
     def serve():
         c, _ = s.accept(); c.recv(99)
         c.sendall(b"\x0a\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00XX"); time.sleep(5)
     threading.Thread(target=serve, daemon=True).start()
     t = time.time()
     try:
         rcon.Client("127.0.0.1", s.getsockname()[1], "pw", timeout=2)
     except Exception as e:
         print(type(e).__name__, round(time.time() - t, 1))
     EOF
     ```
     Expected (by reading, unverified): `TimeoutError 2.0`.

## N2.G3.1.1 blockdiff.diff
1. Claim: lab/blockdiff.py:1-5 returns `changed` (pos, a_name, b_name), `added` (only in b), `missing` (only in
   a), each sorted. Most likely wrong: a/b direction swapped, which reverses "which world had what".
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.1.1):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.1.1 && python lab/tests/test_blockdiff.py Lab.blockdiff_finds_changed_added_and_missing 2>&1; echo EXIT=$?`
   Expect `OK`, last line `EXIT=0`.
3. Mutation: file lab/blockdiff.py
   old: `changed = [(p, a[p], b[p])`
   new: `changed = [(p, b[p], a[p])`
   Same command. Expect `FAIL: blockdiff_finds_changed_added_and_missing`, AssertionError at test_blockdiff.py
   line 17, `FAILED (failures=1)`, `EXIT=1`. Then `git checkout -- lab/blockdiff.py`, same command: `OK`,
   `EXIT=0`; `git status --short` prints nothing.
4. Extra: none.
5. Defects by reading: none. (Fact, not a defect against lab-api.md: a value `None`, which `block_at` returns
   for a non-full chunk, is compared as a name, so it lands in `changed`, not `missing`; blockdiff.py:2.)

## N2.G3.1.2 ores.tally
1. Claim: lab/ores.py:5-12 keys counts by `(x >> 4, z >> 4)` and counts only `minecraft:<ore>_ore` for the seven
   ORES. Most likely wrong: chunk index for negative x/z (truncation toward zero puts x = -1 in chunk 0).
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.1.2):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.1.2 && python lab/tests/test_ores.py Lab.ore_tally_counts_per_chunk 2>&1; echo EXIT=$?`
   Expect `OK`, last line `EXIT=0`.
3. Mutation: file lab/ores.py
   old: `(x >> 4, z >> 4)`
   new: `(int(x / 16), int(z / 16))`
   Same command. Expect `ERROR: ore_tally_counts_per_chunk`, `KeyError: (-1, 0)` at test_ores.py line 17,
   `FAILED (errors=1)`, `EXIT=1`. Then `git checkout -- lab/ores.py`, same command: `OK`, `EXIT=0`;
   `git status --short` prints nothing.
4. Extra: none.
5. Defects by reading: none.

## N2.G3.4.1 orders.py and lab/results/order_squares_more.json
1. Claim: lab/orders.py:9-14 builds a 2x2 square and its 24 permutations; `table()` (lines 17-28) gives 72
   "not run" rows, committed as the JSON. Most likely wrong: a square with a repeated or wrong cell, which still
   yields 24 permutations but fewer distinct orders.
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.1):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.1 && python lab/tests/test_orders.py Lab.square_orders_are_24_distinct_permutations 2>&1; echo EXIT=$?`
   Expect `OK`, last line `EXIT=0`.
3. Mutation: file lab/orders.py
   old: `(cx + 1, cz + 1)]`
   new: `(cx + 1, cz)]`
   Same command. Expect `FAIL: square_orders_are_24_distinct_permutations`, `AssertionError: 12 != 24` at
   test_orders.py line 23, `FAILED (failures=1)`, `EXIT=1`. Then `git checkout -- lab/orders.py`, same command:
   `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Extra (earns it: the bound test never reads the committed JSON; the file has three more unbound methods):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.1 && python lab/tests/test_orders.py Lab.committed_json_equals_table Lab.table_has_72_not_run_rows Lab.squares_are_at_least_32_chunks_apart 2>&1; echo EXIT=$?`
   Expect `Ran 3 tests`, `OK`, `EXIT=0`.
5. Defects by reading:
   - lab/tests/test_orders.py:31 measures distance from chunk (0, 0), not from the world spawn; where seed 7
     puts its spawn is unverified.

## N2.G3.4.A1 squares_plan.plan (guard-style file)
1. Claim: lab/squares_plan.py:1-2 gives one boot per order, each boot visiting every square in that same order.
   Most likely wrong: squares inside one boot not sharing the order, which breaks the one-boot-per-order design.
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.A1):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.A1 && python lab/tests/test_squares_plan.py 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, last line `EXIT=0`.
3. Mutation: file lab/squares_plan.py
   old: `for dx, dz in order]`
   new: `for dx, dz in (order if sx > 0 else order[::-1])]`
   Same command. Expect `FAIL: test_three_squares_one_boot_per_order`, AssertionError at test_squares_plan.py
   line 34 (`self.assertEqual(this, order)`), `FAILED (failures=1)`, `EXIT=1`. Then
   `git checkout -- lab/squares_plan.py`, same command: `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Extra: none.
5. Defects by reading:
   - lab/squares_plan.py:2 reads each order entry as an offset (dx, dz) added to the square corner;
     lab/orders.py:14 (branch res/N2.G3.4.1) `square_orders` yields absolute chunk coordinates. lab-api.md does
     not say which one `plan` takes. Passing one to the other doubles the coordinates. See it:
     `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G3.4.A1 && python -c "import sys; sys.path.insert(0, 'lab'); import squares_plan; print(squares_plan.plan([(64, 64)], [((64, 64), (65, 64), (64, 65), (65, 65))])[0])"`
     Expected: `[(128, 128), (129, 128), (128, 129), (129, 129)]`.
   - lab/tests/test_squares_plan.py:39-40 assert `72 - 24 == 48` and `48 * 20 == 960`; they read no code.

## N2.G2.C3 .gitignore and guard_no_minecraft_in_repo
1. Claim: .gitignore:10-18 add nine Minecraft file names; lab/tests/test_guard_no_minecraft_in_repo.py:36-57
   lists every file in the real server folder, prefixes it with `server-1.16.1/` and `lab/scratch/`, and fails
   if `git check-ignore` does not ignore one. Most likely wrong: a vacuous guard (verdict parsed as "ignored"
   for everything, line 30-32), which would pass while a server file leaks.
2. Re-run (folder C:/Users/seal/Documents/GitHub/sealrun-wt/N2.G2.C3):
   `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G2.C3 && python lab/tests/test_guard_no_minecraft_in_repo.py 2>&1; echo EXIT=$?`
   Expect `Ran 1 test`, `OK`, last line `EXIT=0`.
3. Mutation: file .gitignore
   old: `usercache.json`
   new: `# usercache.json`
   Same command. Expect `FAIL: test_guard_no_minecraft_in_repo`, message containing
   `server files not ignored: server-1.16.1/usercache.json, lab/scratch/usercache.json`, `FAILED (failures=1)`,
   `EXIT=1`. Then `git checkout -- .gitignore`, same command: `OK`, `EXIT=0`; `git status --short` prints nothing.
4. Extra: none.
5. Defects by reading:
   - lab/tests/test_guard_no_minecraft_in_repo.py:32 counts any matching pattern as "ignored". With `-v`, git
     also reports a matching negated pattern (`!name`), which means NOT ignored. No `!` line exists today, so
     this is latent. See it: append a line `!ops.json` to .gitignore, run the re-run command (still `EXIT=0`),
     then `git check-ignore --no-index -q server-1.16.1/ops.json; echo EXIT=$?` prints `EXIT=1` (not ignored);
     then `git checkout -- .gitignore`.
   - The guard covers only files present in the server folder now (16 names plus 7 `.mca`, listed 2026-11-01).
     .gitignore:2 `*.log` does not match a rotated log `*.log.gz`. See it:
     `cd /c/Users/seal/Documents/GitHub/sealrun-wt/N2.G2.C3 && git check-ignore --no-index -v -n server-1.16.1/logs/2026-11-01-1.log.gz; echo EXIT=$?`
     Expected `::` then the path, `EXIT=1`. That the server writes `logs/<date>-<n>.log.gz` on a later boot is
     from memory, unverified.

## uriel / mlm
None earns its cost for this batch: the modules are 2 to 41 lines of stdlib Python with direct tests. No
`research_*` run requested of House.
