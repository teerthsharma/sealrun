# Lab interface (round 2, fixed by House)

Residents build to these names so separate leaves merge into one working lab.
Python 3.11 stdlib only. `lab/` is a flat folder of modules, not a package.

## Test files
- `lab/tests/test_<x>.py`, `unittest`, one `class Lab(unittest.TestCase)`, `unittest.main()` under `__main__`.
- Bound cmd `python lab/tests/test_x.py Lab.<name>`: the method is named exactly `<name>`.
- Guard files (cmd with no test name): the method is `test_<name>` so plain discovery runs it.
- Import lab modules with `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`, then `import rcon`.
- Tests use `tempfile` folders and fakes. Only tests whose goal says so boot the real server.

## Paths (environment variable, then default)
- `SEALRUN_SERVER` = `C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1` (read only, never written)
- `SEALRUN_JAVA` = `C:/Users/seal/Desktop/sanitised mineraft/.minecraft/runtime/jre-legacy/windows/jre-legacy/bin/java.exe`
- `SEALRUN_LAB` = `~/sealrun-lab` (scratch root, outside the repo)

## Modules
- `rcon.py`: `LOGIN=3`, `COMMAND=2`, `RESPONSE=0`;
  `encode(req_id: int, ptype: int, body: str) -> bytes`;
  `decode(buf: bytes) -> tuple[int, int, str, bytes]` = (req_id, ptype, body, rest), `ValueError` on a short or bad packet.
  Later (N2.G1.1.2): `class Client(host, port, password)` with `command(text) -> str`, `close()`.
- `serverdir.py`: `MARKER = ".sealrun-scratch"`;
  `make_scratch(src: Path, root: Path) -> dict` with keys `dir` (Path), `port`, `rcon_port`, `rcon_password`.
  Copies `server.jar`, `server.properties`, `eula.txt` (never `world/`), writes `MARKER` in `dir`,
  sets `enable-rcon=true`, `rcon.port`, `rcon.password`, `server-port`. Never writes `src`.
- `procs.py`: `stop(proc: subprocess.Popen, ask=None, grace: float = 10.0) -> int`: calls `ask()` if given,
  waits `grace` seconds, then kills the process tree (`taskkill /PID <pid> /T /F`); returns the exit code.
- `server.py` (N2.G1.2.3, N2.G1.2.4):
  `start_allowed(free_mb: int, running: int, need_mb: int = 1500, cap: int = 3) -> bool`;
  `free_mb() -> int`; `running_count() -> int`;
  `boot(scratch: dict) -> Server`, raising `RuntimeError` before any process starts when `start_allowed` is false;
  `delete_world(scratch_dir: Path, root: Path) -> None`, raising `ValueError` unless `scratch_dir` is inside `root`
  and holds `MARKER`; then removes `scratch_dir / "world"`.
- `nbt.py`: `read(data: bytes) -> tuple[str, object]` = (root name, value). Compound is `dict`, list is `list`,
  byte/int/long arrays are `list[int]`, strings are `str`.
- `anvil.py`: `present(region_path) -> list[tuple[int, int]]` (local 0..31 chunk coords, sorted);
  `chunk_data(region_path, lx, lz) -> bytes | None` (inflated NBT bytes);
  later `section_blocks(palette, states) -> list[str]`, `block_at(region_dir, x, y, z) -> str | None`,
  `chunk_status(region_dir, cx, cz) -> str | None`. A chunk whose status is not `"full"` answers `None`.
- `fabric_probe.py`: `probe(mc_dir: Path) -> dict`; `python lab/fabric_probe.py` writes `lab/results/fabric_probe.json`.

## Round 2, batch 2
- `rcon.Client(host, port, password, timeout=10.0)`: logs in on construction; a reply id of -1 raises
  `PermissionError`. `command(text) -> str` sends the command (type 2, id n), then a marker packet (type 0, id n+1),
  and joins every reply body with id n until the marker's reply arrives (hypothesis from memory: the server answers
  an unknown type with "Unknown request 0"; N2.G1.2.3 confirms it on the real server). `close()`.
- `anvil.section_blocks(palette: list[str], states: list[int]) -> list[str]`: 4096 names, index `y*256 + z*16 + x`;
  `bits = max(4, (len(palette) - 1).bit_length())`, `64 // bits` values per long, no value spans two longs,
  longs arrive signed from NBT.
- `blockdiff.diff(a: dict, b: dict) -> dict` with `changed` [(pos, a_name, b_name)], `added` [(pos, b_name)],
  `missing` [(pos, a_name)], each sorted by pos; pos is (x, y, z).
- `ores.ORES = ("diamond", "iron", "coal", "gold", "lapis", "redstone", "emerald")`;
  `tally(blocks: dict) -> dict[(cx, cz), dict[str, int]]`, `cx = x >> 4`, counts `minecraft:<ore>_ore` only.
- `orders.SQUARES = [(64, 64), (-64, 64), (64, -64)]` (chunk coords of each 2x2 square's corner, far from spawn);
  `square(cx, cz) -> [(cx, cz), (cx + 1, cz), (cx, cz + 1), (cx + 1, cz + 1)]`;
  `square_orders(cx, cz) -> list of 24 tuples`; `table() -> dict` written to `lab/results/order_squares_more.json`.
- `squares_plan.plan(squares, orders) -> list[list[(cx, cz)]]`: one boot per order, all squares in that order;
  `orders` are corner offsets, so pass `orders.square_orders(0, 0)`, never a square's absolute orders.

## Round 2, batch 3
- `anvil.block_at` / `chunk_status`: region file `r.{cx >> 5}.{cz >> 5}.mca`, local `(cx & 31, cz & 31)`, `cx = x >> 4`;
  section `y >> 4`, index `(y & 15)*256 + (z & 15)*16 + (x & 15)`; status is `Level.Status`. `chunk_status` gives the
  raw string, or None for a missing file or chunk. `block_at` gives None unless the status is `"full"`.
  Known value for tests: y = 0 of a full overworld chunk is `minecraft:bedrock` (real files under
  `SEALRUN_SERVER/world/region`, read only; `r.-1.0.mca` holds negative x).
- `window.chunk_blocks(level: dict) -> dict[(x, y, z), str]` from a parsed chunk's `Level` compound, using only
  `xPos`, `zPos` and each section's `Y`, `Palette`, `BlockStates`; `window.fingerprint(blocks: dict) -> str` is the
  sha256 of the sorted items. (Written by N2.G2.5; the N2.G3.C1 guard imports it.)
- `orderrun.wait_loaded(client, cx, cz, timeout=30.0, poll=0.5, sleep=time.sleep) -> bool`: sends
  `forceload add {cx*16} {cz*16}` once, then repeats `execute if block {cx*16} 0 {cz*16} minecraft:bedrock` until a
  reply contains `Test passed` (True) or `timeout` runs out (False). `client` is anything with `command(text) -> str`.
  Reply texts are a hypothesis from memory; N2.G3.2.2 checks them on the real server.
- `edits.commands(edits, loaded) -> list[str]`: `edits` are `(op, x, y, z, block)` with op `"break"` or `"place"`;
  break gives `setblock x y z minecraft:air`, place gives `setblock x y z <block>`. `loaded` is a set of finished,
  loaded `(cx, cz)`; any edit outside it raises `ValueError` naming the chunk, and no list is returned.
- `aim.best_order(rows) -> dict`: rows are `{"order": [[cx, cz], ...], "diamonds": int | None}`, None rows ignored.
  No numbers: `{"lever": None, "reason": "not run"}`; all equal: `{"lever": False, "diamonds": n, "reason": "all
  orders equal"}`; else `{"lever": True, "order": <first row with the max>, "diamonds": max, "mean": mean}`.
- Result file (every `lab/results/order_*.json` from batch 4 on): `{"seed", "area", "height", "orders": int,
  "control": {"repeat_diff": int | None}, "lever": true | false | null, ...}`.
  `verdict.statements(paths) -> list[str]`, one per path: a missing file gives `"<file name>: not run"`; otherwise
  the statement names seed, area, height and orders; `repeat_diff` None gives "noise floor not measured" and no
  claim that order matters; `repeat_diff > 0` gives "shaky"; `lever` false ends with `"next route: " +
  verdict.NEXT_ROUTE` (`"edit the border band before the neighbour is built (N2.G3.5)"`).

## Round 2, batch 4
- `window.box(region_dir, lo, hi) -> dict[(x, y, z), str | None]` for every position with lo <= pos <= hi (inclusive,
  absolute coords), None where `block_at` gives None; `chunk_blocks` and `fingerprint` as in batch 3. A section with
  no `Palette` (real data has a `Y = -1` section holding only `Y`) is skipped by `chunk_blocks`, never a KeyError.
- `lever.py` (no leaf writes it yet; chart gap, Foreman adds one): `lever.ADMIN = {"forceload", "setblock", "fill",
  "tp", "teleport", "gamerule", "time", "weather", "execute", "save-all", "stop", "kill", "summon", "give"}`;
  `lever.kinds(steps: list[str]) -> list[str]`, each `"admin"` when the first word (without `/`) is in ADMIN, else
  `"player"`; `lever.label(steps) -> str` = `"lab-only"` if any step is admin, else `"player-legal"`.
- `aim.accept(found: int, replays: list[int], default: int | None) -> dict` (to be added by N2.G3.6.3): `{"accepted":
  True}` only when there are at least 2 replays, every replay equals `found`, `default` is not None and `found >
  default`; otherwise `{"accepted": False, "reason": "..."}`.
- `site/build_r2.py`: `build(charts_dir: Path, status: dict[str, str]) -> dict` merges `site/charts/r2/{foreman,
  chase,cameron}.json` cards by goal id with the status (missing id gives `"pending"`); the department of a goal is the
  one whose `departments.json` list holds its nearest listed ancestor: the id itself, then its parent (`N2.G3.6.1`,
  `N2.G3.6`, `N2.G3`), never `"N2"`; None when no ancestor is listed. Status comes from `site/r2_status.json`
  (`{gid: status}`, exported by House after each report). `python site/build_r2.py` writes `site/r2.json`.
  `r2.json` carries `"route": {"played": false, "note": "planned on a map, not yet played in the real game"}` until a
  played result file exists.
- `site/r2_numbers.py`: `numbers(results_dir: Path) -> dict[str, dict | str]`, read from disk on every call (no
  cache): each expected result file name maps to its parsed JSON, or to the string `"not run"` when missing. A missing
  number is never 0.
- `lab/fractal.py`: `variogram(heights: dict[(x, z), float], lags: list[int]) -> list[(lag, gamma)]` with gamma =
  half the mean squared height difference over pairs at that lag along x and z; `hurst(heights, lags) -> float` =
  half the least-squares slope of log gamma on log lag. Synthetic test ground comes from a seeded `random.Random`.

## Round 2, batch 5
- `server.py` (N2.G1.2.3), on top of the names above: `free_mb()` reads free physical RAM with `ctypes`
  (`GlobalMemoryStatusEx`); `running_count()` counts `Server`s this process started whose `proc.poll()` is None;
  `start_allowed` is `free_mb >= need_mb and running < cap`.
  `boot(scratch, timeout=120.0) -> Server`: checks `start_allowed(free_mb(), running_count())` first (RuntimeError,
  no process). Starts `[SEALRUN_JAVA, "-Xmx1G", "-jar", "server.jar", "nogui"]` in `scratch["dir"]` with
  `stdin=PIPE`, stdout and stderr to `scratch["dir"] / "boot.out"` (a file, never a pipe), `creationflags =
  CREATE_NO_WINDOW`. Waits until `boot.out` holds `Done (`; on timeout or early exit it stops the process it
  started (`procs.stop`) and raises RuntimeError with the last log lines. Then opens `rcon.Client("127.0.0.1",
  scratch["rcon_port"], scratch["rcon_password"])`.
  `Server`: `proc`, `scratch`, `client`, `boot_secs` (float); `command(text) -> str`; `stop(grace=30.0) -> int`
  (asks with `stop` over RCON, then `procs.stop(proc, ask, grace)`, closes the client, returns the exit code; a
  second call returns the same code); `with boot(s) as srv:` stops on exit, error or not.
  If the real server shows `rcon.Client` wrong (the marker reply), fix `rcon.py` minimally and keep
  `lab/tests/test_rcon_fake.py` green; report the real reply text.
- "Port free" in a test means a TCP connect to `127.0.0.1:<port>` is refused (never a bind: Windows keeps
  TIME_WAIT). Windows refuses a closed loopback port only after 2.0-2.05 s (measured 3/3, SYN retries after the RST),
  so the connect timeout is 5 s and only `ConnectionRefusedError` counts as free. A guard proves no orphan by `proc.poll() is not None`, `running_count() == 0` and both ports refused.
- `lever.py` (N2.G3.7.3): exactly the batch 4 names; `lab/tests/test_guard_lever_player_legal.py` must pass.
- `flatten.py` (N2.G4.1.1): `TILES = {"air": 0, "stone": 1, "water": 2, "tree": 3, "iron": 4, "goal": 5}`
  (the byte values of `crates/world/src/grid.rs` `Tile`). `flatten.grid(blocks, x0, z0, w, h) -> list[list[int]]`,
  `h` rows of `w` ints, row `z - z0`, column `x - x0`; `blocks` is `window.box` output. Ground of a column = the
  highest y whose name is not in `flatten.PASS` (air, cave_air, void_air, grass, tall_grass, fern, large_fern,
  snow, seagrass, tall_seagrass, kelp, kelp_plant, sugar_cane, dead_bush, and the 1.16 flowers: dandelion, poppy,
  blue_orchid, allium, azure_bluet, red_tulip, orange_tulip, white_tulip, pink_tulip, oxeye_daisy, cornflower,
  lily_of_the_valley, wither_rose, sunflower, lilac, rose_bush, peony) and does not end in `_leaves`.
  First rule that holds wins: ground ends in `_log` gives tree; ground is `minecraft:water` gives water;
  `minecraft:iron_ore` at ground-6..ground gives iron; a 4-neighbour inside the box whose ground differs by 2 or
  more gives stone; else air. A column with no non-None block raises ValueError naming (x, z).
- `site/r2.html` (N2.G5.3): one top-level `function renderR2(data)` returning an HTML string, tested with node
  the way `site/tests/test_render.py` tests `renderPage`. A card per goal with `data-goal="<id>"` (title, plain,
  status, department). Bars from `data.orders` (`[{"order": [[cx, cz], ...], "diff": int}]`), one element with
  `data-order` per row, height by `diff`; no `orders` key gives the text `not run yet`, never a 0 bar. Colour only
  by status (a meaningful datum), never decoration. The page fetches `r2.json` next to it.

## Round 2, batch 6
- `server.delete_world(scratch_dir, root)` exactly as above (ValueError unless `scratch_dir` resolves inside `root`
  and holds `MARKER`; then removes `scratch_dir / "world"`; a missing world is not an error).
  `server.reset(srv, root) -> Server`: `srv.stop()`, `delete_world(srv.scratch["dir"], root)`, `boot(srv.scratch)`;
  returns the new Server (same scratch, same ports). `lab/tests/test_guard_reset_scope.py` must pass unchanged.
- `oneprocess_worlds.py` (N2.G1.4.3): `result(mc_dir: Path) -> dict` uses `fabric_probe.probe(mc_dir)`; with no Fabric
  loader or no mods it gives `{"status": "blocked", "reason": "file list not approved by the owner (house/permissions-
  6h.md row 15); fabric_loader: [...], mods: [...]", "worlds_per_minute": None, "mb_per_world": None}`; with both
  present it gives `{"status": "not run", ...}` and the same two None numbers (measuring is a later leaf). `python
  lab/oneprocess_worlds.py` writes `lab/results/worlds_one_process.json` from the real `.minecraft`. The module
  imports no network library (no urllib, http, socket) and downloads nothing.
- Real-server facts (N2.G1.2.3, measured): boot to `Done (` 19.0-21.0 s alone, 27 s with a second boot running;
  `list` answers `There are 0 of a max of 4 players online: `. A block check is `execute if block x y z <block>`
  after `forceload add x z` (`orderrun.wait_loaded`).

## Round 2, batch 7
- `bench.py` (N2.G1.2.5): `peak_mb(pid: int) -> float`: PeakWorkingSetSize of that process in MB via `ctypes`
  (`OpenProcess` with PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, `K32GetProcessMemoryInfo`), read while it
  runs. `measure(root: Path) -> dict`: make_scratch, `boot` (boot_secs), `reset` timed (reset_secs), peak_mb of each
  java read just before its stop, always stopped and `serverdir.remove`d. Keys: `boot_secs`, `reset_secs`,
  `peak_mb` (max of the two javas), `xmx` ("1G"), `free_mb_before`, `when` (ISO time), `runs` (1).
  `python lab/bench.py` writes `lab/results/lab_timing.json`. Numbers are measured, never typed in.
  Batch 7 fix (Wilson r2-batch7): one more key `other_java` = java.exe processes running when `measure` starts
  (`tasklist`), so a boot timed beside another server says so. The committed file is measured with `other_java` 0.
  The test checks the committed file against its own fresh measurement (boot, reset, peak within 50 %), and
  `reset_secs` against the wall time of `server.reset` itself (within 0.25 s).
- `test_anvil_live.py` (N2.G2.6): boot, `wait_loaded`, place five known blocks with `setblock` (different sections
  and both chunks of a border pair inside loaded chunks), `save-all flush`, `stop`, then `anvil.block_at(scratch_dir /
  "world" / "region", x, y, z)` equals each placed name. Only the test file is written.

## Round 2, batch 8
- Far chunk = `orders.SQUARES[0]` corner (64, 64) (blocks 1024..1039), file `r.2.2.mca`. World spawn comes from the
  scratch `world/level.dat` (`nbt.read`, `Data.SpawnX`, `Data.SpawnZ`); every result names its distance in chunks.
- Statuses are the raw `anvil.chunk_status` strings after `save-all flush` (None = not on disk). Dr House's leap
  n2-L1 (unverified, from memory) predicts a forceloaded chunk's neighbours at Chebyshev distance 1 and 2 are
  `"full"` (forceload ticket level 31, FULL at level <= 33) and distance 3 is not. The real server decides; a test
  written to Foreman's hypothesis that fails on real data is a finding, never bent to pass.
- `test_guard_setblock_edges.py` (N2.G2.C2, guard `test_guard_setblock_edges`): real server; blocks at x 15|16 and
  z -1|0 (both sides of chunk borders), at (-17, 64, -33) (`r.-1.-1.mca`), at y 0 and y 255; `save-all flush`, stop,
  every one read back exactly with `anvil.block_at`.
- Measured (Finding n2-F1, 3 identical runs): one `forceload add` makes its chunk and every chunk within Chebyshev
  distance 2 `"full"` on disk; distance 3..12 is not on disk (not on disk is not "not generated"). So a list of
  neighbouring chunks is one move per 5x5 tile: only the first ticket of a tile changes what gets built.
  Finding n2-F2 (Wilson r2-batch8 V4): while the ticket holds, flush writes only the full chunks; after
  `forceload remove`, 60 s and stop the partials are on disk: d 3 `features`, d 4 `liquid_carvers`, d 5..12
  `structure_starts`. Ores (features) are placed at distance 3 of a ticket while only distance <= 2 is full.
- `orderrun.run_order(scratch: dict, order: list[tuple[int, int]]) -> dict[(x, y, z), str | None]` (N2.G3.2.4):
  `server.boot(scratch)`, then for each `(cx, cz)` in order `wait_loaded` (False raises RuntimeError naming the chunk)
  and `save-all flush`; stop; return `window.box(region, lo, hi)` over the bounding box of the listed chunks, y 0..255.
  Always stops its server; the caller makes and removes the scratch. Test `run_order_returns_window_for_two_chunks`:
  real server, order [(64, 64), (65, 64)], 131072 positions, none None.

## Round 2, batch 10
- Real servers: every boot goes through `python C:/Users/seal/Documents/GitHub/sealrun-wt/slot.py <cmd>`, at most
  2 at once across all agents (owner cap). A run that needs both slots nests it: `slot.py python slot.py <cmd>`.
- `bench_vanilla.py` (N2.G1.4.1): `measure(n: int, secs: float, root: Path) -> dict` runs n servers at once
  (n in 1..2: the cap; 3 is not run and the result says so), each in its own scratch, each looping
  `server.reset` until `secs` pass; counts worlds (resets finished) and samples `bench.peak_mb` of every java.
  Keys: `n`, `secs`, `worlds`, `worlds_per_minute`, `peak_mb_total`, `mb_per_world` (= peak_mb_total / n),
  `other_java` (as bench), `when`. `python lab/bench_vanilla.py` holds both slots and writes
  `lab/results/worlds_vanilla.json` = {"runs": [n=1, n=2], "not_run": {"n": 3, "why": "owner cap of 2 real servers"}}.
  Numbers are measured, never typed in. Test `n_vanilla_servers_worlds_per_minute_and_ram_per_world`: a short
  measure(1, 60) boots, gets worlds >= 1, mb 200..2000, leaves no java and no scratch; the committed json has both
  runs with `other_java` 0.
- `test_forceload_tile.py` (N2.G3.2.A1): one forceload on (64, 64), stop with the ticket held; all 8 rays (east,
  west, north, south and the 4 diagonals) read full at d 0..2 and None at d 3; writes
  `lab/results/forceload_tile.json` before asserting. Claims "not saved at 3", never "not generated".
- `test_guard_settle_invariance.py` (N2.G3.C3, guard): two fresh worlds, same single forceload on (64, 64), one
  saved and stopped at once after load, one after 60 s; `window.fingerprint` of chunk (64, 64)'s blocks (via
  `window.box`) equal. Unequal is a finding (waiting changes blocks), reported, never bent.

## Round 2, batch 11
- `test_order_control.py` (N2.G3.3.1): two fresh scratch worlds, each `orderrun.run_order(scratch, [(64, 64),
  (65, 64)])`; `blockdiff.diff` of the two windows; writes `lab/results/order_control.json` = {"order", "runs": 2,
  "positions", "changed", "added", "removed", "fingerprints": [two], "when"} before asserting; then changed, added and
  removed are all 0. Measured once already by Wilson's lane V1 (r2-batch9): 0 of 131072 differ. Nonzero = the order
  experiment is too noisy to use: reported, never bent.
- `test_order_pair.py` (N2.G3.3.2): AB = run_order [(64, 64), (65, 64)], BA = run_order [(65, 64), (64, 64)], each on
  a fresh world. By the measured tile this compares two ticket centres, not two build orders inside one tile.
  `blockdiff.diff(AB, BA)`; writes `lab/results/order_pair.json` = {"orders": [AB, BA], "positions", "changed",
  "added", "removed", "examples" (<= 20 of (pos, AB, BA)), "by_chunk" {chunk: changed}, "ores" {order: {chunk:
  `ores.tally`}}, "fingerprints", "control_fingerprint" (from order_control.json), "when"}. Asserts only what the
  measurement needs: AB's fingerprint equals the control's (the lab is deterministic) and the json is written; the
  count of differing blocks is the result, any value valid (0 kills this pair as a lever, with a route).

## Round 2, batch 12
- `test_order_edit.py` (N2.G3.5.2): A = (64, 64), B = (68, 64). EDIT = break the 4x4x4 cube x 1068..1071,
  y 30..33, z 1024..1027 (chunk (66, 64), the east edge of A's measured full tile). Two fresh worlds, same
  steps except the edit: boot; `orderrun.wait_loaded(srv, *A)`; edited world only: every line of
  `edits.commands(EDIT ops, A's 5x5 tile)` through `srv.command`; `wait_loaded(srv, *B)`; `save-all flush`; stop.
  Window `window.box` over chunks 64..68 of row z 64: lo (1024, 0, 1024), hi (1103, 255, 1039), 327680 cells.
  `blockdiff.diff(plain, edited)`, changed cells split into inside EDIT and outside. Writes
  `lab/results/order_edit.json` = {"A", "B", "edit": {"lo", "hi", "op": "break"}, "positions", "inside_changed",
  "outside_changed", "added", "removed", "by_chunk_outside" {chunk: n}, "examples_outside" (<= 20 of (pos, plain,
  edited)), "edit_before" {block: count of plain's blocks at the 64 edit cells}, "not_full" [plain, edited],
  "fingerprints", "when"} before asserting. Asserts only: both windows have 0 None cells, every edit cell reads
  `minecraft:air` in the edited world, the json is written. outside_changed is the result, any value valid.
  (The lead "0 outside expected" was refuted by the batch 12 lane; see the fix below.)
- Batch 12 fix (lane r2-batch12): the rush flow above is not deterministic (plain vs plain: 17 cells differ, chunks
  67 and 68). The test uses the settled flow instead. `settle(srv, tile)`: for each chunk of `tile` poll
  `execute if block <cx*16> 0 <cz*16> minecraft:bedrock` every 0.5 s until "Test passed" (120 s budget for the
  whole tile, else RuntimeError), then `save-all flush`, then sleep 10 s; returns the poll seconds. Steps per world:
  boot; `wait_loaded(A)`; settle(A's tile); edit loop (edited world only); settle(A's tile); `wait_loaded(B)`;
  settle(B's tile = chunks 66..70 x 62..66); `save-all flush`; stop.
- Batch 12 fix, second form (fix run 1: the settled plain world is not deterministic either: plain fingerprints
  9fd4b7ed x3, 5bf50afc x1, the odd one differing in chunk (66, 64), inside A's tile; edited 3aaf87b1 x3). Four fresh
  worlds in the settled flow: plain p1, p2, edited e1, e2. Per cell outside EDIT: "noise" if p1 != p2 or e1 != e2;
  "edit_attributed" if p1 == p2 and e1 == e2 and p1 != e1. Json: the earlier keys computed from p1 vs e1, minus
  "control_fingerprint", plus "fingerprints" {p1, p2, e1, e2}, "noise" {count, by_chunk}, "edit_attributed" {count,
  by_chunk, examples (<= 20 of (pos, p1, e1))}, "settle_s" {world: [three poll seconds]}. Asserts: 0 None in all four,
  every edit cell air in e1 and e2, json written. No determinism assertion: noise is a result. Seen so far: 6
  edit-attributed cells in (68, 64), andesite -> diorite.

## Round 2, batch 13
- `choice.py` (N2.G1.4.4), pure: `per_gb(run) -> float` = `worlds_per_minute / (peak_mb_total / 1024)`.
  `pick(vanilla_runs: list[dict], other: dict | None) -> dict` = {"route": "vanilla" | "in_process",
  "worlds_per_minute_per_gb", "vanilla_best_n", "why"}: the best vanilla run by `per_gb`; `other` wins only when it
  is present, has no "blocked" key and its `per_gb` is strictly larger; otherwise "vanilla", and "why" says
  "missing" or quotes the blocked reason. `python lab/choice.py` reads `lab/results/worlds_vanilla.json` and writes
  `lab/results/world_route.json` = pick(runs, {"route": "in_process", "blocked": "Fabric/mod download needs the
  owner's approval of the file list (permissions ledger row 15)"}) plus "when". Test
  `route_choice_picks_more_worlds_per_gb_and_falls_back`: other better -> in_process; other worse or equal ->
  vanilla; other None -> vanilla "missing"; other blocked but better -> vanilla with the reason; on the committed
  numbers vanilla_best_n is 1 (3.07 / (812.2 / 1024) = 3.87 vs 4.42 / (1609.2 / 1024) = 2.81); the committed
  world_route.json equals pick recomputed from the committed worlds_vanilla.json (ignoring "when").

## Round 2, batch 14
- `pool.py` (N2.G1.4.5), pure: `run(jobs: list, fn, workers: int) -> list` runs `fn(job)` for every job with at most
  `workers` at once (`concurrent.futures.ThreadPoolExecutor`) and returns the results in job order. `workers` must be
  1 or 2 (the owner cap of 2 real servers overrules the chart's 3); otherwise `ValueError` before any job starts. An
  exception in a job propagates. Test `pool_returns_results_in_job_order_and_refuses_four_servers`, pure, fake `fn`
  that sleeps a job-dependent time so jobs finish out of order: results come back in job order; the highest number of
  jobs running at once is exactly 2 for workers 2 with 4 jobs and 1 for workers 1; workers 3 and 4 raise ValueError
  and `fn` is never called; a job that raises makes `run` raise.
- `test_order_collapse.py` (N2.G3.C6, guard of N2.G3.4): O1 = `orders.square_orders(64, 64)[0]`, O2 = `[O1[0]] +
  O1[:0:-1]` (same first chunk, the other three reversed). Three fresh worlds: `orderrun.run_order(O1)`,
  `run_order(O2)`, `run_order(O1)` again (control). `blockdiff.diff(O1, control)` and `diff(O1, O2)`. Writes
  `lab/results/order_collapse.json` = {"orders": [O1, O2], "positions", "control_changed", "pair_changed",
  "by_chunk_pair" {chunk: n}, "examples" (<= 20 of (pos, O1, O2)), "fingerprints" [O1, O2, control], "not_full"
  [three None counts], "when"} before asserting. Asserts: 0 None in all three windows, control_changed 0, pair_changed
  0 (the 4-class collapse). Nonzero is a finding (the collapse is false), reported, never bent.

Every agent that stops a process kills only the PID it started (`procs.stop`), never `taskkill /IM`.
