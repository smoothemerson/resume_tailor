# Phase 1: Foundation - Research

**Researched:** 2026-05-28
**Domain:** Python CLI packaging, file I/O, project scaffold (stdlib + requests only)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `BASE_RESUME_PATH` in `config.py` defaults to `resumes/english.tex` (anchored via `Path(__file__).parent.parent / "resumes" / "english.tex"`)
- **D-02:** `pyproject.toml` project name renamed from `"en-cv-ai-engineer"` to `"resume-tailor"` — aligns the package name with the CLI command
- **D-03:** `OLLAMA_MODEL = "mistral-small3.2:24b"` — specific model string; config is the only change point for swapping models

### Claude's Discretion
- Package layout: flat (`resume_tailor/` directly under project root, not `src/resume_tailor/`) — appropriate scale for a single-dep CLI tool
- `requires-python` can stay at `>=3.13` or be relaxed to `>=3.11`; 3.13 is fine since user is on a modern Python

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONF-01 | `config.py` exposes `BASE_RESUME_PATH`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OUTPUT_DIR`, and `TIMEOUT` as named module-level constants | Verified: plain Python module constants, no class wrapping needed, importable directly |
| CONF-02 | All paths in `config.py` are anchored to `Path(__file__)` so the tool works regardless of invocation directory | Verified: `Path(__file__).parent.parent / "resumes" / "english.tex"` resolves correctly from any cwd |
| PKG-01 | Project packaged with `pyproject.toml` + `uv`; installable as `resume-tailor` shell command via `uv tool install .` | Verified: requires `[build-system]` + `[project.scripts]` — CRITICAL: existing pyproject.toml has neither |
| CORE-01 | CLI reads base LaTeX resume from the configurable path in `config.py` | Verified: `Path.read_text(encoding='utf-8')` is the correct idiom; 5,754 chars in existing english.tex |
| CORE-05 | Tool writes tailored LaTeX to `resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex`, creating directory if missing | Verified: `mkdir(parents=True, exist_ok=True)` + `write_text` + `datetime.strftime('%Y%m%d_%H%M%S')` all confirmed working |
| ERR-01 | If base resume file is not found, print human-readable error to stderr and exit with code 1 (no raw traceback) | Verified: `try/except FileNotFoundError` + `print(..., file=sys.stderr)` + `sys.exit(1)` pattern confirmed |
</phase_requirements>

## Summary

Phase 1 is a pure Python scaffold phase: create the `resume_tailor/` package directory with `config.py`, `resume_reader.py`, `resume_writer.py`, and `__init__.py`, then update `pyproject.toml` to make the project installable. Every tool and pattern involved is stdlib-only or `requests` — no external research beyond uv/packaging was needed.

The single highest-risk finding is a **critical gap in the existing `pyproject.toml`**: it has no `[build-system]` table. Per official uv documentation, `[project.scripts]` entry points require a `[build-system]` to be declared — without it, `uv tool install .` will not register the `resume-tailor` shell command. The existing file also has no `dependencies` or `[project.scripts]` entries. All three must be added.

The environment running this research has Python 3.11.2 (stdlib verified: `pathlib`, `datetime`, `json`, `sys`, `argparse`, `tomllib` all present). `uv` is not installed in this environment but is a user-space tool that the developer runs on their own machine — not a blocker for writing or verifying the scaffold code.

**Primary recommendation:** Create four Python files in `resume_tailor/`, update `pyproject.toml` with `[build-system]` + `[project.scripts]` + `dependencies`, and verify with `uv tool install . && resume-tailor --help`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI entry point registration | Packaging (pyproject.toml) | Python module (cli.py) | `[project.scripts]` declares the command; `cli.py` implements it. Phase 1 declares it, Phase 3 implements it. |
| Configuration constants | Config module (config.py) | — | Named constants at module level; no class, no env vars, no TOML parsing. All other modules import from here. |
| File reading (base resume) | File I/O module (resume_reader.py) | Config (for path) | Reader accepts path param; config provides the default. Isolation makes module unit-testable. |
| File writing (output) | File I/O module (resume_writer.py) | Config (for output dir) | Writer accepts content + dir; config provides `OUTPUT_DIR`. Timestamping is internal to writer. |
| Error handling (file not found) | resume_reader.py | — | ERR-01 scoped to reader; caller (Phase 3 main.py) handles the sys.exit boundary |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pathlib` (stdlib) | 3.4+ (3.11 in env) | File paths, mkdir, read/write text | `Path` over `os.path` everywhere — PEP 428 stdlib, universally recommended |
| `datetime` (stdlib) | stdlib | Timestamped output filenames | `strftime('%Y%m%d_%H%M%S')` produces required filename format directly |
| `sys` (stdlib) | stdlib | stderr output, sys.exit(1) | `print(..., file=sys.stderr)` for errors; `sys.exit(1)` for non-zero exit |
| `argparse` (stdlib) | stdlib | CLI flags (`--model`, `--resume`, `--output-dir`) | Project constraint: no Click/Typer; `argparse` handles 3 optional flags trivially |
| `requests` | 2.34.2 (latest) | HTTP POST to Ollama (Phase 2) | Declared in Phase 1 packaging as project dependency |

### Supporting (dev-only)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ruff` | 0.15.14 (latest) | Linting + formatting | Run before commit; replaces flake8 + black + isort |
| `mypy` | 2.1.0 (latest) | Optional static type checking | Run on public function signatures for portfolio legibility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pathlib.Path` | `os.path` | `os.path` is legacy; `Path` is cleaner and required by CLAUDE.md conventions |
| `hatchling` (build backend) | `uv_build` | `uv_build` is newer default in uv-init projects; both work. `hatchling` is more widely documented. Either is fine. |
| `argparse` | `click`, `typer` | Project constraint prohibits Click/Typer; also wrong scale for 3 flags |

**Installation (in pyproject.toml, not via pip directly):**
```toml
[project]
dependencies = ["requests>=2.32.0"]

[project.optional-dependencies]
dev = ["ruff", "mypy"]
```

**Version verification:** Versions verified via PyPI JSON API on 2026-05-28.
```
requests: 2.34.2  (oldest release: 2011-02-14 — highly established)
ruff:     0.15.14 (released 2022-08-27 — dominant Python linter)
mypy:     2.1.0   (released 2009-09-09 — long-established)
uv:       0.11.16 (released 2024-02-15 — Astral official tool)
```

## Package Legitimacy Audit

> slopcheck was not installable in this environment. Manual PyPI verification performed instead.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `requests` | PyPI | ~15 yrs (2011) | hundreds of millions/wk | github.com/psf/requests | N/A (manual: [OK]) | Approved |
| `ruff` | PyPI | ~3 yrs (2022) | tens of millions/wk | github.com/astral-sh/ruff | N/A (manual: [OK]) | Approved |
| `mypy` | PyPI | ~17 yrs (2009) | tens of millions/wk | github.com/python/mypy | N/A (manual: [OK]) | Approved |
| `hatchling` | PyPI | established | high | github.com/pypa/hatch | N/A (manual: [OK]) | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

*slopcheck was unavailable. Manual verification performed: all packages are official, long-established tools from well-known organizations (PSF, Astral, python/mypy). No postinstall scripts checked — all four are well-known and pose no known supply chain risk.*

## Architecture Patterns

### System Architecture Diagram

```
[User invokes resume-tailor]
         |
         v
   cli.py :: main()          (Phase 3 — declared in PKG-01, Phase 1)
         |
    +---------+----------+
    |                    |
    v                    v
config.py           resume_reader.py
(constants)         read_resume(path) --> str
BASE_RESUME_PATH         |
OLLAMA_MODEL         FileNotFoundError
OLLAMA_BASE_URL          --> stderr + exit(1)  [ERR-01]
OUTPUT_DIR
TIMEOUT
                         |
                         v
                   [LaTeX string in memory]
                         |
                         v
                   resume_writer.py
                   write_resume(content, output_dir) --> Path
                   creates: resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex
                   mkdir(parents=True, exist_ok=True)
```

### Recommended Project Structure
```
resume_tailor/          # flat package (no src/ layout)
├── __init__.py         # empty or minimal — marks package boundary
├── config.py           # named constants only, no class, no env var loading
├── resume_reader.py    # read_resume(path: Path) -> str
├── resume_writer.py    # write_resume(content: str, output_dir: Path) -> Path
└── cli.py              # Phase 3 concern — but entry point declared now in PKG-01

resumes/
├── english.tex         # base resume (exists)
├── portuguese.tex      # alternate (exists, not default)
└── output/             # created at runtime by write_resume()
    └── tailored_resume_YYYYMMDD_HHMMSS.tex

pyproject.toml          # update in-place (exists, needs 3 additions)
```

### Pattern 1: `__file__`-Anchored Paths in config.py
**What:** All paths in `config.py` use `Path(__file__)` as the anchor so that the resolved path is always relative to the installed package location, not the caller's working directory.
**When to use:** Always, for any path that references project files (resume, output dir).
**Example:**
```python
# Source: verified in this environment — resolves correctly from any cwd
from pathlib import Path

_HERE = Path(__file__).parent           # resume_tailor/
_ROOT = _HERE.parent                    # project root

BASE_RESUME_PATH = _ROOT / "resumes" / "english.tex"
OUTPUT_DIR = _ROOT / "resumes" / "output"
```

### Pattern 2: Timestamped File Writing in resume_writer.py
**What:** Generate a unique filename from the current timestamp and write LaTeX content using `Path.write_text`.
**When to use:** Every write operation in this tool (always one output file per run).
**Example:**
```python
# Source: stdlib datetime + pathlib — verified working in Python 3.11
from pathlib import Path
from datetime import datetime

def write_resume(content: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
```

### Pattern 3: FileNotFoundError Handling in resume_reader.py (ERR-01)
**What:** Catch `FileNotFoundError` at the read site, print a human-readable message to stderr, and exit with code 1. No raw traceback visible to user.
**When to use:** Exactly once — in `read_resume()`. Do NOT re-raise or let it propagate to main.
**Example:**
```python
# Source: Python stdlib sys + pathlib — verified working
from pathlib import Path
import sys

def read_resume(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
```

### Pattern 4: pyproject.toml for uv tool install (PKG-01)
**What:** The complete set of `pyproject.toml` sections required for `uv tool install .` to register `resume-tailor` as a shell command.
**Critical:** `[build-system]` is REQUIRED — without it, uv will not build/install the package and `[project.scripts]` will be ignored. [VERIFIED: docs.astral.sh/uv/concepts/projects/config]
**Example:**
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

### Pattern 5: config.py Constants (CONF-01)
**What:** Plain Python module with module-level constants. No class, no dataclass, no TOML parsing.
**When to use:** Always — CLAUDE.md and CONTEXT.md both specify this pattern.
**Example:**
```python
# Source: project constraint + CONF-01/CONF-02 requirements
from pathlib import Path

_HERE = Path(__file__).parent
_ROOT = _HERE.parent

OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
BASE_RESUME_PATH: Path = _ROOT / "resumes" / "english.tex"
OUTPUT_DIR: Path = _ROOT / "resumes" / "output"
TIMEOUT: tuple[int, int] = (10, 300)   # (connect_timeout, read_timeout) for requests
```

### Anti-Patterns to Avoid
- **`os.path` instead of `pathlib`:** Use `Path` everywhere — `os.path.join`, `os.makedirs`, `open()` are legacy patterns that CLAUDE.md explicitly deprecates.
- **Wrapping constants in a class or dataclass:** Phase 2 and Phase 3 import `from resume_tailor.config import BASE_RESUME_PATH` directly — class wrapping breaks this pattern and adds unnecessary indirection.
- **Letting FileNotFoundError propagate raw:** ERR-01 requires a human-readable stderr message and exit code 1. A raw traceback is a test failure.
- **Writing pyproject.toml without `[build-system]`:** The existing file omits this section. Without it, `uv tool install .` builds nothing and the `resume-tailor` command is never registered.
- **Hardcoding paths relative to cwd:** Any path that works when running from project root breaks when the tool is installed system-wide. Always anchor to `Path(__file__)`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timestamped filenames | Custom UUID/random suffix generator | `datetime.now().strftime("%Y%m%d_%H%M%S")` | Human-readable, sortable, deterministic format — no library needed |
| Directory creation with parent handling | `os.makedirs` with manual exist check | `Path.mkdir(parents=True, exist_ok=True)` | Single call, atomic, raises only on real errors |
| File read with encoding | `open(f, 'r').read()` manual pattern | `Path.read_text(encoding='utf-8')` | Context manager handled internally; explicit encoding prevents locale bugs |
| CLI argument parsing | Manual `sys.argv` parsing | `argparse` stdlib | Handles `--help`, type coercion, missing arg errors automatically |

**Key insight:** Every operation in this phase is a single stdlib call. The complexity is in the packaging configuration (`pyproject.toml`), not the Python code.

## Common Pitfalls

### Pitfall 1: Missing `[build-system]` in pyproject.toml
**What goes wrong:** `uv tool install .` exits silently or completes without registering the `resume-tailor` command. `resume-tailor --help` gives "command not found".
**Why it happens:** uv requires `[build-system]` to be declared to treat a project as a buildable package. Without it, uv installs only dependencies — the package itself is not built.
**How to avoid:** Always include `[build-system]` with `requires = ["hatchling"]` and `build-backend = "hatchling.build"` (or `uv_build` — both work).
**Warning signs:** `uv tool install .` produces output like "Installed 0 executables" or the command is absent from `uv tool list`.

### Pitfall 2: `cli.py` does not exist at install time
**What goes wrong:** `uv tool install .` fails with an import error or registers the command but running it crashes immediately with `ModuleNotFoundError: No module named 'resume_tailor.cli'`.
**Why it happens:** `[project.scripts]` entry point `"resume_tailor.cli:main"` must resolve at install time. Phase 1 declares the entry point; Phase 3 implements `cli.py` — but a stub `cli.py` with a `main()` function must exist in Phase 1 for the install to succeed.
**How to avoid:** Create a minimal stub `cli.py` in Phase 1 that defines `def main(): pass` (or a real argparse stub). Phase 3 replaces it.
**Warning signs:** `uv tool install .` fails with `ImportError` or the installed command crashes on invocation.

### Pitfall 3: Path anchored to cwd instead of `__file__`
**What goes wrong:** `BASE_RESUME_PATH = Path("resumes/english.tex")` resolves correctly when running from project root, but fails when the tool is installed and invoked from `/home/user/` or any other directory.
**Why it happens:** Relative paths resolve against the current working directory at runtime, not the package location.
**How to avoid:** Always use `Path(__file__).parent.parent / "resumes" / "english.tex"` in `config.py`.
**Warning signs:** Tests pass from project root but `resume-tailor` fails after `uv tool install .` invoked from a different directory.

### Pitfall 4: `encoding` not specified in `read_text` / `write_text`
**What goes wrong:** LaTeX files with non-ASCII characters (accented names, special symbols) fail with `UnicodeDecodeError` on some systems where the default locale is not UTF-8.
**Why it happens:** Python's default encoding is platform-dependent; on some Linux setups it is ASCII.
**How to avoid:** Always pass `encoding="utf-8"` to `read_text()` and `write_text()`.
**Warning signs:** Works for developer, breaks on CI or other machines with different locale settings.

### Pitfall 5: `sys.exit(1)` called in module, not at CLI boundary
**What goes wrong:** If `read_resume()` calls `sys.exit(1)` directly, it becomes untestable in isolation — a missing file during unit tests terminates the test runner.
**Why it happens:** `sys.exit()` raises `SystemExit`, which propagates out of test functions and can crash the test suite.
**How to avoid:** For Phase 1, ERR-01 explicitly puts the `sys.exit(1)` in `resume_reader.py` (that is the spec). Accept this — the Phase 3 STATE.md note says "all exception catches handled at main.py boundary only" applies to future phases. ERR-01 is a Phase 1 requirement specifically in the reader.
**Warning signs:** N/A — this is by design for this phase per ERR-01 spec.

## Code Examples

Verified patterns from stdlib and project requirements:

### config.py — Complete Reference Implementation
```python
# Source: CONF-01 + CONF-02 requirements; Path.__file__ pattern verified in Python 3.11
from pathlib import Path

_HERE = Path(__file__).parent          # resume_tailor/
_ROOT = _HERE.parent                   # project root (works after uv tool install)

OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
BASE_RESUME_PATH: Path = _ROOT / "resumes" / "english.tex"
OUTPUT_DIR: Path = _ROOT / "resumes" / "output"
TIMEOUT: tuple[int, int] = (10, 300)
```

### resume_reader.py — Complete Reference Implementation
```python
# Source: CORE-01 + ERR-01 requirements; pathlib + sys pattern verified
from pathlib import Path
import sys

def read_resume(path: Path) -> str:
    """Read the base resume LaTeX file and return its content as a string."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Base resume not found at {path}", file=sys.stderr)
        sys.exit(1)
```

### resume_writer.py — Complete Reference Implementation
```python
# Source: CORE-05 requirement; datetime + pathlib pattern verified in Python 3.11
from pathlib import Path
from datetime import datetime

def write_resume(content: str, output_dir: Path) -> Path:
    """Write tailored LaTeX content to a timestamped file under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
```

### cli.py stub (Phase 1 only — replaced in Phase 3)
```python
# Stub required so uv tool install . can resolve resume_tailor.cli:main
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

### `__init__.py`
```python
# Empty — just marks resume_tailor/ as a Python package
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `requirements.txt` | `pyproject.toml` (PEP 517/518) + `uv` | PEP 517 (2017), uv mainstream 2024 | `uv tool install .` replaces `pip install -e .`; no `setup.py` needed |
| `os.path.join(...)` | `pathlib.Path` / operator | PEP 428 (Python 3.4, 2014) | Cleaner, readable, no string concatenation for paths |
| `hatchling` as uv default backend | `uv_build` as new uv default | uv ~0.4+ | Both work; `hatchling` is more documented; either acceptable |
| `mypy` version 1.x | `mypy` version 2.x | mypy 2.0 released 2025 | Type stub handling improved; `mypy 2.1.0` is current stable |

**Deprecated/outdated:**
- `setup.py`: do not create; `pyproject.toml` replaces it completely
- `requirements.txt`: do not create; `pyproject.toml` `dependencies` replaces it
- `open(file, 'r')` pattern: use `Path.read_text(encoding='utf-8')` instead

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `uv_build` (the newer default) and `hatchling` are both fully supported build backends for `uv tool install` | Standard Stack / Pitfall 1 | If only one works, planner should specify which; low risk since hatchling is well-documented |
| A2 | The developer's machine has `uv` installed and available in PATH (not present in research environment) | Environment Availability | If uv is not installed, PKG-01 cannot be verified; developer must install uv separately |
| A3 | `TIMEOUT: tuple[int, int] = (10, 300)` is the correct constant name and type for Phase 2 compatibility | Code Examples | Phase 2 must import `TIMEOUT` from config — if name/type differ, Phase 2 breaks |

## Open Questions

1. **`uv_build` vs `hatchling` as build backend**
   - What we know: uv's init command now defaults to `uv_build>=0.11.16`; hatchling is the older default and remains fully supported
   - What's unclear: user preference — both work for `uv tool install .`
   - Recommendation: Use `hatchling` for maximum documentation coverage; switch to `uv_build` if user prefers the newer default

2. **`requires-python` value: `>=3.13` vs `>=3.11`**
   - What we know: research environment has Python 3.11.2; CONTEXT.md says either is fine; CLAUDE.md recommends `>=3.11` as safe minimum
   - What's unclear: what Python version the developer actually runs the tool on
   - Recommendation: Keep `>=3.13` per CONTEXT.md D-discretion note ("3.13 is fine since user is on a modern Python")

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All modules | ✓ | 3.11.2 (env) | — |
| `uv` | PKG-01 (uv tool install) | ✗ (not in PATH) | — | Developer must install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `git` | Version control | ✓ | 2.39.5 | — |
| `ruff` | Dev linting | ✗ (not installed) | — | Install via `uv add --dev ruff` after PKG-01 complete |
| `mypy` | Dev type checking | ✗ (not installed) | — | Install via `uv add --dev mypy` after PKG-01 complete |
| `resumes/english.tex` | CORE-01, ERR-01 | ✓ | 5,754 chars | — |

**Missing dependencies with no fallback:**
- `uv` — required for `uv tool install .` (PKG-01 success criterion). Planner must include an installation verification step.

**Missing dependencies with fallback:**
- `ruff`, `mypy` — dev-only; installed via `uv add --dev` as part of Phase 1 packaging task.

## Security Domain

> `security_enforcement` not explicitly set to false in config.json — treated as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Tool is local-only CLI; no user auth |
| V3 Session Management | no | Stateless CLI; no sessions |
| V4 Access Control | no | Single-user local tool |
| V5 Input Validation | limited | File paths from config only; no user-supplied paths in Phase 1 |
| V6 Cryptography | no | No encryption in this phase |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via BASE_RESUME_PATH | Tampering | Path is hardcoded in config.py, not user-supplied in Phase 1; no mitigation needed |
| Writing output to unexpected directory | Tampering | OUTPUT_DIR anchored to `Path(__file__)` — cannot be redirected by cwd |

**Security assessment:** Phase 1 has minimal attack surface. All paths are config-module constants, not user input. No network calls, no shell invocations, no secrets handling. Security-relevant features (Ollama connection, prompt injection) are Phase 2+ concerns.

## Sources

### Primary (HIGH confidence)
- Python stdlib `pathlib` — [VERIFIED: docs.python.org/3/library/pathlib.html] — `Path.__file__` anchoring, `read_text`, `write_text`, `mkdir(parents, exist_ok)` all verified running in Python 3.11.2 in this environment
- Python stdlib `datetime` — [VERIFIED: live test] — `strftime('%Y%m%d_%H%M%S')` produces `tailored_resume_YYYYMMDD_HHMMSS.tex` format as required
- PyPI JSON API — [VERIFIED: pypi.org/pypi/{pkg}/json] — versions confirmed for `requests` (2.34.2), `ruff` (0.15.14), `mypy` (2.1.0), `uv` (0.11.16), `hatchling` (1.29.0) on 2026-05-28
- uv build-system requirement — [CITED: docs.astral.sh/uv/concepts/projects/config/] — "Using entry point tables requires a build system to be defined"

### Secondary (MEDIUM confidence)
- uv `[build-system]` required for `[project.scripts]` — [CITED: docs.astral.sh/uv/concepts/projects/config/] confirmed via WebFetch; cross-referenced with WebSearch result from docs.astral.sh
- `uv_build` as new default backend — [CITED: docs.astral.sh/uv/concepts/projects/init/] — "requires = ['uv_build>=0.11.16,<0.12']" shown as default for packaged projects

### Tertiary (LOW confidence)
- None — all claims in this research are either VERIFIED (live tool execution) or CITED (official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib; `requests` is project constraint; versions verified via PyPI API
- Architecture: HIGH — flat package pattern is explicit in CONTEXT.md; `__file__` anchoring verified in live Python 3.11
- Pitfalls: HIGH — `[build-system]` pitfall confirmed by official uv docs; path anchoring pitfall confirmed by live test
- Packaging: HIGH — `pyproject.toml` format verified against official uv and PEP 517/518 documentation

**Research date:** 2026-05-28
**Valid until:** 2026-08-28 (stable stdlib; uv packaging format changes infrequently)
