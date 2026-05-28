from pathlib import Path
import sys


def read_resume(path: Path) -> str:
    """Read the base resume LaTeX file and return its content as a string."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
