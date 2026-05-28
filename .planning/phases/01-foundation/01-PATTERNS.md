# Phase 1: Foundation - Pattern Map

**Mapped:** 2026-05-28
**Files analyzed:** 6 (4 new Python modules + 1 updated config + 1 stub)
**Analogs found:** 0 / 6 — greenfield project; no existing Python source in codebase

## Analog Search Result

The codebase contains no existing Python source files. The only files present are:
- `pyproject.toml` (7 lines, no build-system, no scripts — to be updated)
- `resumes/english.tex` and `resumes/portuguese.tex` (LaTeX source, not Python)

All patterns are sourced from RESEARCH.md's verified stdlib code examples, which were tested in a live Python 3.11.2 environment. These are treated as canonical analogs.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | — | RESEARCH.md Pattern 4 (verified) | no-codebase-analog |
| `resume_tailor/__init__.py` | config | — | RESEARCH.md `__init__.py` snippet | no-codebase-analog |
| `resume_tailor/config.py` | config | — | RESEARCH.md Pattern 5 (verified) | no-codebase-analog |
| `resume_tailor/resume_reader.py` | utility | file-I/O | RESEARCH.md Pattern 3 (verified) | no-codebase-analog |
| `resume_tailor/resume_writer.py` | utility | file-I/O | RESEARCH.md Pattern 2 (verified) | no-codebase-analog |
| `resume_tailor/cli.py` | utility | request-response | RESEARCH.md cli.py stub (verified) | no-codebase-analog |

## Pattern Assignments

### `pyproject.toml` (config)

**Analog:** RESEARCH.md — Pattern 4: pyproject.toml for uv tool install (PKG-01)
**Source line in RESEARCH.md:** lines 215-234

**Critical note:** The existing `pyproject.toml` (7 lines) has no `[build-system]`, no `dependencies`, and no `[project.scripts]`. All three sections must be added. Without `[build-system]`, `uv tool install .` will not register the `resume-tailor` shell command.

**Complete target state:**
```toml
[project]
name = "resume-tailor"
version = "0.1.0"
description = "Tailor a LaTeX resume to a job description using a local Ollama LLM"
readme = "README.md"
requires-python = ">=3.13"
dependencies = ["requests>=2.32.0"]

[project.scripts]
resume-tailor = "resume_tailor.cli:main"

[project.optional-dependencies]
dev = ["ruff", "mypy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Changes from current file:**
- `name`: `"en-cv-ai-engineer"` → `"resume-tailor"` (D-02)
- `description`: placeholder → real description
- `dependencies`: `[]` → `["requests>=2.32.0"]`
- ADD `[project.scripts]` table with `resume-tailor = "resume_tailor.cli:main"`
- ADD `[project.optional-dependencies]` with `dev = ["ruff", "mypy"]`
- ADD `[build-system]` table (CRITICAL — must not be omitted)

---

### `resume_tailor/__init__.py` (config)

**Analog:** RESEARCH.md — `__init__.py` snippet

**Complete target state:**
```python
# Empty — marks resume_tailor/ as a Python package
```

No imports, no logic. Phase 2 and Phase 3 import individual modules directly (`from resume_tailor.config import ...`), not from `__init__.py`.

---

### `resume_tailor/config.py` (config)

**Analog:** RESEARCH.md — Pattern 5 + Code Examples: config.py Complete Reference Implementation
**Source lines in RESEARCH.md:** lines 238-251 (Pattern 5), lines 309-321 (Code Examples)

**Imports pattern:**
```python
from pathlib import Path
```

**Path anchoring pattern (CONF-02):**
```python
_HERE = Path(__file__).parent          # resume_tailor/
_ROOT = _HERE.parent                   # project root (works after uv tool install)
```

**Constants pattern (CONF-01):**
```python
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
BASE_RESUME_PATH: Path = _ROOT / "resumes" / "english.tex"
OUTPUT_DIR: Path = _ROOT / "resumes" / "output"
TIMEOUT: tuple[int, int] = (10, 300)   # (connect_timeout, read_timeout) for requests
```

**Critical rules:**
- NO class wrapping — Phase 2 and Phase 3 use `from resume_tailor.config import BASE_RESUME_PATH` directly
- NO env var loading — plain Python module constants only
- `OLLAMA_MODEL` value must be exactly `"mistral-small3.2:24b"` (D-03)
- `BASE_RESUME_PATH` must use `Path(__file__)` anchoring, NOT `Path("resumes/english.tex")` (D-01, CONF-02)
- All 5 constants required by CONF-01: `BASE_RESUME_PATH`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OUTPUT_DIR`, `TIMEOUT`

---

### `resume_tailor/resume_reader.py` (utility, file-I/O)

**Analog:** RESEARCH.md — Pattern 3 + Code Examples: resume_reader.py Complete Reference Implementation
**Source lines in RESEARCH.md:** lines 197-210 (Pattern 3), lines 323-336 (Code Examples)

**Imports pattern:**
```python
from pathlib import Path
import sys
```

**Core file-I/O pattern (CORE-01):**
```python
def read_resume(path: Path) -> str:
    """Read the base resume LaTeX file and return its content as a string."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
```

**Error handling pattern (ERR-01):**
- `try/except FileNotFoundError` — catch at the read site, not at a higher level
- `print(..., file=sys.stderr)` — human-readable message, no raw traceback
- `sys.exit(1)` — non-zero exit code signals failure to shell callers
- Do NOT re-raise; do NOT let the exception propagate to `main()`
- `encoding="utf-8"` is mandatory — LaTeX files with accented characters (user's name) will fail without it

---

### `resume_tailor/resume_writer.py` (utility, file-I/O)

**Analog:** RESEARCH.md — Pattern 2 + Code Examples: resume_writer.py Complete Reference Implementation
**Source lines in RESEARCH.md:** lines 178-192 (Pattern 2), lines 337-351 (Code Examples)

**Imports pattern:**
```python
from pathlib import Path
from datetime import datetime
```

**Core file-I/O pattern (CORE-05):**
```python
def write_resume(content: str, output_dir: Path) -> Path:
    """Write tailored LaTeX content to a timestamped file under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
```

**Key details:**
- `mkdir(parents=True, exist_ok=True)` — creates `resumes/output/` if missing; idempotent
- Filename format: `tailored_resume_YYYYMMDD_HHMMSS.tex` — human-readable, sortable
- Returns the `Path` of the written file so callers can print the output location
- `encoding="utf-8"` mandatory on both read and write

---

### `resume_tailor/cli.py` — Phase 1 Stub (utility, request-response)

**Analog:** RESEARCH.md — Code Examples: cli.py stub
**Source lines in RESEARCH.md:** lines 353-368

**Purpose:** Phase 1 must create a minimal stub so that `uv tool install .` can resolve `resume_tailor.cli:main`. Without this file, the install will fail with `ModuleNotFoundError`. Phase 3 replaces this stub with the full implementation.

**Phase 1 stub pattern:**
```python
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor a LaTeX resume to a job description using a local Ollama LLM.",
    )
    # Full implementation in Phase 3
    parser.parse_args()

if __name__ == "__main__":
    main()
```

**Critical:** This stub must define `main()` with exactly this name — it must match `"resume_tailor.cli:main"` in `[project.scripts]`.

---

## Shared Patterns

### Path Anchoring (applies to `config.py`)
**Source:** RESEARCH.md Pattern 1 (lines 163-176), confirmed via live Python 3.11.2 test
**Apply to:** `resume_tailor/config.py`
```python
_HERE = Path(__file__).parent   # resume_tailor/ package dir
_ROOT = _HERE.parent            # project root — stable after uv tool install
```
Never use `Path("resumes/...")` — cwd-relative paths break when the tool is installed system-wide.

### File Text I/O (applies to reader and writer)
**Source:** RESEARCH.md "Don't Hand-Roll" section (lines 262-269)
**Apply to:** `resume_reader.py`, `resume_writer.py`
- Read: `Path.read_text(encoding="utf-8")` — not `open(f, 'r').read()`
- Write: `Path.write_text(content, encoding="utf-8")` — not `open(f, 'w').write(...)`
- Directory creation: `Path.mkdir(parents=True, exist_ok=True)` — not `os.makedirs`

### Error Output (applies to reader)
**Source:** RESEARCH.md Pattern 3 (lines 197-210)
**Apply to:** `resume_reader.py`
```python
print(f"Error: ...", file=sys.stderr)
sys.exit(1)
```
Success output goes to stdout; error messages go to stderr. No `logging` module — direct `print(..., file=sys.stderr)`.

### Type Annotations (applies to all public functions)
**Source:** CLAUDE.md "Type checking" section + RESEARCH.md Stack table
**Apply to:** All `.py` files with public functions
- Annotate all public function signatures: `def read_resume(path: Path) -> str:`
- Annotate all module-level constants: `OLLAMA_BASE_URL: str = ...`
- Use stdlib types only (`Path`, `str`, `tuple[int, int]`) — no `pydantic`, no `typing.Optional` for simple types

---

## No Analog Found

All files in this phase have no codebase analog — the project has no existing Python source. The table below documents this for planner reference.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pyproject.toml` (update) | config | — | Only existing file is the 7-line stub being replaced; no Python package structure exists yet |
| `resume_tailor/__init__.py` | config | — | No existing Python package directory |
| `resume_tailor/config.py` | config | — | No existing Python source files |
| `resume_tailor/resume_reader.py` | utility | file-I/O | No existing Python source files |
| `resume_tailor/resume_writer.py` | utility | file-I/O | No existing Python source files |
| `resume_tailor/cli.py` | utility | request-response | No existing Python source files |

**Planner action:** Use RESEARCH.md code examples as the implementation source. Every pattern in RESEARCH.md was verified against a live Python 3.11.2 environment on 2026-05-28. Treat them as authoritative.

---

## Metadata

**Analog search scope:** `/workspace` — all `.py` files, `pyproject.toml`, `resumes/`
**Files scanned:** 3 (pyproject.toml, resumes/english.tex, resumes/portuguese.tex)
**Python source files found:** 0
**Pattern extraction date:** 2026-05-28
**Pattern source:** RESEARCH.md verified code examples (stdlib only; no external dependencies for Phase 1 Python modules)
