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

Every agent that stops a process kills only the PID it started (`procs.stop`), never `taskkill /IM`.
