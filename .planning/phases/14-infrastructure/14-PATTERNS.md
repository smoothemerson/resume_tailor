# Phase 14: Infrastructure - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 6 new/modified files
**Analogs found:** 5 / 6 (`.github/workflows/ci.yml` has no codebase analog — use RESEARCH.md pattern directly)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/jd_analyzer_test.py` | test | transform (pure string in/dict out) | `src/llm_client_test.py` + `tests/unit/test_jd_analyzer.py` | role-match (same project, same marker convention) |
| `src/resume_reader_test.py` | test | file-I/O | `tests/unit/test_resume_reader.py` | exact (identical cases, src/ placement only difference) |
| `src/resume_writer_test.py` | test | file-I/O | `tests/unit/test_resume_writer.py` | exact (identical cases, src/ placement only difference) |
| `.github/workflows/ci.yml` | config (CI) | request-response (GitHub Actions) | none | no analog |
| `pyproject.toml` (update) | config (build) | batch | `pyproject.toml` existing include list | exact (add two lines to existing pattern) |
| `.gitignore` (replace) | config (vcs) | — | existing `.gitignore` (5 lines) | supersede (replace entirely) |

## Pattern Assignments

### `src/jd_analyzer_test.py` (test, transform)

**Primary analog:** `tests/unit/test_jd_analyzer.py` (for `@pytest.mark.unit` + import style)
**Secondary analog:** `src/llm_client_test.py` (for `*_test.py` naming and pytest-function style without `unittest.TestCase`)

**Key distinction:** `llm_client_test.py` does NOT use `@pytest.mark.unit` (lines 9, 13, 19, 24, 29…) — it uses bare `def test_*`. The `tests/unit/` files DO use `@pytest.mark.unit`. Since `--strict-markers` is enforced and all new tests must be tagged, copy the marker pattern from `tests/unit/test_jd_analyzer.py`, but use the pytest-function style (no `unittest.TestCase`) from `src/llm_client_test.py`.

**Imports pattern** (`tests/unit/test_jd_analyzer.py` lines 1-5):
```python
import pytest
import requests
from unittest.mock import MagicMock, patch

from jd_analyzer import analyze_job_description
```

For `jd_analyzer_test.py`, adapt to import the private function directly:
```python
import pytest
from jd_analyzer import _parse_analysis_response
```

**Core test pattern** (`tests/unit/test_jd_analyzer.py` lines 8-22 — `@pytest.mark.unit` + plain function style):
```python
@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_dict_with_three_keys(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": '{"technologies": ["Python"], "requirements": ["5 years"], "emphasis_areas": ["ML"]}'},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert isinstance(result, dict)
```

For `jd_analyzer_test.py`, no mocking is needed — the function is pure. Pattern simplifies to:
```python
@pytest.mark.unit
def test_parse_valid_json_returns_dict():
    content = '{"technologies": ["Python"], "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'
    result = _parse_analysis_response(content)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"technologies", "requirements", "emphasis_areas"}
```

**All 6 required test cases** (derived from `src/jd_analyzer.py` `_parse_analysis_response` logic, lines 27-43):

The function: strips fences → `json.loads` → validates `dict` type → validates 3 required keys present → validates all 3 values are `list` → returns filtered dict. Each guard is a test case:

| Case | Input | Expected |
|---|---|---|
| valid JSON | `'{"technologies": ["Python"], "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'` | `dict` with 3 keys |
| missing key | `'{"technologies": ["Python"], "requirements": ["5 yrs"]}'` | `None` |
| non-list value | `'{"technologies": "Python", "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'` | `None` |
| fenced JSON | `` ```json\n{...valid...}\n``` `` | `dict` (not None) |
| non-JSON string | `"not json at all"` | `None` |
| empty string | `""` | `None` |

---

### `src/resume_reader_test.py` (test, file-I/O)

**Analog:** `tests/unit/test_resume_reader.py` — exact copy with same module import path (both resolve via `pythonpath = ["src"]` in pyproject.toml).

**Imports pattern** (`tests/unit/test_resume_reader.py` lines 1-3):
```python
import pytest

from resume_reader import read_resume
```

**Core test pattern with `tmp_path`** (`tests/unit/test_resume_reader.py` lines 6-16):
```python
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

`src/resume_reader_test.py` is a direct copy of this file (D-03: acceptable duplication). No modifications needed beyond the copy.

---

### `src/resume_writer_test.py` (test, file-I/O)

**Analog:** `tests/unit/test_resume_writer.py` — exact copy (D-03).

**Imports pattern** (`tests/unit/test_resume_writer.py` lines 1-6):
```python
import re
from pathlib import Path

import pytest

from resume_writer import write_resume
```

**Core test pattern** (`tests/unit/test_resume_writer.py` lines 9-33):
```python
@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    assert not output_dir.exists()
    write_resume("content", output_dir)
    assert output_dir.exists()


@pytest.mark.unit
def test_write_resume_returns_path(tmp_path):
    result = write_resume("content", tmp_path / "out")
    assert isinstance(result, Path)


@pytest.mark.unit
def test_write_resume_filename_matches_timestamp_pattern(tmp_path):
    result = write_resume("content", tmp_path / "out2")
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)


@pytest.mark.unit
def test_write_resume_content_equals_input_string(tmp_path):
    content = "\\documentclass{article}\n\\end{document}"
    result = write_resume(content, tmp_path / "out3")
    assert result.read_text(encoding="utf-8") == content
```

Note: RESEARCH.md TEST-16 specifies 3 cases; `tests/unit/test_resume_writer.py` has 4. Copy all 4 — the extra `test_write_resume_returns_path` is additive and harmless.

---

### `.github/workflows/ci.yml` (config, CI)

**Analog:** None — no existing workflow in the repo (`.github/` directory does not exist).

**Use RESEARCH.md Pattern 3 directly** (lines 186-221 of 14-RESEARCH.md):
```yaml
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

**Critical version note:** Use `astral-sh/setup-uv@v8.2.0` — NOT `@v4` (stale; Astral stopped publishing moving major-version tags at v8.0.0, March 2025).

---

### `pyproject.toml` (update — PKG-01)

**Analog:** The existing `[tool.hatch.build.targets.wheel]` include list in `pyproject.toml` lines 16-27.

**Current state** (`pyproject.toml` lines 16-27):
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",
    "src/guards.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

**Target state** — add two entries in alphabetical order:
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",
    "src/guards.py",
    "src/jd_analyzer.py",
    "src/keyword_matcher.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

**Path format rule:** Paths must use the `src/X.py` form (project-root-relative), not just `X.py`. This is the existing convention and is required because `sources = ["src"]` remaps module names but include paths remain root-relative.

---

### `.gitignore` (replace — REPO-01)

**Current state** (5 lines, no analog to copy from):
```
**/__pycache__
.venv
uv.lock
resumes/
.claude/settings.local.json
```

**Target state** — replace entirely (current content is superseded; the new file preserves all existing ignore patterns plus adds the comprehensive set from D-09):
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

**Note on existing entries:** `**/__pycache__` becomes `__pycache__/` (standard form). `.claude/settings.local.json` is superseded by `.claude/` directory glob. `resumes/` and `uv.lock` are preserved. No existing ignores are lost.

---

## Shared Patterns

### `@pytest.mark.unit` marker
**Source:** `tests/unit/test_resume_reader.py`, `tests/unit/test_resume_writer.py`, `tests/unit/test_jd_analyzer.py`, `src/cli_test.py`
**Apply to:** All three new `src/*_test.py` files — every test function
**Registration:** Already declared in `pyproject.toml` lines 39-43:
```toml
markers = [
    "unit: fast isolated tests, no external deps",
    "integration: requires Ollama running locally",
    "e2e: full CLI subprocess invocation",
]
addopts = "--strict-markers -ra --import-mode=importlib"
```
No `conftest.py` changes needed. `--strict-markers` means omitting the marker causes a collection error, not a silent skip.

### `tmp_path` fixture for file-I/O tests
**Source:** `tests/unit/test_resume_reader.py` lines 7-16, `tests/unit/test_resume_writer.py` lines 9-33
**Apply to:** `src/resume_reader_test.py`, `src/resume_writer_test.py`
**Pattern:** Pass `tmp_path` as a function argument; pytest injects an isolated `Path` object. No setup/teardown needed. Subdirectories can be created via `tmp_path / "subdir"`.

### Import resolution
**Source:** `pyproject.toml` line 38: `pythonpath = ["src"]`
**Apply to:** All three new `src/*_test.py` files
**Pattern:** Import modules by bare name — `from jd_analyzer import _parse_analysis_response`, not `from src.jd_analyzer import ...`. The `pythonpath = ["src"]` setting makes `src/` a root for imports in both `src/` and `tests/` test paths.

### pytest-function style (not `unittest.TestCase`)
**Source:** `src/cli_test.py`, `tests/unit/test_resume_reader.py`, `tests/unit/test_resume_writer.py`, `tests/unit/test_jd_analyzer.py`
**Apply to:** All three new `src/*_test.py` files
**Anti-pattern to avoid:** `src/guards_test.py` and `src/keyword_matcher_test.py` use `unittest.TestCase` — this is the legacy pattern. New files in this phase use plain `def test_*()` functions with `@pytest.mark.unit`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.github/workflows/ci.yml` | config | CI/CD | No existing GitHub Actions workflows in repo; `.github/` directory does not exist |

Use RESEARCH.md Pattern 3 (lines 186-221) as the authoritative template for this file.

---

## Metadata

**Analog search scope:** `src/`, `tests/unit/`, `tests/e2e/`, `tests/integration/`, project root
**Files scanned:** 15 source files, 7 test files, `pyproject.toml`, `.gitignore`
**Pattern extraction date:** 2026-06-09
