---
phase: 04-output-reliability-guards
fixed_at: 2026-06-04T14:30:00Z
review_path: .planning/phases/04-output-reliability-guards/04-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 7
skipped: 1
status: partial
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-06-04T14:30:00Z
**Source review:** .planning/phases/04-output-reliability-guards/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (3 Critical + 5 Warning)
- Fixed: 7
- Skipped: 1 (CR-03 resolved as a side-effect of CR-02)

## Fixed Issues

### CR-01: `_check_hallucinated_employers` detects the wrong direction

**Files modified:** `src/guards.py`
**Commit:** b78706c
**Applied fix:** Added a second loop that iterates over `tailored_employers` and logs a warning for any employer present in the tailored output but absent from the original. This catches LLM-invented employers that the original code entirely missed. The original loop (detecting dropped employers) was preserved.

---

### CR-02: `_validate_latex` uses substring check — trailing prose passes validation

**Files modified:** `src/llm_client.py`
**Commit:** f8af9c2
**Applied fix:** Replaced the `"\\end{document}" in text` substring check with `stripped.endswith("\\end{document}")` after calling `text.rstrip()`. Also updated the `startswith` check to use the same `stripped` variable. The error message was updated to reflect the new trailing-prose scenario. This closes the attack surface described in CR-03 as well.

---

### WR-01: `_check_missing_sections` uses substring match — false negatives on section names

**Files modified:** `src/guards.py`
**Commit:** 6179c9e
**Applied fix:** Changed the check from `if section not in tailored` to `if f'\\header{{{section}}}' not in tailored` so the guard looks for the actual LaTeX structural command rather than any occurrence of the section name string anywhere in the document. Existing tests already use `\\header{...}` in their tailored strings and remain compatible.

---

### WR-02: `_check_ollama_health` does not call `raise_for_status`

**Files modified:** `src/llm_client.py`
**Commit:** 067b288
**Applied fix:** Captured the response object returned by `requests.get(...)`, added `response.raise_for_status()`, and added a new `except requests.HTTPError` branch that raises a `RuntimeError` with the HTTP error details. This ensures HTTP 4xx/5xx responses from Ollama during the health check are surfaced with a clean error message rather than passing silently.

---

### WR-03: `_check_format_violations` bold regex misses single-character bold markers

**Files modified:** `src/guards.py`
**Commit:** 8f0b9dd
**Applied fix:** Replaced the pattern `r'\*\*\S[^*]*\S\*\*'` (which requires at least two non-star characters) with `r'\*\*[^*]+\*\*'` (which matches one or more non-star characters). This correctly detects single-character bold markers like `**X**` or `**I**`.

---

### WR-04: `cli_test.py` patches `run_guards` but never asserts it was called

**Files modified:** `src/cli_test.py`
**Commit:** 40230cd
**Applied fix:** Added `mock_guards.assert_called_once_with("resume text", "\\documentclass{article}\n\\end{document}", False)` assertion to `test_end_sentinel_breaks_loop`. This verifies that `run_guards` is actually called on the happy path with the correct arguments, so deleting the `run_guards(...)` call in `cli.py` would now cause a test failure.

---

### WR-05: Error-path tests do not patch `cli.run_guards` — fragile implicit ordering

**Files modified:** `src/cli_test.py`
**Commit:** 3f8dcd2
**Applied fix:** Added `@patch("cli.run_guards")` decorator and `mock_guards` parameter to both `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1`. The parameter is appended after the existing `mock_generate` parameter following Python's decorator stacking order (innermost decorator = leftmost parameter after `self`). These tests now explicitly isolate `run_guards` regardless of call order changes in the future.

---

## Skipped Issues

### CR-03: `_strip_fences` only removes outermost fence pair — mid-document fence plus trailing prose corrupts output silently

**File:** `src/llm_client.py:109-113`
**Reason:** The reviewer explicitly noted that applying the CR-02 fix (enforcing `\end{document}` as terminal) "closes this attack surface entirely." The CR-02 fix was applied and committed (f8af9c2). CR-03 is resolved as a side-effect of CR-02 — `_validate_latex` will now reject any output containing trailing prose after `\end{document}`, regardless of fence stripping completeness. No separate code change was needed.
**Original issue:** `_strip_fences` regex only removes outermost fences, leaving mid-document fence residue when prose follows the closing `\end{document}`.

---

_Fixed: 2026-06-04T14:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
