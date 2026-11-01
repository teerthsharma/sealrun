import ctypes
import json
import os
import subprocess
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

import server
import serverdir

SRC = Path(os.environ.get("SEALRUN_SERVER", "C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1"))
RESULT = Path(__file__).resolve().parent / "results" / "lab_timing.json"
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
MB = 1024 * 1024


class _Counters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def peak_mb(pid: int) -> float:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        c = _Counters(cb=ctypes.sizeof(_Counters))
        if not k32.K32GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return c.PeakWorkingSetSize / MB
    finally:
        k32.CloseHandle(h)


def measure(root: Path) -> dict:
    free_before = server.free_mb()
    tasks = subprocess.run(["tasklist", "/FI", "IMAGENAME eq java.exe", "/NH", "/FO", "CSV"], capture_output=True, text=True).stdout
    other_java = sum(1 for line in tasks.splitlines() if line.startswith('"java.exe"'))
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    scratch = serverdir.make_scratch(SRC, root)
    srv = None
    try:
        srv = server.boot(scratch)
        boot_secs = srv.boot_secs
        peak = peak_mb(srv.proc.pid)
        t0 = time.monotonic()
        srv = server.reset(srv, root)
        reset_secs = time.monotonic() - t0
        peak = max(peak, peak_mb(srv.proc.pid))
    finally:
        if srv is not None:
            srv.stop()
        serverdir.remove(scratch["dir"])
    return {
        "boot_secs": round(boot_secs, 2),
        "reset_secs": round(reset_secs, 2),
        "peak_mb": round(peak, 1),
        "xmx": "1G",
        "free_mb_before": free_before,
        "other_java": other_java,
        "when": when,
        "runs": 1,
    }


def main() -> None:
    root = Path(os.environ.get("SEALRUN_LAB", Path.home() / "sealrun-lab"))
    root.mkdir(parents=True, exist_ok=True)
    result = measure(root)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(RESULT.read_text(), end="")


if __name__ == "__main__":
    main()
