# Phase 10: Integration Tests - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 10-integration-tests
**Areas discussed:** Minimal resume fixture, TEST-08 scope, TEST-09 assertion depth

---

## Minimal resume fixture

| Option | Description | Selected |
|--------|-------------|----------|
| Bare-bones only | `\documentclass{article}\begin{document}\section{Summary}AI engineer with 3 years experience.\end{document}` — fastest inference, ~30 words | ✓ |
| Minimal but realistic | Summary + skills + one experience entry with bullet (~80 words). Exercises prompt section-targeting more faithfully. | |
| You decide | Claude picks based on simplicity, prioritizing inference speed. | |

**User's choice:** Bare-bones only

**Follow-up — fixture location:**

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in test file | Module-level constant in `tests/integration/test_llm_client.py`. Simple, self-contained. | ✓ |
| conftest.py pytest fixture | Shared via `tests/conftest.py`; reusable by Phase 11 but forward-looking scope creep. | |
| You decide | Claude picks based on simplicity. | |

**User's choice:** Inline in test file

---

## TEST-08 scope

| Option | Description | Selected |
|--------|-------------|----------|
| Call `_check_ollama_health()` | Tests our function's behavior against live Ollama — integration complement to Phase 9's mocked unit test. | ✓ |
| Raw HTTP `/api/tags` check | Hits the endpoint directly; redundant with what `ollama_available` fixture already does. | |
| You decide | Claude picks based on testing intent. | |

**User's choice:** Call `_check_ollama_health()`
**Notes:** Preferred because it tests the function layer (our code), not just the HTTP layer.

---

## TEST-09 assertion depth

| Option | Description | Selected |
|--------|-------------|----------|
| `content starts with \documentclass` | Required per TEST-09 requirement text | ✓ |
| `content ends with \end{document}` | Required per TEST-09 requirement text | ✓ |
| `fences_stripped == False` | Verifies model returned clean LaTeX without fences | ✓ |
| `No markdown fences in content` | `"```" not in result.content` — direct check matching requirement text | ✓ |

**User's choice:** All four assertions selected.
**Notes:** Full assertion coverage — structural validity (start/end) AND fence absence (both string check and fences_stripped flag).

---

## Claude's Discretion

None — all areas were decided explicitly by the user.

## Deferred Ideas

None — discussion stayed within phase scope.
