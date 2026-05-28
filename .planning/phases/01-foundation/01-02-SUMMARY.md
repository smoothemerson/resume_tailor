---
phase: 01-foundation
plan: "02"
subsystem: packaging
tags: [python, pyproject, hatchling, uv, packaging, cli-entry-point]

# Dependency graph
requires:
  - 01-01 (resume_tailor package with cli.py stub)
provides:
  - Installable pyproject.toml with [build-system] (hatchling), [project.scripts], and [project.optional-dependencies]
  - resume-tailor shell command entry point registered via uv tool install .
affects: [02-llm-integration, 03-cli-integration]

# Tech tracking
tech-stack:
  added:
    - hatchling (build backend for uv tool install)
    - requests>=2.32.0 (runtime dependency)
    - ruff (dev dep for linting)
    - mypy (dev dep for type checking)
  patterns:
    - "[build-system] table with hatchling.build is required for uv tool install to register executables"
    - "[project.scripts] maps shell command name to Python entry point (module:function)"
    - "Project renamed from 'en-cv-ai-engineer' to 'resume-tailor' per D-02"

key-files:
  created: []
  modified:
    - pyproject.toml
  deviations:
    - README.md added (required by hatchling build backend — not in plan)

key-decisions:
  - "Project name set to 'resume-tailor' per decision D-02 (renamed from 'en-cv-ai-engineer')"
  - "hatchling chosen as build backend — PyPA-maintained, uv's default, approved in RESEARCH.md audit"
  - "requests pinned at >=2.32.0 to capture GHSA-9wx4-h78v-vm56 urllib3 CVE fix"
  - "README.md added to satisfy hatchling build requirement (plan listed readme = README.md but did not create it)"

requirements-completed: [PKG-01]

# Metrics
duration: 5min
completed: 2026-05-28
---

# Phase 1 Plan 02: pyproject.toml — Installable Package Configuration Summary

**pyproject.toml updated from 7-line placeholder to fully installable package with hatchling build-backend, resume-tailor script entry point, and requests>=2.32.0 runtime dependency**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-28T13:35:08Z
- **Completed:** 2026-05-28T13:35:38Z
- **Tasks:** 2 of 2 (Task 1: auto, Task 2: human-verify — APPROVED)
- **Files modified:** 2 (pyproject.toml updated, README.md created)

## Accomplishments

- Updated pyproject.toml from its 7-line placeholder state to a fully installable package configuration
- Renamed project from `"en-cv-ai-engineer"` to `"resume-tailor"` per D-02
- Added `dependencies = ["requests>=2.32.0"]` — only runtime dependency
- Added `[project.scripts]` table: `resume-tailor = "resume_tailor.cli:main"`
- Added `[project.optional-dependencies]` dev section with `ruff` and `mypy`
- Added `[build-system]` table with `hatchling.build` (CRITICAL for `uv tool install .` to register the shell command)
- Verified with tomllib parse-and-assert script — all five structural checks pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Update pyproject.toml with build-system, scripts, and dependencies** - `1da7288` (feat)
2. **Deviation: Add README.md required by hatchling** - `348913c` (docs)

## Files Created/Modified

- `pyproject.toml` — Updated with all four required sections ([project], [project.scripts], [project.optional-dependencies], [build-system])
- `README.md` — Created (deviation: required by hatchling build backend; plan referenced it but did not create it)

## Decisions Made

- Project name `resume-tailor` aligns with D-02 and is used as both the PyPI package name and the registered shell command
- hatchling selected as build backend — it is PyPA-maintained, the default for `uv init`, and pre-approved in the RESEARCH.md Package Legitimacy Audit
- `requests>=2.32.0` floor captures the GHSA-9wx4-h78v-vm56 urllib3 CVE fix (confirmed in RESEARCH.md)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added README.md required by hatchling build backend**
- **Found during:** Task 2 (human-verify checkpoint)
- **Issue:** pyproject.toml declares `readme = "README.md"` but the file did not exist; hatchling refused to build without it
- **Fix:** Added minimal README.md with project name and one-line description
- **Files modified:** README.md (created)
- **Commit:** 348913c

## Issues Encountered

None.

## Checkpoint Status

**Task 2 (checkpoint:human-verify) — APPROVED**

Human verification completed:

1. `uv tool install .` — output: "Installed 1 executable: resume-tailor" (PASS)
2. `resume-tailor --help` — showed usage message with "Tailor a LaTeX resume" (PASS)
3. Exit code: 0 (PASS)

PKG-01 is fully verified. Phase 1 is complete.

## Next Phase Readiness

**Phase 1 is complete.** All five success criteria verified:

1. `resume-tailor --help` (after `uv tool install .`) works — exit code 0, usage message shown (PASS)
2. config.py constants are importable and paths are anchored via Path(__file__) (PASS)
3. read_resume returns file content as string for valid .tex path (PASS)
4. write_resume creates timestamped .tex under resumes/output/ (PASS)
5. Missing resume file: prints stderr error, exits 1, no traceback (PASS)

Phase 2 (llm_client.py) can begin immediately:
- `from resume_tailor.config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT` resolves correctly
- The `resume-tailor` shell command is registered and functional
- Phase 3 (full cli.py) replaces the stub body while keeping the same entry point

---
*Phase: 01-foundation*
*Completed: 2026-05-28*
