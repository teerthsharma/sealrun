# Permissions chart for the unattended six hours (round 2)

Window: owner away 07:34 to 13:34 IST, 2026-11-01. Session runs in bypass-permissions mode, so tool prompts do not block.
What still needs a specific owner yes in any mode: downloads, pushes or publishing, messages, permanent deletion of data that is not our own scratch, credentials, system or security settings. His CLAUDE.md also keeps delete_*, PR merge and push_files on ask.

Checked on this machine at 2026-11-01 (Cameron, read-only):
- RAM 16,092 MB total, 5,631 MB free at the check (other agents and builds share it); disk C: 67 GB free.
- `python` and `cargo` on PATH; `java` is not on PATH, the bundled Java 8u51 exists at the `SEALRUN_JAVA` path.
- Server folder: `server.jar` 37,968,964 bytes, `eula.txt` already `eula=true`, `server.properties` has `server-ip=127.0.0.1` (per brief-r2), `online-mode=false`, `enable-rcon=false`, no java process running now.
- `.minecraft/mods` is empty, no Fabric loader anywhere (`lab/results/fabric_probe.json`: `fabric_loader: []`, `mods: []`).
- sealrun git repo has no remote (`git remote` prints nothing): a push is impossible as configured.
- `cargo fetch --offline --locked` exits 0 in the workspace: the Rust dependencies are already cached, so `cargo test` needs no download.

## The chart

| # | Action | Goals that need it | Bypass mode covers it | Needs a specific owner yes | Cheaper route / note |
|---|--------|--------------------|-----------------------|----------------------------|----------------------|
| 1 | Run `python` (3.11, stdlib only): lab tests, benches, site scripts | every leaf | yes | no | Stdlib only, so no `pip install`, so no download. |
| 2 | Boot a Java 8 server through `subprocess` from a scratch copy, `-Xmx1G nogui`, port per server | G1.2.3, G1.2.4, G1.2.5, G1.4.1, G2.6, G2.8, G3.2.2 to G3.2.4, G3.3, G3.4, G3.5.2, G3.6.3, G4.1.5, G4.1.A1 | yes | no | The jar is the owner's own, copied, never written back. His `eula=true` is carried by the copied `eula.txt`; no new terms are accepted. Keep `server-ip=127.0.0.1` so Windows Firewall has no reason to raise a dialog nobody can click (G1.2.3 should assert the bound address with `netstat` once). |
| 3 | Copy `server.jar` (37,968,964 B), `server.properties`, `eula.txt` into `~/sealrun-lab/<scratch>` | G1.2.1, G1.2.3 | yes | no | Local file copy, not a download. About 38 MB per scratch dir; 20 scratch dirs is under 1 GB of 67 GB free. `*.jar` stays git-ignored, guard `test_guard_no_minecraft_in_repo` keeps it out of the repo. |
| 4 | `taskkill /PID <pid> /T /F` on servers the lab itself started | G1.C1, G1.2.x, every boot test | yes | no | Kill by the PID of our own `Popen` only. Never `taskkill /IM java.exe`: the owner may have his own game open. `procs.stop` already works this way. |
| 5 | RCON to `127.0.0.1` on scratch ports | G1.1.2, G2.6, G3.2.x, G3.5.2, G4.1.5 | yes | no | Loopback only. The RCON password is a random test value written into the scratch `server.properties` only; it is not a real credential and is never printed in reports. |
| 6 | Write under the repo (`lab/`, `lab/results/`, `site/`, `house/`) | all leaves | yes | no | Minecraft files never enter the repo (guard test). |
| 7 | Write inside `sealrun-wt/<goal>` worktrees and `~/sealrun-lab` | all leaves, G1, G2, G3 | yes | no | Both are our own scratch areas. |
| 8 | Delete a scratch world through `serverdir.delete_world` / `server.delete_world` | G1.2.4, G1.2.5, G1.4.1, G3.3.x, G3.4.2, G3.6.3 | yes | no | Allowed only because the function refuses any path outside `~/sealrun-lab` or without the `.sealrun-scratch` marker (G1.C2). That makes it deleting our own throwaway data, not "permanent deletion of the owner's data". The real `server-1.16.1/world` (4 MB) is never a target. |
| 9 | `git add`, `git commit`, `git merge` (local) into `main` in `C:/Users/seal/Documents/GitHub/sealrun` | merge of every `res/N2.*` branch | yes | no | Local git only. Commits carry no Claude attribution and no Co-Authored-By line (owner CLAUDE.md overrides the harness reminder). No signing is configured (`commit.gpgsign` empty), so no passphrase prompt. |
| 10 | `git worktree remove`, `git branch -D` for finished goals | cleanup after merge | yes | no, but avoid | Not needed: 67 GB free and worktrees are small. Leave all `sealrun-wt/*` and `res/*` branches in place; the owner prunes them when back. This keeps the "deleting" count at zero outside rows 8 and 14. |
| 11 | `cargo test -p sealrun-route` / workspace tests, `cargo build` | G4.1.3, G4.2.x, G4.7, G4.C4 | yes | no | Use `--offline --locked`: dependencies are cached (checked), so a missing crate fails loudly instead of downloading. G4.1.3 says no new Rust library is needed. One build is about 2 GB RAM, so run it with at most 1 server up (row 16). |
| 12 | Local web server (`site/serve.py`) on localhost | G5.4, G5.5, G5.A1, G5.C1 | yes | no | Loopback only; stop it at the end of the goal. Reading the page with a browser tool is also local. |
| 13 | Write to the House graph (`house_report`, `house_fact`, goal status) | all, House only | yes | no | Residents do not write the graph; House does. |
| 14 | Delete `~/sealrun-lab/*` scratch roots at the end of the round | cleanup | yes | no | Only through the marker-guarded function (row 8). Not required; skip if in doubt. |
| 15 | Download Fabric loader and speedrunner mods for the multi-world branch | G1.4.3 (and its use in G1.4.4) | no | **yes** | Not needed. Use three vanilla servers on separate ports (G1.4.1). G1.4.3 records "blocked: file list not approved" in `worlds_one_process.json` and G1.4.4 falls back to vanilla by its own text. Arithmetic below. |
| 16 | Start more than one heavy process at once (servers plus cargo builds) | G1.4.1, G1.4.5, G4 builds | yes | no | RAM, not permission, is the limit. See the arithmetic below. |
| 17 | `git push`, `gh pr`, publish the site to GitHub Pages, verify the live deploy | any "site is live" claim, G5.5 | no | **yes** | Nothing to push as configured: the repo has no remote. G5 is complete when the local page at the local address returns the numbers (G5.4). Park the deploy. |
| 18 | Install or update a tool (pip, npm, winget, JDK, Fabric installer) | none planned | no | **yes** | Not needed. Java 8u51 is on disk, Python and Cargo are present. |
| 19 | Open or change a firewall rule, enable RCON on the owner's real server, edit his `server.properties` | none | no | **yes** | Never. RCON is switched on only in scratch copies; the real server folder is read only. |
| 20 | Send messages (mail, chat, GitHub comments) | none | no | **yes** | Not needed. |
| 21 | Enter real credentials or tokens | none | no | **yes** | Not needed. The only secret in play is the generated scratch RCON password (row 5). |

Rows: 21.

## RAM arithmetic (why vanilla replaces the download)

- Vanilla server: `-Xmx1G`, one measured working-set sample 717 MB, budgeted at 1,500 MB each (heap + metaspace + threads).
- 1 server = 1,500 MB; 2 servers = 3,000 MB; 3 servers = 4,500 MB. The cap of 3 holds on a 16,092 MB box.
- Free RAM at the check was 5,631 MB. After 3 servers that leaves 5,631 - 4,500 = 1,131 MB, below one cargo build (about 2,000 MB). So: 3 servers only with no build running; 2 servers (3,000 MB, leaving 2,631 MB) alongside one build.
- `server.start_allowed(free_mb, running, need_mb=1500, cap=3)` already enforces the same numbers at run time, so a busy morning makes the lab run fewer servers, not crash.
- Fabric route, for comparison: one JVM with several worlds would need a loader, mods and probably a client-side game (the speedrunner mods are client mods, a memory-from-training hypothesis, not checked here). Its upside is about one JVM base saved per extra world, at most 2 x 700 MB = 1,400 MB for three worlds. That is not worth a download plus an untested setup while the owner sleeps, and G1.4.4 needs only the vanilla numbers to choose.

## Needs the owner's yes before it can happen

1. Download of the Fabric loader and the speedrunner mods (G1.4.3). No file list is approved, so nothing is downloaded. When the owner wants it he must name: the Fabric loader/installer file name and version, the mod file names and versions, the source site, and the size. File names, source and sizes are unknown size: they cannot be read without downloading or fetching a listing, and none was fetched. Route taken instead: three vanilla servers on separate ports.
2. Any `git push`, pull request, release or GitHub Pages publish (row 17). The sealrun repo has no remote, so there is nothing to push; the live-deploy check on the site is not possible this window.
3. Installing any tool or package (row 18), changing firewall or system settings, or enabling RCON on his real server folder (row 19). None is planned.
4. Sending any message, and entering any real credential (rows 20, 21). None is planned.

## Parked until the owner is back

- G1.4.3 outcome: `worlds_one_process.json` holds "blocked, file list not approved"; G1.4.4 chooses vanilla.
- Any publish of the round 2 site and the "live Pages deploy verified" step from his global site rule.
- Pruning of `sealrun-wt/*` worktrees, `res/*` branches and `~/sealrun-lab/*` scratch roots (kept, not deleted).
- Playing the route in the real game with a bot (later round, per N2.G4).
- Merging anything into a remote main or closing any issue.
