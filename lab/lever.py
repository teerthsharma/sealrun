ADMIN = {"forceload", "setblock", "fill", "tp", "teleport", "gamerule", "time", "weather",
         "execute", "save-all", "stop", "kill", "summon", "give"}


def kinds(steps: list[str]) -> list[str]:
    return ["admin" if _word(step) in ADMIN else "player" for step in steps]


def label(steps: list[str]) -> str:
    return "lab-only" if "admin" in kinds(steps) else "player-legal"


def _word(step: str) -> str:
    words = step.split()
    return words[0].removeprefix("/") if words else ""
