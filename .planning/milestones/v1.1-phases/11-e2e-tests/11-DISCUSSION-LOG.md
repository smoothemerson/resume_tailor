# Phase 11: E2E Tests - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 11-E2E Tests
**Areas discussed:** Subprocess invocation, Resume fixture for TEST-11

---

## Subprocess Invocation

| Option | Description | Selected |
|--------|-------------|----------|
| sys.executable + src/cli.py | Works without install, always uses the same Python interpreter as pytest. Path via Path(__file__).parents[2]. | ✓ |
| python -m cli | Requires cli.py importable as module; pythonpath=['src'] supports it, but no real benefit here. | |
| Installed resume-tailor command | Tests the installed entry point. Realistic for CI but fragile without uv tool install. | |

**User's choice:** sys.executable + src/cli.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| Path(__file__).parents[2] / 'src/cli.py' | Absolute path derived from test file — robust regardless of pytest cwd. | ✓ |
| Path('src/cli.py') | Relative path — works when cwd is project root but fragile otherwise. | |

**User's choice:** Path(__file__).parents[2] / 'src/cli.py'

---

| Option | Description | Selected |
|--------|-------------|----------|
| input='END\n', text=True | Clean, readable, no bytes encoding needed. capture_output=True, text=True. | ✓ |
| input=b'END\n' | Bytes mode — more explicit but requires manual decode of stdout/stderr. | |

**User's choice:** input='END\n', text=True

---

## Resume Fixture for TEST-11

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal fixture written to tmp_path | Write MINIMAL_RESUME to tmp_path, pass --resume. Isolated, fast inference, no coupling to real resume. | ✓ |
| Real resumes/english.tex | No --resume flag needed (config default). But slower inference and couples test to actual file. | |

**User's choice:** Minimal fixture written to tmp_path

---

| Option | Description | Selected |
|--------|-------------|----------|
| No — filename pattern + stdout message only | TEST-11 requirements: exit 0, filename matches timestamp pattern, stdout contains success message. LaTeX structure covered by integration test. | ✓ |
| Yes — also check file content | Belt-and-suspenders: confirms full pipeline produced valid LaTeX. Slight duplication with integration test. | |

**User's choice:** No — filename pattern + stdout message only (no content assertion)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — exact string | Assert "Error: Job description cannot be empty." in stderr. String is stable (constant in cli.py). Documents user-visible error. | ✓ |
| Partial match only | Assert stderr non-empty or "Error:" appears. Looser but survives phrasing changes. | |

**User's choice:** Yes — exact string assertion for TEST-10 stderr

---

| Option | Description | Selected |
|--------|-------------|----------|
| Define its own in test_cli.py | Module-level MINIMAL_RESUME constant — same pattern as Phase 10. Self-contained file. | ✓ |
| Import from integration tests | Reuse constant from tests/integration/test_llm_client.py. Creates coupling between test files. | |

**User's choice:** Define its own module-level constant in tests/e2e/test_cli.py

---

## Claude's Discretion

None — all decisions made by user.

## Deferred Ideas

None — discussion stayed within phase scope.
