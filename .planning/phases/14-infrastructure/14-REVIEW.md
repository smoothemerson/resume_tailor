---
phase: 14-infrastructure
reviewed: 2026-06-11T21:22:07Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - .github/workflows/ci.yml
  - .gitignore
  - pyproject.toml
  - src/jd_analyzer_test.py
  - src/resume_reader_test.py
  - src/resume_writer_test.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-06-11T21:22:07Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the phase 14 infrastructure deliverables: CI workflow, .gitignore rewrite, pyproject wheel-include fix, and three new src-colocated test files. All new test assertions were traced against the actual implementations (`_parse_analysis_response`, `read_resume`, `write_resume`) and are logically correct — every expected outcome matches the real code paths, and all three files compile. No critical defects found.

However, the headline deliverable claim of "12 new unit tests" does not hold up: `src/resume_reader_test.py` and `src/resume_writer_test.py` are byte-for-byte identical copies of pre-existing `tests/unit/test_resume_reader.py` and `tests/unit/test_resume_writer.py` (verified with `diff`), and `src/jd_analyzer_test.py` largely re-covers behaviors already exercised by `tests/unit/test_jd_analyzer.py` at a different layer. Because `testpaths = ["src", "tests"]`, the duplicated tests run twice in every CI invocation and must now be maintained in two places. Additional warnings concern CI reproducibility (no lock file), missing workflow permissions hardening, and a recurrence-prone wheel include allowlist.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Six of the twelve "new" unit tests are verbatim duplicates of existing tests

**File:** `src/resume_reader_test.py:1-16`, `src/resume_writer_test.py:1-33`, `src/jd_analyzer_test.py:1-39`
**Issue:** `src/resume_reader_test.py` and `src/resume_writer_test.py` are byte-identical to `tests/unit/test_resume_reader.py` and `tests/unit/test_resume_writer.py` respectively (confirmed via `diff` — zero differing lines, including identical test function names). `src/jd_analyzer_test.py` re-covers fenced-JSON, non-JSON, and missing-key behavior already tested in `tests/unit/test_jd_analyzer.py` through `analyze_job_description` with mocked `requests.post`. With `testpaths = ["src", "tests"]` in pyproject.toml, every duplicated test is collected and executed twice per run, and any behavior change now requires editing two files. The repo now has two competing test layout conventions (src-colocated `*_test.py` vs `tests/unit/test_*.py`) with no rule about which wins.
**Fix:** Pick one layout and delete the other copy. If src-colocation is the convention going forward, delete `tests/unit/test_resume_reader.py`, `tests/unit/test_resume_writer.py`, and migrate the unique `analyze_job_description` mock tests from `tests/unit/test_jd_analyzer.py` into `src/jd_analyzer_test.py`; otherwise delete the three new src files.

### WR-02: CI dependency resolution is unpinned — uv.lock is gitignored, so every CI run resolves fresh

**File:** `.github/workflows/ci.yml:21`, `.gitignore:17`
**Issue:** `uv sync` in CI resolves dependencies from scratch on every run because `uv.lock` is listed in `.gitignore` and not committed. A new release of `requests`, `pytest`, or `ruff` can break or change CI behavior with zero repo changes, making failures non-reproducible locally. This also directly contradicts the project's own stack documentation in CLAUDE.md: "pyproject.toml + uv.lock is the correct packaging baseline even for a single-dep project." Particularly risky for `ruff format --check`, where a new ruff version with changed formatting rules will fail CI on untouched code.
**Fix:** Remove `uv.lock` from `.gitignore`, commit the lock file, and change the CI step to:
```yaml
- name: Install dependencies
  run: uv sync --locked
```

### WR-03: Workflow has no permissions block — GITHUB_TOKEN gets default (potentially write) scope

**File:** `.github/workflows/ci.yml:9`
**Issue:** No `permissions:` key is declared at workflow or job level, so the job's `GITHUB_TOKEN` inherits the repository default, which is read/write on many repos. A lint+test job needs only read access to checkout. If any step (or a compromised third-party action — see IN-04) is subverted, the token could push commits or tamper with the repo. Least-privilege token scoping is the baseline GitHub Actions hardening control.
**Fix:**
```yaml
permissions:
  contents: read
```
at the top level of the workflow, below `on:`.

### WR-04: Wheel include allowlist is the exact failure mode this phase just fixed

**File:** `pyproject.toml:18-29`
**Issue:** The bug this phase fixed (broken wheel because `jd_analyzer.py` and `keyword_matcher.py` were absent from the include list) is guaranteed to recur: the fix keeps the manual per-file allowlist, so the next module added to `src/` will silently be omitted from the wheel again. Nothing in CI builds or installs the wheel, so the breakage would again go undetected until install time.
**Fix:** Replace the enumerated list with a pattern that cannot drift:
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = ["src/*.py"]
exclude = ["src/*_test.py"]
```

### WR-05: Wheel installs generic top-level module names into site-packages

**File:** `pyproject.toml:16-29`
**Issue:** With `sources = ["src"]` and flat modules, installing this wheel places `cli.py`, `config.py`, `guards.py`, etc. as top-level modules in site-packages. Names like `config` and `cli` are highly collision-prone: any other package in the same environment that ships or imports a top-level `config` will silently get this project's module (or vice versa), and the entry point `resume-tailor = "cli:main"` breaks if anything shadows `cli`. Pre-existing structure, but the include list was the subject of this phase's change and the defect ships with every wheel built from this file.
**Fix:** Move modules into a package directory (`src/resume_tailor/`), set `packages = ["src/resume_tailor"]`, and change the script to `resume-tailor = "resume_tailor.cli:main"`. If deferred, record it as a known limitation requiring isolated installs (`uv tool install` / pipx).

## Info

### IN-01: Timestamp filename assertion is not end-anchored

**File:** `src/resume_writer_test.py:26`
**Issue:** `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)` anchors only the start; a filename like `tailored_resume_20260611_212207.tex.bak` would also pass. The current implementation cannot produce such a name, but the assertion is weaker than intended for a regression test.
**Fix:** Use `re.fullmatch(...)`.

### IN-02: Fenced-JSON test asserts only non-None, not parsed content

**File:** `src/jd_analyzer_test.py:27-29`
**Issue:** `test_parse_fenced_json_returns_dict` asserts `is not None` but never checks that the fences were actually stripped and the values survived parsing. A regression that returned `{"technologies": [], "requirements": [], "emphasis_areas": []}` (or otherwise mangled values) would still pass.
**Fix:** `assert _parse_analysis_response(content) == {"technologies": ["Go"], "requirements": ["3 yrs"], "emphasis_areas": ["backend"]}`

### IN-03: CI lint and format checks skip the tests/ tree

**File:** `.github/workflows/ci.yml:24-26`
**Issue:** `ruff check src/` and `ruff format --check src/` exclude `tests/`, so the conftest and the test files under `tests/` (which CI executes) are never linted or format-checked.
**Fix:** Run `uv run ruff check .` and `uv run ruff format --check .` (ruff respects .gitignore by default).

### IN-04: Third-party action pinned to mutable tag instead of commit SHA

**File:** `.github/workflows/ci.yml:16`
**Issue:** `astral-sh/setup-uv@v8.2.0` is a tag reference, which the publisher can move or which can be replaced if the repo is compromised; `actions/checkout@v4` is a floating major tag. SHA-pinning is the supply-chain hardening standard for non-GitHub-owned actions especially.
**Fix:** Pin to the full commit SHA, e.g. `astral-sh/setup-uv@<40-char-sha> # v8.2.0`.

---

_Reviewed: 2026-06-11T21:22:07Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
