---
phase: 14-infrastructure
plan: 01
subsystem: infra
tags: [packaging, ci, github-actions, uv, hatchling]
requires: []
provides:
  - "Wheel include list covering all 10 src modules (PKG-01)"
  - "GitHub Actions CI workflow with lint + unit tests on push/PR to main (CI-01)"
affects:
  - 14-03
tech-stack:
  added: [github-actions, astral-sh/setup-uv@v8.2.0]
  patterns: ["uv sync + uv run in CI", "full-semver action pinning"]
key-files:
  created:
    - .github/workflows/ci.yml
  modified:
    - pyproject.toml
decisions:
  - "Pinned astral-sh/setup-uv to full semver v8.2.0 — Astral stopped publishing moving major-version tags at v8.0.0 (March 2025), so @v4 from the context doc is stale"
  - "CI workflow contains zero secrets references — only public tool invocations (T-14-02 accepted)"
metrics:
  duration: "2m"
  completed: "2026-06-11"
---

# Phase 14 Plan 01: Packaging Fix and CI Workflow Summary

Wheel include list fixed to ship jd_analyzer.py and keyword_matcher.py, plus a secrets-free GitHub Actions CI workflow running ruff lint/format-check and pytest -m unit via uv on every push and PR to main.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Add jd_analyzer.py and keyword_matcher.py to wheel include list (PKG-01) | 8865703 | pyproject.toml |
| 2 | Create GitHub Actions CI workflow (CI-01, D-05 through D-08) | d5d7b89 | .github/workflows/ci.yml |

## What Was Built

- **pyproject.toml** — `[tool.hatch.build.targets.wheel]` include list expanded from 8 to 10 entries; `src/jd_analyzer.py` and `src/keyword_matcher.py` inserted in alphabetical position between `src/guards.py` and `src/llm_client.py`. No other section touched.
- **.github/workflows/ci.yml** — single `test` job on ubuntu-latest: actions/checkout@v4 → astral-sh/setup-uv@v8.2.0 with Python 3.13 → `uv sync` → `uv run ruff check src/` + `uv run ruff format --check src/` → `uv run pytest -m unit`. Triggers on push and pull_request to main. Zero `${{ secrets.* }}` references.

## Verification Results

- `grep "src/jd_analyzer.py" pyproject.toml` — entry present
- `grep "src/keyword_matcher.py" pyproject.toml` — entry present
- Include block contains exactly 10 `"src/` entries
- `grep "setup-uv@v8.2.0" .github/workflows/ci.yml` — pinned version confirmed
- `grep "secrets\." .github/workflows/ci.yml` — no matches (exit 1, pass)
- All lint/format/test step strings confirmed present; no tabs; no GitHub expressions

**Verification limitation:** the plan's YAML parse check (`python3 -c "import yaml; yaml.safe_load(...)"`) could not run — this environment has no PyYAML, no pip, no yq, and no js-yaml. The file is a line-for-line copy of the verified Pattern 3 template in 14-RESEARCH.md (sourced from official Astral docs), uses consistent 2-space indentation with no tabs, and all grep-based acceptance criteria pass. The CI run itself will be the definitive syntax validation on first push to main.

## Deviations from Plan

None - plan executed exactly as written. (The YAML parser absence is an environment limitation on a verification step, not a code deviation.)

## Known Stubs

None — both files are complete configuration artifacts with no placeholders.

## Threat Model Notes

- T-14-01 (mitigate): both actions pinned — astral-sh/setup-uv@v8.2.0 full semver, actions/checkout@v4
- T-14-02 (accept): zero secrets/tokens/credentials in workflow, verified by grep
- T-14-SC (mitigate): only Astral-official and GitHub-official actions used, per RESEARCH.md Package Legitimacy Audit

No new threat surface introduced beyond the plan's threat model.

## Self-Check: PASSED

- FOUND: pyproject.toml (modified, 10 include entries)
- FOUND: .github/workflows/ci.yml
- FOUND: commit 8865703
- FOUND: commit d5d7b89
