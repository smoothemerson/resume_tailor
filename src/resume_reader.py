from pathlib import Path


def read_resume(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Base resume not found at {path}") from exc
