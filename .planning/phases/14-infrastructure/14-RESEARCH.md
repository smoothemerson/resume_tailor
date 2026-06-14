# Phase 14: Infrastructure - Research

**Researched:** 2026-06-09
**Domain:** Python packaging (hatchling), GitHub Actions CI, pytest unit testing, git repository hygiene
**Confidence:** HIGH

## Summary

Phase 14 closes infrastructure debt across four distinct areas with no new features. Each area is well-understood and carries no significant technical risk. All decisions were locked in CONTEXT.md during the discuss phase, so this research validates and operationalizes those decisions rather than exploring alternatives.

The packaging fix is a one-line-per-module addition to `pyproject.toml`. The CI workflow is a ~25-line YAML file using an Astral-maintained GitHub Action. The test files are pure string-in/string-out functions with no mocking. The `.claude/` removal is a standard `git rm --cached` operation followed by a `.gitignore` update.

One important correction to the context: `astral-sh/setup-uv@v4` referenced in CONTEXT.md D-05 is stale. The action has reached v8.2.0 and no longer publishes moving major-version tags (e.g., `@v4`, `@v8`) for supply-chain security. The planner must use either the full SHA pin or a full semver tag such as `@v8.2.0`. [VERIFIED: github.com/astral-sh/setup-uv/releases]

**Primary recommendation:** Execute the four sub-areas as sequential waves in a single plan: (1) packaging fix, (2) test files, (3) CI workflow, (4) repo hygiene. All are independent and low-risk.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Add `src/jd_analyzer_test.py`, `src/resume_reader_test.py`, `src/resume_writer_test.py` as REQUIREMENTS.md specifies — colocated with source, following the existing pattern of `llm_client_test.py`, `guards_test.py`, etc.
- **D-02:** `src/jd_analyzer_test.py` tests `_parse_analysis_response()` directly (no mocking — pure string in/out). This is additive to the existing `tests/unit/test_jd_analyzer.py` which tests `analyze_job_description()` with mocked HTTP. Both coexist.
- **D-03:** `src/resume_reader_test.py` and `src/resume_writer_test.py` coexist with the identical tests already in `tests/unit/`. Acceptable duplication — files are tiny and the `src/` pattern is already established.
- **D-04:** All new tests tagged `@pytest.mark.unit`. Use `tmp_path` fixture for file-system tests.
- **D-05:** Use `astral-sh/setup-uv@v4` action to install uv — official Astral action, handles binary caching automatically. *(See note in Summary: this tag is stale; use `@v8.2.0` or pinned SHA instead.)*
- **D-06:** Include both `ruff check src/` and `ruff format --check src/` in the CI lint step.
- **D-07:** Trigger on push and pull_request to main. Runner: ubuntu-latest, Python 3.13.
- **D-08:** Use `uv sync` to install dependencies.
- **D-09:** Create a standard Python `.gitignore` — not just `.claude/`. Include: `.claude/`, `__pycache__/`, `*.py[cod]`, `.venv/`, `dist/`, `*.egg-info/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`.
- **D-10:** Remove `.claude/` from git tracking via `git rm -r --cached .claude/` then commit. Local directory is preserved.

### Claude's Discretion

- CI job name, step names, timeout values — standard conventions are fine.
- `uv sync --dev` vs `uv sync` — use `uv sync` (includes dev dependencies by default from `[dependency-groups]`).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | `jd_analyzer.py` and `keyword_matcher.py` added to `[tool.hatch.build.targets.wheel]` include list in `pyproject.toml` | Two paths confirmed missing from current include list: `src/jd_analyzer.py` and `src/keyword_matcher.py`. Addition follows the existing `src/X.py` pattern already in the list. |
| CI-01 | `.github/workflows/ci.yml` triggers on push and pull_request to main, uses ubuntu-latest + Python 3.13, installs deps with uv, runs `ruff check src/` and `pytest -m unit` | `.github/` directory does not exist yet. CI YAML structure verified against official Astral docs. `astral-sh/setup-uv@v8.2.0` is the correct current action reference. |
| TEST-14 | `src/jd_analyzer_test.py` covers `_parse_analysis_response`: valid JSON, missing key, non-list value, fenced JSON, non-JSON string, empty string | `_parse_analysis_response` is a pure function (no HTTP, no side effects). All 6 cases are string-in/`dict|None`-out. Existing `tests/unit/test_jd_analyzer.py` does NOT cover this function — it tests `analyze_job_description()` via HTTP mock. |
| TEST-15 | `src/resume_reader_test.py` covers `read_resume`: existing file returns content, missing file raises `FileNotFoundError` | `read_resume` is 4 lines. Identical test logic already exists in `tests/unit/test_resume_reader.py` — the `src/` file is additive duplication by design (D-03). Uses `tmp_path` fixture. |
| TEST-16 | `src/resume_writer_test.py` covers `write_resume`: file created in given dir, filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex`, file content matches input | Identical test logic in `tests/unit/test_resume_writer.py` — additive duplication. The timestamp pattern test uses `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)`. Uses `tmp_path`. |
| REPO-01 | `.claude/` added to `.gitignore` and untracked from git history | `.claude/` currently has 429 tracked files. `.gitignore` exists but only has `.claude/settings.local.json` entry. `git rm -r --cached .claude/` removes index entries without deleting local files. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Packaging fix (pyproject.toml) | Build configuration | — | Pure metadata; no runtime tier |
| CI workflow | CI/CD infrastructure | — | GitHub Actions YAML; no app tier |
| Unit test files | Test layer (src-colocated) | — | Tests are infrastructure, not application logic |
| Repository hygiene (.gitignore, git rm) | Version control | — | Git index operation; no app tier |

## Standard Stack

### Core (no new packages — all existing)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | `>=9.0.3` (pinned in pyproject.toml) | Test runner, `tmp_path` fixture, `@pytest.mark.unit` | Already in `[dependency-groups].dev`; `--strict-markers` and `testpaths` configured |
| hatchling | build system (pyproject.toml `[build-system]`) | Wheel builder; `[tool.hatch.build.targets.wheel]` controls include list | Already the project build backend |
| ruff | (unpinned in dev deps) | Linting + format-check for CI step | Already in dev deps |
| astral-sh/setup-uv | GitHub Action `@v8.2.0` | Install uv + Python in CI runner | Official Astral action; handles binary cache |
| actions/checkout | `@v4` | Checkout repository in CI | GitHub standard; v4 is current LTS |

### No New Packages

This phase installs zero new runtime or dev dependencies. The Package Legitimacy Audit section covers only the GitHub Actions references (not pip packages).

## Package Legitimacy Audit

This phase installs **no new pip/PyPI packages**. GitHub Actions references are not registry packages; they are git-ref-pinned actions.

| Action Reference | Source | Maintained By | Disposition |
|-----------------|--------|---------------|-------------|
| `astral-sh/setup-uv@v8.2.0` | github.com/astral-sh/setup-uv | Astral (authors of uv) | Approved [VERIFIED: github.com/astral-sh/setup-uv/releases] |
| `actions/checkout@v4` | github.com/actions/checkout | GitHub | Approved [VERIFIED: standard GitHub Actions] |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
**slopcheck status:** unavailable in this environment (pip not installed); no new pip packages to audit in this phase.

## Architecture Patterns

### System Architecture Diagram

```
pyproject.toml
  └─ [tool.hatch.build.targets.wheel].include
       ├─ src/jd_analyzer.py   <── ADD (PKG-01)
       └─ src/keyword_matcher.py <── ADD (PKG-01)

src/ (colocated test pattern)
  ├─ jd_analyzer.py
  │    └─ _parse_analysis_response(str) -> dict | None
  │         └─ jd_analyzer_test.py  <── NEW (TEST-14)
  ├─ resume_reader.py
  │    └─ read_resume(Path) -> str
  │         └─ resume_reader_test.py <── NEW (TEST-15)
  └─ resume_writer.py
       └─ write_resume(str, Path) -> Path
            └─ resume_writer_test.py <── NEW (TEST-16)

.github/workflows/ci.yml   <── NEW (CI-01)
  on: push/PR to main
  jobs:
    test:
      runs-on: ubuntu-latest
      steps: checkout → setup-uv (Python 3.13) → uv sync → ruff check → ruff format --check → pytest -m unit

.gitignore   <── UPDATE (REPO-01)
  + .claude/
  + standard Python ignores

git index   <── MUTATE (REPO-01)
  git rm -r --cached .claude/  (429 files removed from tracking)
```

### Recommended Project Structure (no changes to src/ layout)

```
.github/
└── workflows/
    └── ci.yml            # New — CI-01
src/
├── jd_analyzer.py
├── jd_analyzer_test.py   # New — TEST-14
├── resume_reader.py
├── resume_reader_test.py # New — TEST-15
├── resume_writer.py
└── resume_writer_test.py # New — TEST-16
.gitignore                # Update — REPO-01
pyproject.toml            # Update — PKG-01
```

### Pattern 1: src-colocated `*_test.py` style

**What:** Test files live in `src/` next to the module they test, named `<module>_test.py`. No test class — pytest-style functions only, each decorated `@pytest.mark.unit`.

**When to use:** Any new unit test for a `src/` module (established project convention, see `llm_client_test.py`).

**Example (from existing `src/llm_client_test.py`):**
```python
# Source: src/llm_client_test.py (existing file in repo)
import pytest

@pytest.mark.unit
def test_strip_latex_fence():
    result = _strip_fences("```latex\n\\documentclass{article}\n```")
    assert result == "\\documentclass{article}"
```

Note: `guards_test.py` uses `unittest.TestCase` — this is the legacy pattern. New files in this phase should use the pytest-function style from `llm_client_test.py`, not the `unittest.TestCase` style from `guards_test.py`. [ASSUMED — CONTEXT.md does not specify; the newer `llm_client_test.py` pattern is cleaner and consistent with `@pytest.mark.unit`]

### Pattern 2: `tmp_path` for file-system tests

**What:** pytest's built-in `tmp_path` fixture provides an isolated temporary directory per test. No manual cleanup needed.

**When to use:** Any test that creates or reads files (`resume_reader_test.py`, `resume_writer_test.py`).

**Example (from existing `tests/unit/test_resume_writer.py`):**
```python
# Source: tests/unit/test_resume_writer.py (existing file in repo)
@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    assert not output_dir.exists()
    write_resume("content", output_dir)
    assert output_dir.exists()
```

### Pattern 3: GitHub Actions CI with uv

**What:** Single-job workflow using `astral-sh/setup-uv` to install uv + Python, then `uv sync` to install project + dev deps, then run linters and tests via `uv run`.

**When to use:** Standard for all uv-based Python projects on GitHub.

**Example (from official Astral docs, adapted for this project):**
```yaml
# Source: docs.astral.sh/uv/guides/integration/github/ (verified 2026-06-09)
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv and Python 3.13
        uses: astral-sh/setup-uv@v8.2.0
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: |
          uv run ruff check src/
          uv run ruff format --check src/

      - name: Test
        run: uv run pytest -m unit
```

**Critical version note:** The context document references `astral-sh/setup-uv@v4`. This is stale — the action no longer publishes moving major-version tags as of v8.0.0 (March 2025). Using `@v4` will resolve to nothing or an old release. Use `@v8.2.0` (latest as of June 2026). [VERIFIED: github.com/astral-sh/setup-uv/releases]

### Pattern 4: git rm --cached for untracking files

**What:** `git rm -r --cached <path>` removes files from the git index (stops tracking) without deleting them from disk. Combined with a `.gitignore` entry, the files become permanently untracked.

**When to use:** When a directory was accidentally committed and must be removed from version control without destroying local files.

**Command sequence:**
```bash
# Step 1: Add to .gitignore FIRST (prevents re-add)
# Step 2: Remove from index
git rm -r --cached .claude/
# Step 3: Commit the removal
git commit -m "chore: untrack .claude/ from version control"
```

**Pitfall:** If `.gitignore` is not written before `git rm --cached`, a subsequent `git add .` can re-add the files. Always write `.gitignore` first.

### Anti-Patterns to Avoid

- **Using `astral-sh/setup-uv@v4`:** This tag is defunct as of March 2025. Always use full semver `@v8.2.0` or a pinned SHA.
- **Using `@pytest.mark.unit` without registration:** The project has `--strict-markers` set. The `unit` marker is already registered in `pyproject.toml` — no additional `conftest.py` entry needed.
- **Naming test files `test_*.py` in `src/`:** The `src/` convention uses `*_test.py` (pytest's `--import-mode=importlib` handles both, but `*_test.py` is the established project pattern here).
- **Using `git rm -r --cached` without `.gitignore` entry:** Files will be re-tracked on the next `git add .`.
- **Committing `.claude/` removal and `.gitignore` update in separate commits without care about ordering:** If `.gitignore` isn't in the commit that removes tracking, CI could fail on the next push before `.gitignore` is merged.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporary file isolation in tests | Custom temp dir teardown | `tmp_path` (pytest built-in) | Thread-safe, auto-cleaned, already used in project |
| Wheel include list | Custom build script | `[tool.hatch.build.targets.wheel].include` in pyproject.toml | hatchling native; one line per module |
| CI Python setup | Custom install scripts | `astral-sh/setup-uv` with `python-version` input | Handles binary caching, PATH config, version resolution |

**Key insight:** Every problem in this phase has a one-liner solution. If any task requires more than ~10 lines to accomplish the core change, something is wrong.

## Common Pitfalls

### Pitfall 1: setup-uv major tag staleness

**What goes wrong:** `astral-sh/setup-uv@v4` fails to resolve or resolves to a very old release. CI job errors with "unable to find action" or installs ancient uv.

**Why it happens:** Astral stopped publishing moving major tags (`@v4`, `@v5`, etc.) at v8.0.0 for supply-chain security. Tags v1–v7 exist but are frozen; `@v8` was never published.

**How to avoid:** Use `@v8.2.0` (full semver) as the action reference.

**Warning signs:** CI step "Install uv" fails immediately or reports uv version older than 0.5.x.

### Pitfall 2: .gitignore written after git rm --cached

**What goes wrong:** `.claude/` is removed from the index via `git rm --cached`, but `.gitignore` is only committed later. Between those two commits, a `git add` or automated tool re-adds the files.

**Why it happens:** Order of operations error.

**How to avoid:** Always write and commit `.gitignore` in the same commit as (or before) `git rm --cached .claude/`. In this phase: update `.gitignore` first, then `git rm --cached`, then commit both together.

**Warning signs:** `git status` shows `.claude/` files as untracked after the removal commit.

### Pitfall 3: Missing `@pytest.mark.unit` on new test functions

**What goes wrong:** Tests run without `-m unit` but are silently skipped (or error with `PytestUnknownMarkWarning`) when `--strict-markers` is active.

**Why it happens:** `--strict-markers` is set in `pyproject.toml`. Any test not decorated with a registered marker will fail collection under strict mode.

**How to avoid:** Every test function in the three new `src/*_test.py` files must have `@pytest.mark.unit`.

**Warning signs:** `pytest --collect-only` shows warnings about unknown markers; tests not appearing in `-m unit` run.

### Pitfall 4: PKG-01 path format in include list

**What goes wrong:** Adding `jd_analyzer.py` (without `src/` prefix) fails to include the file in the wheel.

**Why it happens:** `[tool.hatch.build.targets.wheel]` include paths are relative to the project root when `sources = ["src"]` is set — the existing entries use `src/X.py` form, not just `X.py`.

**How to avoid:** Match the existing pattern exactly: `"src/jd_analyzer.py"` and `"src/keyword_matcher.py"`.

**Warning signs:** `uv build` succeeds but `unzip -l dist/*.whl | grep jd_analyzer` shows no match.

### Pitfall 5: Existing `.gitignore` has partial .claude/ entry

**What goes wrong:** Current `.gitignore` already has `.claude/settings.local.json`. Adding `.claude/` as a directory glob is additive and correct, but the planner must not accidentally overwrite the existing file — it must append/merge.

**Why it happens:** Overwriting `.gitignore` with `Write` tool loses the existing `**/__pycache__`, `.venv`, `uv.lock`, `resumes/` entries.

**How to avoid:** Read the existing `.gitignore` before writing. Current content:
```
**/__pycache__
.venv
uv.lock
resumes/
.claude/settings.local.json
```
The new standard Python `.gitignore` (D-09) supersedes this. Replace entirely with the comprehensive set, which includes `.claude/` at the directory level (making the individual `.claude/settings.local.json` entry redundant but harmless to remove).

## Code Examples

### TEST-14: jd_analyzer_test.py pattern

```python
# Source: derived from _parse_analysis_response() in src/jd_analyzer.py (read 2026-06-09)
import pytest
from jd_analyzer import _parse_analysis_response


@pytest.mark.unit
def test_parse_valid_json_returns_dict():
    content = '{"technologies": ["Python"], "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'
    result = _parse_analysis_response(content)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"technologies", "requirements", "emphasis_areas"}


@pytest.mark.unit
def test_parse_missing_key_returns_none():
    content = '{"technologies": ["Python"], "requirements": ["5 yrs"]}'
    assert _parse_analysis_response(content) is None


@pytest.mark.unit
def test_parse_non_list_value_returns_none():
    content = '{"technologies": "Python", "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'
    assert _parse_analysis_response(content) is None


@pytest.mark.unit
def test_parse_fenced_json_returns_dict():
    content = '```json\n{"technologies": ["Go"], "requirements": ["3 yrs"], "emphasis_areas": ["backend"]}\n```'
    result = _parse_analysis_response(content)
    assert result is not None


@pytest.mark.unit
def test_parse_non_json_string_returns_none():
    assert _parse_analysis_response("not json at all") is None


@pytest.mark.unit
def test_parse_empty_string_returns_none():
    assert _parse_analysis_response("") is None
```

### TEST-15: resume_reader_test.py pattern

```python
# Source: mirrors tests/unit/test_resume_reader.py (read 2026-06-09)
import pytest
from resume_reader import read_resume


@pytest.mark.unit
def test_read_resume_returns_file_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("\\documentclass{article}", encoding="utf-8")
    assert read_resume(resume_file) == "\\documentclass{article}"


@pytest.mark.unit
def test_read_resume_missing_file_raises_file_not_found_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_resume(tmp_path / "nonexistent.tex")
```

### TEST-16: resume_writer_test.py pattern

```python
# Source: mirrors tests/unit/test_resume_writer.py (read 2026-06-09)
import re
from pathlib import Path
import pytest
from resume_writer import write_resume


@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    assert not output_dir.exists()
    write_resume("content", output_dir)
    assert output_dir.exists()


@pytest.mark.unit
def test_write_resume_filename_matches_timestamp_pattern(tmp_path):
    result = write_resume("content", tmp_path / "out")
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)


@pytest.mark.unit
def test_write_resume_content_equals_input_string(tmp_path):
    content = "\\documentclass{article}\n\\end{document}"
    result = write_resume(content, tmp_path / "out2")
    assert result.read_text(encoding="utf-8") == content
```

### PKG-01: pyproject.toml include list update

```toml
# Source: pyproject.toml (read 2026-06-09) — add two lines
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",
    "src/guards.py",
    "src/jd_analyzer.py",       # ADD
    "src/keyword_matcher.py",   # ADD
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

### REPO-01: .gitignore replacement content

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/

# Virtual environments
.venv/

# Tools
.mypy_cache/
.ruff_cache/
.pytest_cache/

# Project-specific
resumes/
uv.lock

# Claude Code workspace
.claude/
```

### REPO-01: git untracking command

```bash
# Run from project root after .gitignore is written and staged
git rm -r --cached .claude/
# Then commit .gitignore update and the removal together
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `astral-sh/setup-uv@v4` (moving tag) | `astral-sh/setup-uv@v8.2.0` (full semver) | March 2025 (v8.0.0) | Moving tags no longer published; must pin to full version |
| `uv sync --dev` (explicit dev flag) | `uv sync` (includes dev by default via `[dependency-groups]`) | uv >=0.4 | `[dependency-groups]` in PEP 735 style; `uv sync` installs all groups |

**Deprecated/outdated:**
- `astral-sh/setup-uv@v4` through `@v7`: These tags exist in the registry but are frozen old releases. v8.0.0 breaking change removed the moving-tag pattern entirely.
- `requirements.txt` + `setup.py`: Replaced by `pyproject.toml` + `uv.lock`. Not applicable here (already using pyproject.toml).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | New test files should use pytest-function style (not `unittest.TestCase` style from `guards_test.py`) | Architecture Patterns / Pattern 1 | Low — both styles pass pytest; style choice only affects readability |
| A2 | `actions/checkout@v4` is the current LTS version | Standard Stack | Low — v3 also works; `@v4` is the safe current choice |
| A3 | `uv sync` without `--locked` is acceptable for CI (vs. `uv sync --locked`) | CI YAML example | Medium — `--locked` is safer for reproducibility; omitting it allows lockfile drift. Consider adding `--locked` for CI. |

## Open Questions

1. **`uv sync` vs `uv sync --locked` in CI**
   - What we know: `uv sync` installs from lockfile when present; `--locked` adds a strict assertion that the lockfile is up to date with `pyproject.toml`
   - What's unclear: CONTEXT.md D-08 says "Use `uv sync`" without `--locked`. The official Astral docs recommend `uv sync --locked --all-extras --dev` for CI.
   - Recommendation: Use `uv sync --locked` in the CI workflow to prevent lockfile drift from silently passing CI. The project has `uv.lock` in `.gitignore`, which means the lock file may or may not be committed — if `uv.lock` is gitignored, `--locked` will fail. Planner should verify whether `uv.lock` is committed before adding `--locked`.

2. **`uv.lock` in `.gitignore`**
   - What we know: Current `.gitignore` lists `uv.lock`, meaning the lockfile is intentionally not committed.
   - What's unclear: If `uv.lock` is gitignored, CI `uv sync` will generate a fresh lockfile on each run (acceptable but not reproducible).
   - Recommendation: For a portfolio project, this is acceptable. Use `uv sync` without `--locked`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Test execution | ✓ | 3.11.2 (system) | — |
| uv | Dependency management | ✗ | — | `pip install` (slower, not preferred) |
| git | REPO-01 (`git rm --cached`) | ✓ (implied by repo existence) | — | — |
| pytest | Test runner | ✗ (no pip/venv active) | — | Install via `uv sync` in project venv |
| ruff | Lint/format check | ✗ (not system-installed) | — | Install via `uv sync` in project venv |
| GitHub Actions runner | CI-01 | N/A (remote) | ubuntu-latest | — |

**Missing dependencies with no fallback:**
- uv: Required for `uv sync`, `uv run`, `uv build`. Must be installed before project venv is usable. CI handles this via `astral-sh/setup-uv`. Local dev requires manual install from `https://docs.astral.sh/uv/getting-started/installation/`.

**Missing dependencies with fallback:**
- pytest, ruff: Not system-installed but available via `uv sync` once uv is present. Standard project workflow.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=9.0.3` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -m unit` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | `jd_analyzer.py` and `keyword_matcher.py` in wheel | smoke | `uv build && unzip -l dist/*.whl \| grep -E "jd_analyzer\|keyword_matcher"` | N/A (build check) |
| CI-01 | CI YAML is valid and triggers correctly | manual | `yamllint .github/workflows/ci.yml` (optional) | ❌ Wave 0 |
| TEST-14 | `_parse_analysis_response` — 6 cases | unit | `uv run pytest src/jd_analyzer_test.py -m unit` | ❌ Wave 0 |
| TEST-15 | `read_resume` — 2 cases | unit | `uv run pytest src/resume_reader_test.py -m unit` | ❌ Wave 0 |
| TEST-16 | `write_resume` — 3 cases | unit | `uv run pytest src/resume_writer_test.py -m unit` | ❌ Wave 0 |
| REPO-01 | `.claude/` untracked, `.gitignore` updated | manual | `git ls-files .claude/` returns nothing | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest -m unit`
- **Per wave merge:** `uv run pytest -m unit`
- **Phase gate:** Full suite green (`uv run pytest`) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `src/jd_analyzer_test.py` — covers TEST-14 (6 unit tests for `_parse_analysis_response`)
- [ ] `src/resume_reader_test.py` — covers TEST-15 (2 unit tests for `read_resume`)
- [ ] `src/resume_writer_test.py` — covers TEST-16 (3 unit tests for `write_resume`)
- [ ] `.github/workflows/ci.yml` — covers CI-01
- [ ] Framework already installed: `pytest >=9.0.3` in `[dependency-groups].dev`; no new install needed beyond `uv sync`

## Security Domain

This phase introduces no authentication, session management, external HTTP calls, or user-supplied input processing. The only ASVS-relevant item is the CI workflow:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — |
| V6 Cryptography | no | — |
| CI secrets exposure | yes (tangential) | CI-01 spec: "no secrets" — workflow uses no secrets, no tokens, no env vars beyond what GitHub injects automatically |

The CI workflow must not reference `${{ secrets.* }}` variables (there are none to reference; the workflow only runs public tools with no external service calls). [VERIFIED: CI-01 requirement spec]

## Sources

### Primary (HIGH confidence)

- github.com/astral-sh/setup-uv/releases — verified v8.2.0 is latest stable, confirmed moving tags discontinued at v8.0.0
- docs.astral.sh/uv/guides/integration/github/ — verified `uv sync` syntax, `python-version` input, complete workflow pattern
- src/jd_analyzer.py (read directly) — verified `_parse_analysis_response` signature and behavior
- src/resume_reader.py, src/resume_writer.py (read directly) — verified function signatures
- pyproject.toml (read directly) — verified missing include entries, existing test config
- tests/unit/test_resume_reader.py, test_resume_writer.py, test_jd_analyzer.py (read directly) — verified test patterns and coverage gaps
- src/llm_client_test.py (read directly) — verified `@pytest.mark.unit` style reference

### Secondary (MEDIUM confidence)

- pypi.org/project/pytest/ — pytest 8.3.4 confirmed as latest stable; pyproject.toml pins `>=9.0.3` which suggests a pre-release or the search result was incomplete [ASSUMED — verify before CI runs]

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already in project; no new installs
- Architecture: HIGH — all four sub-areas are well-understood, small-scope changes
- Pitfalls: HIGH — setup-uv tag staleness verified via official releases page; git/pytest pitfalls are established knowledge
- CI YAML syntax: HIGH — verified against official Astral docs

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (CI action version — check for setup-uv updates before implementing if >30 days pass)
