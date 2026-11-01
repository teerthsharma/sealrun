import subprocess


def stop(proc: subprocess.Popen, ask=None, grace: float = 10.0) -> int:
    if ask is not None:
        ask()
    try:
        return proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
        return proc.wait()
