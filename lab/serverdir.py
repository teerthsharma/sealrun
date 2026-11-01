import secrets
import shutil
import socket
import tempfile
import time
from pathlib import Path

MARKER = ".sealrun-scratch"


def remove(scratch_dir: Path, timeout: float = 10.0) -> None:
    marker = Path(scratch_dir, MARKER)
    if not marker.is_file():
        raise ValueError(f"not a scratch folder (no {MARKER}): {scratch_dir}")
    deadline = time.monotonic() + timeout
    while True:
        try:
            for child in scratch_dir.iterdir():
                if child.name == MARKER:
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            marker.unlink()
            scratch_dir.rmdir()
            return
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.5)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_scratch(src: Path, root: Path) -> dict:
    d = Path(tempfile.mkdtemp(dir=root))
    for name in ("server.jar", "eula.txt"):
        shutil.copy2(src / name, d / name)
    (d / MARKER).write_text("scratch\n")
    port, rcon_port, password = _free_port(), _free_port(), secrets.token_hex(16)
    values = {
        "enable-rcon": "true",
        "rcon.port": str(rcon_port),
        "rcon.password": password,
        "server-port": str(port),
    }
    kept = [
        line
        for line in (src / "server.properties").read_text().splitlines()
        if line.split("=", 1)[0] not in values
    ]
    kept += [f"{k}={v}" for k, v in values.items()]
    (d / "server.properties").write_text("\n".join(kept) + "\n")
    return {"dir": d, "port": port, "rcon_port": rcon_port, "rcon_password": password}
