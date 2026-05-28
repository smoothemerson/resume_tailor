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

key-decisions:
  - "Project name set to 'resume-tailor' per decision D-02 (renamed from 'en-cv-ai-engineer')"
  - "hatchling chosen as build backend — PyPA-maintained, uv's default, approved in RESEARCH.md audit"
  - "requests pinned at >=2.32.0 to capture GHSA-9wx4-h78v-vm56 urllib3 CVE fix"

# Metrics
duration: 1min
completed: 2026-05-28
---

# Phase 1 Plan 02: pyproject.toml — Installable Package Configuration Summary

**pyproject.toml updated from 7-line placeholder to fully installable package with hatchling build-backend, resume-tailor script entry point, and requests>=2.32.0 runtime dependency**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-28T13:35:08Z
- **Completed:** 2026-05-28T13:35:38Z
- **Tasks:** 1 of 2 auto-executed (Task 2 is a human-verify checkpoint)
- **Files modified:** 1

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

## Files Created/Modified

- `pyproject.toml` — Updated with all four required sections ([project], [project.scripts], [project.optional-dependencies], [build-system])

## Decisions Made

- Project name `resume-tailor` aligns with D-02 and is used as both the PyPI package name and the registered shell command
- hatchling selected as build backend — it is PyPA-maintained, the default for `uv init`, and pre-approved in the RESEARCH.md Package Legitimacy Audit
- `requests>=2.32.0` floor captures the GHSA-9wx4-h78v-vm56 urllib3 CVE fix (confirmed in RESEARCH.md)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Checkpoint Status

**Task 2 (checkpoint:human-verify)** is pending human verification. The user must run:

1. `uv tool install .` — expected output: "Installed 1 executable: resume-tailor"
2. `resume-tailor --help` — expected: usage message with "Tailor a LaTeX resume" and exit code 0

Until this checkpoint is approved, PKG-01 is not fully verified.

## User Setup Required

Run the following from `/workspace` to complete Phase 1 verification:

```bash
uv tool install .
resume-tailor --help
```

Expected exit code: 0. Expected output includes: "resume-tailor" and "Tailor a LaTeX resume".

## Next Phase Readiness

- pyproject.toml is now valid for `uv tool install .`
- Phase 2 (llm_client.py) can begin immediately — it imports from `resume_tailor.config` which is already implemented
- Phase 3 (cli.py full implementation) replaces the stub body while keeping the same entry point

---
*Phase: 01-foundation*
*Completed: 2026-05-28*
