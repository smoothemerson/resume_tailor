---
phase: 01-foundation
plan: "01"
subsystem: cli
tags: [python, pathlib, argparse, stdlib, config, file-io]

# Dependency graph
requires: []
provides:
  - resume_tailor Python package with five source files
  - config.py with OLLAMA_BASE_URL, OLLAMA_MODEL, BASE_RESUME_PATH, OUTPUT_DIR, TIMEOUT constants anchored via Path(__file__)
  - read_resume(path: Path) -> str with FileNotFoundError handling and stderr exit(1)
  - write_resume(content: str, output_dir: Path) -> Path with timestamped output under output_dir
  - cli.py stub with main() entry point for uv tool install resolution
affects: [02-foundation, 02-llm-integration, 03-cli-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Path(__file__).parent anchoring for config constants (cwd-independent)"
    - "Module-level constants only in config.py — no class, no env var loading"
    - "FileNotFoundError caught at read site: print to stderr, sys.exit(1)"
    - "Timestamped output filenames: tailored_resume_YYYYMMDD_HHMMSS.tex"
    - "Path.read_text/write_text with encoding='utf-8' over open()"
    - "mkdir(parents=True, exist_ok=True) for idempotent directory creation"

key-files:
  created:
    - resume_tailor/__init__.py
    - resume_tailor/config.py
    - resume_tailor/cli.py
    - resume_tailor/resume_reader.py
    - resume_tailor/resume_writer.py
  modified: []

key-decisions:
  - "OLLAMA_MODEL = 'mistral-small3.2:24b' — exact model string per D-03, not an alias"
  - "BASE_RESUME_PATH anchored via Path(__file__) not Path('resumes/...') — survives uv tool install (D-01, CONF-02)"
  - "cli.py Phase 1 stub: defines main() so uv tool install can resolve the entry point; Phase 3 adds full implementation"
  - "All error handling scoped to individual modules (read_resume catches FileNotFoundError locally)"

patterns-established:
  - "Pattern 1: config.py uses _HERE/_ROOT private anchors before public constants"
  - "Pattern 2: resume_reader.py handles FileNotFoundError inline — no raw tracebacks to user"
  - "Pattern 3: resume_writer.py returns Path of written file for caller display"

requirements-completed: [CONF-01, CONF-02, CORE-01, CORE-05, ERR-01]

# Metrics
duration: 2min
completed: 2026-05-28
---

# Phase 1 Plan 01: resume_tailor Package — config, reader, writer, cli stub Summary

**Five-module resume_tailor package with Path(__file__)-anchored config, FileNotFoundError-safe reader, timestamped writer, and cli.py entry point stub**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-28T13:30:42Z
- **Completed:** 2026-05-28T13:32:13Z
- **Tasks:** 2
- **Files modified:** 5 created

## Accomplishments

- Created resume_tailor/ Python package with all five source files required by Phase 1
- config.py establishes the five public constants (OLLAMA_BASE_URL, OLLAMA_MODEL, BASE_RESUME_PATH, OUTPUT_DIR, TIMEOUT) at module level with Path(__file__) anchoring — cwd-independent after uv tool install
- resume_reader.py reads english.tex as UTF-8 string with inline FileNotFoundError handling (prints to stderr, exits 1)
- resume_writer.py creates timestamped .tex files under any output directory, creating parent directories as needed, and returns the written Path
- cli.py stub defines main() so the pyproject.toml entry point `resume_tailor.cli:main` can be resolved by uv tool install before Phase 3 is implemented

## Task Commits

Each task was committed atomically:

1. **Task 1: Create resume_tailor package — config.py, __init__.py, and cli.py stub** - `1b388c7` (feat)
2. **Task 2: Create resume_reader.py and resume_writer.py** - `f82a110` (feat)

## Files Created/Modified

- `resume_tailor/__init__.py` - Python package marker with single comment line
- `resume_tailor/config.py` - Five module-level constants; _HERE/_ROOT anchors from Path(__file__)
- `resume_tailor/cli.py` - Phase 1 stub: argparse ArgumentParser with main() for entry point resolution
- `resume_tailor/resume_reader.py` - read_resume(path: Path) -> str; FileNotFoundError -> stderr + exit(1)
- `resume_tailor/resume_writer.py` - write_resume(content: str, output_dir: Path) -> Path; timestamped filename; mkdir parents

## Decisions Made

- OLLAMA_MODEL set to exact string `"mistral-small3.2:24b"` per D-03 — single change point for model swaps
- BASE_RESUME_PATH uses `Path(__file__).parent.parent / "resumes" / "english.tex"` per D-01/CONF-02 — survives `uv tool install` where cwd is unrelated to the package location
- cli.py stub created now (Phase 1) rather than Phase 3 to prevent `ModuleNotFoundError` during packaging
- Error handling scoped to the module that owns the I/O (resume_reader.py catches FileNotFoundError directly) rather than propagating to main()

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All five package files exist under resume_tailor/ and are importable
- Phase 2 (llm_client.py) can import `from resume_tailor.config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT` immediately
- Phase 3 (cli.py full implementation) can import `read_resume`, `write_resume`, and replace the cli.py stub's body
- pyproject.toml update (Plan 02) can add `[project.scripts]` and `[build-system]` — the entry point `resume_tailor.cli:main` already resolves

---
*Phase: 01-foundation*
*Completed: 2026-05-28*
