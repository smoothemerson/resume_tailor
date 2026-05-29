---
phase: 03-cli-wiring
fixed_at: 2026-05-29T00:00:00Z
fix_scope: critical_warning
findings_in_scope: 7
fixed: 7
skipped: 0
iteration: 1
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed:** 2026-05-29
**Scope:** Critical + Warning
**Findings in scope:** 7 (3 Critical, 4 Warning)
**Fixed:** 7
**Skipped:** 0

## Fixes Applied

### CR-01: `resume_reader` now raises instead of calling `sys.exit`

**Commit:** e7a431c + b8e76fd

`src/resume_reader.py` was changed to raise `FileNotFoundError` instead of calling `sys.exit(1)`. The `log_manager` and `sys` imports were removed. `src/cli.py` was updated to include `FileNotFoundError` in the `except` clause, ensuring the error is caught and formatted uniformly with a clean exit-1 message.

---

### CR-02: Wheel include list now contains all required modules

**Commit:** eb20ba5

`pyproject.toml` was updated to add `src/llm_client.py` and `src/log_manager.py` to the explicit wheel `include` list. Both were missing, causing `ModuleNotFoundError` on any installed run. The explicit list is required because hatchling cannot auto-discover the flat `src/` layout without a package subdirectory.

---

### CR-03: Wheel layout fragility resolved with complete explicit include

**Commit:** eb20ba5

The fragile interaction between `sources` rewriting and the explicit `include` list is resolved by using a complete and authoritative include list of all 6 source files. All files are explicitly enumerated, making the build configuration unambiguous across hatchling versions.

---

### WR-01: `OSError` added to `cli.py` error handler

**Commit:** b8e76fd

`OSError` (covers `PermissionError`, disk-full, read-only filesystem) added to the `except` clause in `src/cli.py:44`. Filesystem failures from `write_resume` now produce a clean `Error: …` message to stderr and exit code 1 instead of an unhandled traceback.

---

### WR-02: `--model`, `--resume`, `--output-dir` flags implemented

**Commit:** b8e76fd

`src/cli.py` now declares all three flags via `add_argument`, captures the `parse_args()` result, and passes the values through: `resume_path = args.resume or BASE_RESUME_PATH`, `output_dir = args.output_dir or OUTPUT_DIR`, and `model=args.model` forwarded to `generate_tailored_resume`. The dead argparse call is eliminated.

---

### WR-03: Dev dependencies consolidated into `[dependency-groups]`

**Commit:** ab90519

`ruff` and `mypy` moved from `[project.optional-dependencies]` into `[dependency-groups]` alongside `pytest`. The `[project.optional-dependencies]` section was removed. `uv sync --group dev` now installs the complete dev environment.

---

### WR-04: `log_manager` removed from `llm_client.py`

**Commit:** 24a5e46

`from log_manager import logger` import removed from `src/llm_client.py`. Redundant `logger.error(...)` calls (before raise statements) dropped. Progress `logger.info(...)` noise to stderr removed. An optional `model` parameter added to `generate_tailored_resume` so the `--model` CLI flag can override config. All error context is preserved in the raised exceptions.

---

## Remaining Issues

None — all 7 in-scope findings resolved.

_Fixed: 2026-05-29_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
