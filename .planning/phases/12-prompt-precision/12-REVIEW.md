---
phase: 12-prompt-precision
reviewed: 2026-06-11T21:17:40Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - src/llm_client.py
findings:
  critical: 0
  warning: 1
  info: 5
  total: 6
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-11T21:17:40Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Fresh re-review of `src/llm_client.py` after the iteration-1 fixes (12-REVIEW-FIX.md, commits b342794, 806a44c, bd3e178, 1ea2441). All four previously blocking/warning findings are verified resolved in the current file:

- **CR-01 resolved** — `<CONSTRAINTS>` (lines 70-72) no longer says "entire" and carries an EXCEPT clause naming the `\ {AI Engineer}\\` title line as the only rewritable line inside `\begin{center}`; `<ALLOWED>` line 54 mirrors the pattern. No contradiction remains.
- **CR-02 resolved** — `<OUTPUT_FORMAT>` line 96 now reads "Rewritten content limited to the six elements listed in <ALLOWED>." The stale "professional summary, skills, and experience bullets only" checklist is gone.
- **WR-01 resolved** — the blanket LaTeX-commands constraint (lines 79-82) now carries the command-vs-argument qualifier: "the commands themselves never change; only text content inside the elements listed in <ALLOWED> may be reworded."
- **WR-02 resolved** — line 102 forbids "comments of any kind — including LaTeX % comment lines," closing the `%` annotation loophole.

Structural verification: all six prompt tags (`<PERSONA>`, `<TASK>`, `<CONTEXT>`, `<ALLOWED>`, `<CONSTRAINTS>`, `<OUTPUT_FORMAT>`) are present and balanced; the raw string renders all LaTeX escapes literally; the prompt correctly references the resume's actual inline patterns (`\textbf{EMPLOYER}\textbf{ | ROLE} \hfill ...`, `\textit{\small ...}\\`, `{\Huge \scshape ...}\\`) rather than the unused `\employer{}{}{}` macro form, matching the 12-RESEARCH.md findings (lines 122, 128, 217). The gating tag-presence tests in `tests/unit/test_llm_client.py` (lines 30-31, 37-38) remain satisfied.

One new precision gap was found in the rewrite-scope instructions (WR-01 below): the `<ALLOWED>` skills entry cites the `\noindent\textbf{Category:}` pattern without scoping it to the Skills section, and the protected Languages section uses the byte-identical pattern. Two prior Info items (project subtitle wrapper, `_validate_latex` return) were out of the iteration-1 fix scope and remain open; three new Info items were found. Tests could not be executed in this environment (no pytest, no requests module); all verification was static.

## Warnings

### WR-01: ALLOWED skills pattern is unscoped and byte-identical to protected Languages lines

**File:** `src/llm_client.py:61-62` (conflicts with `src/llm_client.py:74`)
**Issue:** `<ALLOWED>` grants: "Skills content: the technology lists on \noindent\textbf{Category:} lines." Per 12-RESEARCH.md, the Skills section uses `\noindent\textbf{AI:} LangChain, ChromaDB, ...\\` (line 141) — but the Languages section uses the byte-identical pattern: `\noindent\textbf{English:} Professional Working Proficiency\\` (line 144). The ALLOWED entry does not scope the pattern to the Skills section, so a model pattern-matching `\noindent\textbf{X:}` lines will see the Languages entries as rewritable "Category:" lines. `<CONSTRAINTS>` line 74 protects "everything under \header{Languages}", so the two instructions collide on the same lines — the same ambiguity class as the fixed WR-01/CR-01: a model weighting ALLOWED over CONSTRAINTS may "reorder/reweight" the Languages entries, corrupting protected content. The phase goal was eliminating exactly this kind of scope imprecision.
**Fix:** Scope the pattern to its section:
```text
- Skills content: the technology lists on \noindent\textbf{Category:} lines under
\header{Skills} only — the \noindent\textbf{...:} lines under \header{Languages}
use the same pattern and are protected
(reorder/reweight within categories; use only skills already present in the original)
```

## Info

### IN-01: Project subtitle pattern still omits the actual `\text{ | ...}` wrapper (carried from prior IN-02)

**File:** `src/llm_client.py:58`
**Issue:** Unchanged from the prior review (it was outside the critical_warning fix scope). The entry reads "the descriptive text after \textbf{ProjectName} on each project line," but per 12-RESEARCH.md line 295 the subtitle lives inside a `\text{ | subtitle}` wrapper following the `\href{...}{\textbf{Name}}` anchor. Naming the wrapper would tell the model exactly which braces it may edit inside and would protect the literal `| ` separator.
**Fix:** `- Project subtitle: the text inside \text{ | ...} after the \href{...}{\textbf{ProjectName}} anchor on each project line`

### IN-02: `_validate_latex` return value discarded at call site (carried from prior IN-03)

**File:** `src/llm_client.py:201` (function at `src/llm_client.py:141-151`)
**Issue:** Unchanged from the prior review. `_validate_latex` returns `text` but the only call site uses it purely for its raise-on-invalid side effect, discarding the return. Harmless, but the signature overpromises.
**Fix:** Either use the return (`content = _validate_latex(content)`) or change the return type to `None` and drop the `return text`.

### IN-03: Mixed placeholder vs concrete values across the title-line references

**File:** `src/llm_client.py:54` (vs `src/llm_client.py:72`)
**Issue:** `<ALLOWED>` cites the title line as `\ {Title}\\` (generic placeholder) while `<CONSTRAINTS>` cites the same line as `\ {AI Engineer}\\` (concrete value from the resume). Line 69 similarly uses the `{Name}` placeholder. A model has to infer that `{Title}` and `{AI Engineer}` denote the same physical line; using the concrete pattern in both places (or placeholders in both) removes the inference step.
**Fix:** Use `\ {AI Engineer}\\` in the ALLOWED entry as well, matching the CONSTRAINTS wording.

### IN-04: Hardcoded `num_ctx: 8192` magic number

**File:** `src/llm_client.py:165`
**Issue:** `"options": {"num_ctx": 8192}` embeds a model-tuning constant in the request-building code while all other runtime constants (`OLLAMA_MODEL`, `TIMEOUT`, `OLLAMA_BASE_URL`) live in `config.py`. If the resume plus job description outgrow this window, the only signal is the `done_reason == "length"` failure; adjusting the limit requires editing client code instead of config.
**Fix:** Add `NUM_CTX: int = 8192` to `src/config.py` and reference it in the payload.

### IN-05: Every system-prompt line carries 8 spaces of source indentation

**File:** `src/llm_client.py:27-105`
**Issue:** The raw string is indented to match the function body, and `.strip()` only removes leading/trailing whitespace of the whole string — verified statically: every non-empty line after the first reaches the model with an 8-space prefix. This is harmless to meaning but adds token noise on ~75 lines and prefixes the literal LaTeX patterns the model is told to match.
**Fix:** Dedent at build time with stdlib: `textwrap.dedent(...)` (move the prompt's body one indent level into the raw string margins), or store the prompt as a module-level constant with no indentation.

---

_Reviewed: 2026-06-11T21:17:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
