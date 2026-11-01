import json
import subprocess
from pathlib import Path

REAL = Path("C:/Users/seal/Desktop/sanitised mineraft/.minecraft")
OUT = Path(__file__).resolve().parent / "results" / "fabric_probe.json"


def _names(folder: Path, keep) -> list:
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if keep(p))


def _java_version(exe: Path):
    try:
        r = subprocess.run([str(exe), "-version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = (r.stderr or r.stdout).strip().splitlines()
    return lines[0] if lines else None


def probe(mc_dir: Path) -> dict:
    jar = Path("versions/1.16.1/1.16.1.jar")
    runtime = mc_dir / "runtime"
    return {
        "client_1_16_1": {"present": (mc_dir / jar).is_file(), "path": jar.as_posix()},
        "fabric_loader": _names(mc_dir / "versions", lambda p: p.is_dir() and "fabric-loader" in p.name),
        "mods": _names(mc_dir / "mods", lambda p: p.is_file()),
        "java": [
            {"path": p.relative_to(mc_dir).as_posix(), "version": _java_version(p)}
            for p in sorted(runtime.rglob("java.exe")) if runtime.is_dir()
        ],
    }


if __name__ == "__main__":
    result = probe(REAL)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
