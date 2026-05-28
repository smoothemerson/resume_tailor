---
phase: 02-llm-integration
reviewed: 2026-05-28T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/llm_client.py
  - src/log_manager.py
  - src/llm_client_test.py
findings:
  critical: 0
  warning: 6
  info: 3
  total: 9
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-28
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed `src/llm_client.py`, `src/log_manager.py`, and `src/llm_client_test.py` — the LLM
integration layer. No critical (security or data-loss) bugs found. The core logic is structurally
sound: exception handling order is safe (`requests.Timeout` is not a subclass of
`requests.ConnectionError`, so ordering is correct), the health check timeout semantics are correct
(`TIMEOUT[0]` as a bare int applies to both connect and read), and `stacklevel=3` in
`CustomLogger._log_with_extra` correctly attributes log records to the actual caller.

Six warnings require attention before this code is production-ready. The most impactful are: an
unhandled `KeyError` on the API response parse path, a fence-stripping regex that fails silently on
space-separated language tags, and `_validate_latex` accepting responses that contain prose before
the LaTeX content. Additionally, `log_manager.py` violates two project conventions from `CLAUDE.md`
(use of the `logging` module instead of `print`, and routing logs to `stdout` instead of `stderr`).

## Warnings

### WR-01: Unhandled `KeyError` on API response parse (line 100, `llm_client.py`)

**File:** `src/llm_client.py:100`
**Issue:** `data["message"]["content"]` uses bare dict access. `raise_for_status()` on line 81
prevents 4xx/5xx bodies from reaching this point, but Ollama can return HTTP 200 with an error
body such as `{"error": "model not found"}` when the model name is invalid. In that case `message`
key is absent and a raw `KeyError` propagates to the caller with no helpful message.

**Fix:**
```python
try:
    content = data["message"]["content"]
except KeyError as exc:
    raise RuntimeError(
        f"Unexpected Ollama response structure: {data}"
    ) from exc
```

---

### WR-02: `_strip_fences` silently fails on space-separated fence language tag

**File:** `src/llm_client.py:45`
**Issue:** The regex `^```\w*\n?` matches triple-backticks followed by zero or more word characters.
If the LLM outputs ` ```latex` (common variant) the regex works, but if it outputs ` ``` latex`
(space between backticks and language name), `\w*` stops at the space, the `\n?` fails to consume
it, and the result is `" latex\n<actual content>"` passed to `_validate_latex`. The `\documentclass`
check still finds its target via substring search so `_validate_latex` passes, and the file written
to disk starts with `" latex\n"` — invalid LaTeX.

**Fix:** Extend the regex to handle an optional space before the language tag and make the language
tag portion optional including surrounding whitespace:
```python
text = re.sub(r"^```\s*\w*\s*\n?", "", text)
```

---

### WR-03: `_validate_latex` accepts responses that contain prose before `\documentclass`

**File:** `src/llm_client.py:51-58`
**Issue:** Both checks use `in` (substring membership). If the LLM prepends prose — e.g.,
`"Here is your tailored resume:\n\n```latex\n\\documentclass{article}..."` — and the fence strip
does not fully remove the wrapper (see WR-02, or when the opening fence is not at position 0),
`_validate_latex` still passes because `\\documentclass` exists anywhere in the string. The file
written to disk then contains the prose prefix and will not compile.

**Fix:** Assert that `\documentclass` appears at the start of the (stripped) text:
```python
def _validate_latex(text: str) -> str:
    if not text.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if "\\end{document}" not in text:
        raise ValueError(
            "LLM response does not contain \\end{document} — output may be truncated."
        )
    return text
```

---

### WR-04: `response.json()` not guarded against `JSONDecodeError`

**File:** `src/llm_client.py:92`
**Issue:** `data = response.json()` is outside the `try/except` block (lines 75-90). If Ollama
returns a non-JSON body with a 200 status code (e.g. during version mismatches or reverse-proxy
intercepts), `requests.exceptions.JSONDecodeError` propagates unhandled with no user-friendly
message.

**Fix:** Move the json parse inside the error handling block or add its own guard:
```python
try:
    data = response.json()
except requests.exceptions.JSONDecodeError as exc:
    raise RuntimeError(
        f"Ollama returned non-JSON response: {response.text[:200]}"
    ) from exc
```

---

### WR-05: `log_manager` uses `logging` module — violates project convention (`CLAUDE.md`)

**File:** `src/log_manager.py:1,20`
**Issue:** `CLAUDE.md` explicitly states: *"The tool has two output paths: success message to
stdout, error message to stderr. A full logging framework is unnecessary. Direct
`print(..., file=sys.stderr)` is cleaner for a CLI."* `log_manager.py` wraps Python's `logging`
module with a custom class, contradicting this constraint. The extra indirection (`CustomLogger` →
`_log_with_extra` → `logging.Logger.log`) adds complexity with no benefit over `print`.

**Fix:** Replace `log_manager.py` with a minimal shim that routes to `print`:
```python
import sys

class _Logger:
    def info(self, message: str) -> None:
        print(message, file=sys.stderr)

    def warning(self, message: str) -> None:
        print(f"WARNING: {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        print(f"ERROR: {message}", file=sys.stderr)

logger = _Logger()
```

---

### WR-06: Log handler writes to `sys.stdout` — pollutes stdout for a CLI tool

**File:** `src/log_manager.py:20`
**Issue:** `handler = logging.StreamHandler(sys.stdout)` routes all log output to standard output.
For a CLI tool that could pipe its LaTeX output, logging to stdout risks corrupting the output
stream. Log/diagnostic output in CLIs must go to `stderr`. This is also inconsistent with the
project convention cited in WR-05.

**Fix:** Replace with `sys.stderr`:
```python
handler = logging.StreamHandler(sys.stderr)
```
(Or, preferably, apply the full fix from WR-05 and remove the `logging` dependency entirely.)

---

## Info

### IN-01: `LOG_FORMAT` environment variable is read but never used (dead code)

**File:** `src/log_manager.py:6`
**Issue:** `LOG_FORMAT = os.environ.get("LOG_FORMAT", "text").lower()` is assigned but referenced
nowhere else in the file. There is no JSON formatting branch. This implies an incomplete feature
or leftover from a design that was not implemented. The `os` import on line 2 exists solely for
this dead assignment.

**Fix:** Remove both the `os` import and the `LOG_FORMAT` assignment, or implement the JSON
formatting branch if structured logging is desired.

---

### IN-02: `ConnectTimeout` caught by `ConnectionError` handler — misleading error message

**File:** `src/llm_client.py:82-84` and `src/llm_client.py:12-14`
**Issue:** `requests.exceptions.ConnectTimeout` is a multiple-inheritance subclass of both
`requests.Timeout` and `requests.ConnectionError`. In the `except` chain, `ConnectionError` is
listed first, so `ConnectTimeout` is caught there and reports *"Cannot connect to Ollama"* rather
than *"timed out"*. This is misleading for operators debugging a slow-to-accept Ollama instance.

**Fix:** Reorder the `except` clauses so `Timeout` is caught before `ConnectionError`:
```python
except requests.Timeout as exc:
    ...
except requests.ConnectionError as exc:
    ...
```
Apply in both `_check_ollama_health` and `generate_tailored_resume`.

---

### IN-03: `_check_ollama_health` does not call `raise_for_status()`

**File:** `src/llm_client.py:9-17`
**Issue:** The health check catches `ConnectionError` and `Timeout` but ignores HTTP error status
codes (5xx from a reverse proxy, for example). A 503 would silently pass the health gate and then
fail at `raise_for_status()` on the main request, producing a less precise error. The health check
effectively tests only TCP reachability, not Ollama availability.

**Fix:** Add a status check after the `get` call:
```python
response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
response.raise_for_status()
```
Wrap in a new `except requests.HTTPError` clause with an appropriate error message.

---

_Reviewed: 2026-05-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
