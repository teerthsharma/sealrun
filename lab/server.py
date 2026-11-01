import ctypes
import os
import shutil
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

import procs
import rcon
import serverdir

JAVA = os.environ.get(
    "SEALRUN_JAVA",
    "C:/Users/seal/Desktop/sanitised mineraft/.minecraft/runtime/jre-legacy/windows/jre-legacy/bin/java.exe",
)
SERVER = os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1")
CREATE_NO_WINDOW = 0x08000000
DONE = "Done ("

_servers: list = []


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def free_mb() -> int:
    st = _MemoryStatus()
    st.dwLength = ctypes.sizeof(st)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        raise ctypes.WinError()
    return st.ullAvailPhys // (1024 * 1024)


def start_allowed(free_mb: int, running: int, need_mb: int = 1500, cap: int = 3) -> bool:
    return free_mb >= need_mb and running < cap


def running_count() -> int:
    return sum(1 for s in _servers if s.proc.poll() is None)


def _text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except FileNotFoundError:
        return ""


def _fail(proc: subprocess.Popen, log: Path, why: str) -> RuntimeError:
    procs.stop(proc, grace=0.0)
    tail = "\n".join(_text(log).splitlines()[-20:])
    return RuntimeError(f"{why}; last log lines:\n{tail}")


class Server:
    def __init__(self, proc, scratch, client, boot_secs: float):
        self.proc = proc
        self.scratch = scratch
        self.client = client
        self.boot_secs = boot_secs
        self._code = None

    def command(self, text: str) -> str:
        return self.client.command(text)

    def stop(self, grace: float = 30.0) -> int:
        if self._code is None:
            self._code = procs.stop(self.proc, self._ask_stop, grace)
            self.client.close()
        return self._code

    def _ask_stop(self) -> None:
        try:
            self.client.command("stop")
        except (OSError, ValueError):
            pass

    def __enter__(self) -> "Server":
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def boot(scratch: dict, timeout: float = 120.0) -> Server:
    if not start_allowed(free_mb(), running_count()):
        raise RuntimeError("start refused: free RAM below 1500 MB or 3 servers running")
    d = Path(scratch["dir"])
    log = d / "boot.out"
    t0 = time.monotonic()
    with open(log, "wb") as out:
        proc = subprocess.Popen(
            [JAVA, "-Xmx1G", "-jar", "server.jar", "nogui"],
            cwd=d,
            stdin=subprocess.PIPE,
            stdout=out,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
    try:
        while DONE not in _text(log):
            if proc.poll() is not None:
                raise _fail(proc, log, f"server exited with {proc.returncode} before Done")
            if time.monotonic() - t0 > timeout:
                raise _fail(proc, log, f"no Done within {timeout} s")
            time.sleep(0.5)
    except BaseException:
        procs.stop(proc, grace=0.0)
        raise
    boot_secs = time.monotonic() - t0
    try:
        client = rcon.Client("127.0.0.1", scratch["rcon_port"], scratch["rcon_password"])
    except BaseException:
        procs.stop(proc, grace=0.0)
        raise
    srv = Server(proc, scratch, client, boot_secs)
    _servers.append(srv)
    return srv


def delete_world(scratch_dir: Path, root: Path) -> None:
    d = Path(scratch_dir).resolve()
    r = Path(root).resolve()
    if not d.is_relative_to(r) or d == r or not (d / serverdir.MARKER).is_file():
        raise ValueError(f"refusing to delete a world outside a marked scratch folder under {r}: {d}")
    if (d / "world").exists():
        shutil.rmtree(d / "world")


def reset(srv: Server, root: Path) -> Server:
    srv.stop()
    delete_world(srv.scratch["dir"], root)
    return boot(srv.scratch)
