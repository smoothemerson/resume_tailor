---
phase: 14-infrastructure
fixed_at: 2026-06-13T00:00:00Z
review_path: .planning/phases/14-infrastructure/14-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 14: Code Review Fix Report

**Fixed at:** 2026-06-13T00:00:00Z
**Source review:** .planning/phases/14-infrastructure/14-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (2 Critical, 3 Warning)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `uv.lock` gitignored — CI resolves unpinned deps on every run

**Files modified:** `.gitignore`, `.github/workflows/ci.yml`
**Commit:** 8ed8238
**Applied fix:** Removed `uv.lock` from `.gitignore` so the lockfile can be committed. Added `--locked` flag to the `uv sync` CI step so CI enforces the committed lockfile. Note: `uv` is not available in this environment, so `uv lock` must be run manually by the developer to generate and commit `uv.lock` before CI will pass with `--locked`.

---

### CR-02: Duplicate test files cause doubled test execution and divergent coverage

**Files modified:** `src/jd_analyzer_test.py` (deleted), `src/resume_reader_test.py` (deleted), `src/resume_writer_test.py` (deleted), `pyproject.toml`
**Commit:** f2e88c0
**Applied fix:** Deleted the three duplicate test files from `src/`. `src/resume_reader_test.py` and `src/resume_writer_test.py` were byte-for-byte identical to their `tests/unit/` counterparts. `src/jd_analyzer_test.py` tested the private `_parse_analysis_response` helper rather than the public API. Updated `testpaths` in `pyproject.toml` from `["src", "tests"]` to `["tests"]` so pytest only collects the canonical suite.

---

### WR-01: Test name asserts the opposite of what the test verifies

**Files modified:** `tests/unit/test_jd_analyzer.py`
**Commit:** 339fd7f
**Applied fix:** Renamed `test_analyze_job_description_returns_none_on_fence_wrapped_valid_json` to `test_analyze_job_description_returns_dict_on_fence_wrapped_valid_json` at line 77. The test body asserts `isinstance(result, dict)` and `result is not None`; the name now matches those assertions.

---

### WR-02: Wheel include allowlist will cause the same bug again on the next new module

**Files modified:** `pyproject.toml`
**Commit:** 69dc426
**Applied fix:** Replaced the 10-item explicit file list in `[tool.hatch.build.targets.wheel]` with `include = ["src/*.py"]` and `exclude = ["src/*_test.py"]`. Any new module added to `src/` is now automatically included in the wheel without requiring a manual list update.

---

### WR-03: CI workflow declares no permissions — `GITHUB_TOKEN` defaults to read/write

**Files modified:** `.github/workflows/ci.yml`
**Commit:** 2001aed
**Applied fix:** Added `permissions: contents: read` at the workflow level immediately after the `on:` section. A lint-and-test job requires only read access; this limits the blast radius if a step or third-party action is compromised.

---

_Fixed: 2026-06-13T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
