---
phase: 01-foundation
reviewed: 2026-05-28T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - resume_tailor/__init__.py
  - resume_tailor/config.py
  - resume_tailor/cli.py
  - resume_tailor/resume_reader.py
  - resume_tailor/resume_writer.py
  - pyproject.toml
  - README.md
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-28T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

This is a Phase 1 foundation scaffold. The implemented files are thin but real: `config.py`, `resume_reader.py`, and `resume_writer.py` each contain concrete logic; `cli.py` is a documented stub. Two blockers exist — a path resolution defect that makes the installed tool silently fail to find user files, and a Python version mismatch between `pyproject.toml` and `README.md`. Three warnings cover missing error handling in `resume_writer.py`, an unhandled `UnicodeDecodeError` in `resume_reader.py`, and a stub `cli.py` that parses no arguments but is wired as the live entry point. No security issues were found.

## Critical Issues

### CR-01: `config.py` path resolution breaks under `uv tool install`

**File:** `resume_tailor/config.py:3-9`
**Issue:** `_ROOT` is computed as `Path(__file__).parent.parent`, which resolves correctly during development (project root). When the package is installed via `uv tool install .`, `__file__` resolves to something like `<venv>/lib/python3.x/site-packages/resume_tailor/__init__.py`, making `_ROOT` equal to `<venv>/lib/python3.x/site-packages`. As a result, `BASE_RESUME_PATH` becomes `<venv>/lib/python3.x/site-packages/resumes/english.tex` — a path that never exists — and `OUTPUT_DIR` writes into the venv's site-packages tree. The inline comment `# works after uv tool install` is factually wrong; this is the exact scenario that breaks.

User-data files like resumes should be resolved relative to a well-known user directory (`~/.config/resume-tailor/` or `~/resumes/`), or the path must be supplied via CLI flag with no default that assumes file layout relative to the package. Using `__file__` for user data is only safe in dev mode.

**Fix:**
```python
from pathlib import Path

# Resolve user data relative to home, not the installed package location.
_USER_DATA_DIR: Path = Path.home() / ".config" / "resume-tailor"

OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
BASE_RESUME_PATH: Path = _USER_DATA_DIR / "resumes" / "english.tex"
OUTPUT_DIR: Path = _USER_DATA_DIR / "output"
TIMEOUT: tuple[int, int] = (10, 300)
```
Alternatively (and more in keeping with the CLI design), remove static defaults entirely and require the `--resume` and `--output-dir` flags to be provided or defaulted at the `argparse` level using `os.getcwd()` anchoring, keeping the path resolution deterministic and user-visible.

---

### CR-02: Python version requirement mismatch between `pyproject.toml` and `README.md`

**File:** `pyproject.toml:6` / `README.md:15`
**Issue:** `pyproject.toml` declares `requires-python = ">=3.13"`, but `README.md` documents `Python 3.11+`. The packaging metadata is authoritative at install time — `pip`/`uv` will refuse to install on Python 3.11 or 3.12 even though the README invites users to try. The discrepancy will cause silent install failures for any user on 3.11 or 3.12 and makes the documentation misleading. CLAUDE.md itself states 3.11 is the safe minimum.

**Fix:**
Align both to the same floor. CLAUDE.md's guidance is `>=3.11`; update `pyproject.toml` to match:
```toml
requires-python = ">=3.11"
```
If 3.13-specific features are actually required, update the README instead.

---

## Warnings

### WR-01: `resume_writer.py` — no error handling around file I/O

**File:** `resume_tailor/resume_writer.py:7-10`
**Issue:** `output_dir.mkdir()` and `output_path.write_text()` can each raise `PermissionError` or `OSError` (e.g., read-only filesystem, disk full, bad path). Neither is caught. An unhandled exception here produces a raw Python traceback to the user rather than a clean error message, which is inconsistent with the deliberately user-friendly error handling in `resume_reader.py`. For a CLI tool, all I/O failure paths should emit a human-readable message to `stderr` and exit with code 1.

**Fix:**
```python
import sys

def write_resume(content: str, output_dir: Path) -> Path:
    """Write tailored LaTeX content to a timestamped file under output_dir."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"tailored_resume_{timestamp}.tex"
        output_path.write_text(content, encoding="utf-8")
        return output_path
    except OSError as exc:
        print(f"Error: Could not write output file: {exc}", file=sys.stderr)
        sys.exit(1)
```

---

### WR-02: `resume_reader.py` — `UnicodeDecodeError` not caught

**File:** `resume_tailor/resume_reader.py:7-11`
**Issue:** `path.read_text(encoding="utf-8")` raises `UnicodeDecodeError` if the file exists but is not valid UTF-8 (e.g., a Latin-1 encoded `.tex` file, or a binary file accidentally placed at the resume path). Only `FileNotFoundError` is caught. The unhandled `UnicodeDecodeError` produces a raw traceback that leaks the internal call stack to the user.

**Fix:**
```python
def read_resume(path: Path) -> str:
    """Read the base resume LaTeX file and return its content as a string."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(
            f"Error: Resume file at {path} is not valid UTF-8. "
            "Save the file as UTF-8 and retry.",
            file=sys.stderr,
        )
        sys.exit(1)
```

---

### WR-03: `cli.py` is a live entry point with a non-functional argument parser

**File:** `resume_tailor/cli.py:6-16`
**Issue:** `cli.py` is registered as the `resume-tailor` entry point in `pyproject.toml`. In its current state, it calls `parser.parse_args()` but accepts no arguments and does nothing. Any user who installs the package and runs `resume-tailor --model llama3` will receive: `error: unrecognized arguments: --model llama3` — an unhelpful argparse error that suggests the tool rejects its own documented flags. The comments `# Full implementation: Phase 3` are planning context that is invisible to a CLI consumer. If this phase ships as an installable package, the entry point should either be a no-op stub that prints "Coming soon" or not be registered until Phase 3.

**Fix (minimal guard):**
```python
def main() -> None:
    print(
        "resume-tailor: full CLI not yet implemented. "
        "Run again after Phase 3 is complete.",
        file=sys.stderr,
    )
    sys.exit(1)
```
Or defer the `[project.scripts]` entry in `pyproject.toml` until Phase 3 completes.

---

## Info

### IN-01: `TIMEOUT` constant defined but not yet referenced

**File:** `resume_tailor/config.py:10`
**Issue:** `TIMEOUT: tuple[int, int] = (10, 300)` is defined but is not imported or used anywhere in the codebase. This is expected for a Phase 1 scaffold (the Ollama HTTP call is Phase 3 work), but the constant creates a false impression that timeout handling is already wired up. No action needed until Phase 3, but it should be consumed in the `requests.post()` call when that is implemented.

**Fix:** No change needed now. In Phase 3, ensure the HTTP call passes `timeout=TIMEOUT` to `requests.post()`.

---

### IN-02: `__init__.py` contains only a comment — no `__all__` or version export

**File:** `resume_tailor/__init__.py:1`
**Issue:** The package `__init__.py` is a single comment line. No `__version__`, no `__all__`. This is acceptable for a Phase 1 stub, but for a portfolio piece it is conventional to at least export `__version__` consistent with `pyproject.toml`. Not a bug; noted for completeness.

**Fix (optional):**
```python
"""resume_tailor — LaTeX resume tailoring CLI."""

__version__ = "0.1.0"
```

---

_Reviewed: 2026-05-28T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
