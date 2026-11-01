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
