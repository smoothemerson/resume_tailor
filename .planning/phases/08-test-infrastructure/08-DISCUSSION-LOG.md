# Phase 8: Test Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 8-Test Infrastructure
**Areas discussed:** sys.path cleanup, tests/ package layout, Ollama fixture design

---

## sys.path cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Remove them | pythonpath=["src"] makes the hacks redundant; removing keeps files clean and avoids confusing future test authors | ✓ |
| Leave them untouched | Requirements say "left in place" — interpret as zero internal changes; hacks are harmless | |

**User's choice:** Remove them (Recommended)
**Notes:** Phase 8 will remove the `sys.path.insert(0, str(Path(__file__).parent))` lines from both `src/cli_test.py` and `src/llm_client_test.py`. The files themselves stay in `src/`.

---

## tests/ package layout

| Option | Description | Selected |
|--------|-------------|----------|
| No `__init__.py` (rootdir-relative) | pytest's recommended approach for new projects; avoids module name collisions across subdirs | ✓ |
| `__init__.py` in each subdir | Package mode; makes subdirs importable; useful if tests need to import from each other | |

**User's choice:** No `__init__.py` (Recommended)
**Notes:** `tests/unit/`, `tests/integration/`, `tests/e2e/` will be bare empty directories in Phase 8. Rootdir-relative test discovery.

---

## Ollama fixture design

| Option | Description | Selected |
|--------|-------------|----------|
| Import from `config.OLLAMA_BASE_URL` | Single source of truth; follows existing production code pattern; auto-follows if URL changes | ✓ |
| Hardcode `http://localhost:11434` | Simpler; no import dependency; creates duplication | |

**User's choice:** Import from config.OLLAMA_BASE_URL (Recommended)
**Notes:** During codebase scout, confirmed the config constant is `OLLAMA_BASE_URL` (not `OLLAMA_URL`). The conftest will use `from config import OLLAMA_BASE_URL`.

---

## Claude's Discretion

None — all three areas had clear user decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
