import sys
from pathlib import Path


def read_resume(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
