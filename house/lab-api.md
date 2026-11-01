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
