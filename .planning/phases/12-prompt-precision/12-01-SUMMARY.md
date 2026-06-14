---
phase: 12-prompt-precision
plan: 01
subsystem: llm
tags: [prompt-engineering, ollama, latex]

requires: []
provides:
  - "_build_messages() system prompt with <ALLOWED> section naming the six rewritable resume elements by LaTeX pattern"
  - "<CONSTRAINTS> section with MUST NOT CHANGE list of nine protected inline LaTeX patterns"
  - "TECHNOLOGY FIDELITY rule inside <CONSTRAINTS> with Azure/AWS example"
affects: []

tech-stack:
  added: []
  patterns:
    - "Raw string literal for prompts containing LaTeX backslash sequences"

key-files:
  created: []
  modified:
    - src/llm_client.py

key-decisions:
  - "Converted system_prompt to a raw string (r-prefix on line 27, inside the editable region) because the new content includes \\usepackage (\\u is a hard Python SyntaxError in non-raw strings) and \\textit/\\noindent/\\begin/\\vspace (silent escape corruption)"
  - "Used 8-space indentation for all continuation lines per plan instruction, overriding the 10-space continuation shown in PATTERNS.md target snippets"

duration: 5min
completed: 2026-06-10
---

# Phase 12 Plan 01: Prompt Precision Summary

Rewrote the `_build_messages()` system prompt to replace the generic `<INSTRUCTIONS>` block with an explicit `<ALLOWED>` whitelist and a `<CONSTRAINTS>` MUST-NOT-CHANGE list referencing the resume's actual inline LaTeX patterns, plus a TECHNOLOGY FIDELITY rule.

## What Was Built

The system prompt in `src/llm_client.py` `_build_messages()` now has the section order `<PERSONA>` -> `<TASK>` -> `<CONTEXT>` -> `<ALLOWED>` -> `<CONSTRAINTS>` -> `<OUTPUT_FORMAT>` (D-06). PERSONA, TASK, CONTEXT, and OUTPUT_FORMAT are byte-identical to the previous version.

**`<ALLOWED>` (renamed from `<INSTRUCTIONS>`, D-01)** lists exactly six rewritable elements with their LaTeX patterns:
1. Title line in the contact header
2. Employer taglines (`\textit{\small ...}\\`)
3. Employer bullet points (`\item` inside `\begin{itemize}`, count fixed)
4. Project subtitle (text after `\textbf{ProjectName}`)
5. Project bullet points (count fixed)
6. Skills content (`\noindent\textbf{Category:}` lines, reorder/reweight only)

Closes with "Everything not listed above must remain byte-for-byte identical."

**`<CONSTRAINTS>` (tag kept, content rewritten, D-02)** contains:
- MUST NOT CHANGE: nine protected elements by actual inline pattern — candidate name (`{\Huge \scshape {Name}}\\`), contact block, Education section, Languages section, employer header lines (`\textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\`), project anchors (`\href{url}{\textbf{ProjectName}}`), section headers (`\header{...}`), all LaTeX commands/environments, bullet point count
- TECHNOLOGY FIDELITY (D-05): present technologies must remain, absent technologies must not be added, with the Azure/AWS example

Per RESEARCH.md Pitfall 1, the prompt does not reference `\employer{}{}{}` or `\contact{}{}{}` macro signatures — only the inline patterns actually used in the resume body.

## Verification Results

- `pytest tests/unit/test_llm_client.py -x -q` — 26 passed
- `pytest src/llm_client_test.py -x -q` — 15 passed
- `pytest -m unit -x -q` — 50 passed, 57 deselected
- `pytest -x -q` (full suite) — 104 passed, 3 skipped (Ollama-dependent integration/e2e, expected)
- `grep -c '<ALLOWED>' src/llm_client.py` = 1; `<CONSTRAINTS>` = 1; `TECHNOLOGY FIDELITY` = 1; `<INSTRUCTIONS>` = 0; `\employer{` = 0
- Runtime assertion confirmed the rendered prompt string contains literal `\usepackage` and `\textit{\small ...}\\` (raw string renders backslashes correctly)
- All existing tests pass without modification

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Raw string prefix required for new prompt content**
- **Found during:** Task 1
- **Issue:** The new prompt text includes `\usepackage`, which in a non-raw Python string is a truncated `\uXXXX` escape and a hard SyntaxError; `\textit`, `\noindent`, `\begin`, `\vspace` would silently corrupt to tab/newline/backspace/vertical-tab characters
- **Fix:** Changed `system_prompt = """` to `system_prompt = r"""` on line 27, which is inside the plan's editable region (lines 27–95). Unchanged sections (`\documentclass`, `\end{document}`) render identically under the raw prefix since `\d` and `\e` were already literal
- **Files modified:** src/llm_client.py
- **Commit:** f6a4e13

**2. [Rule 3 - Blocking] Broken project venv interpreter in worktree environment**
- **Found during:** Task 1 verification
- **Issue:** `/workspace/.venv/bin/python` is a broken symlink to `/home/emerson/.pyenv/versions/3.13.8/bin/python3` (created on another machine); system python3 has no pytest/requests
- **Fix:** Ran the test suite with system `python3` and `PYTHONPATH=/workspace/.venv/lib/python3.13/site-packages` (pytest and requests are pure Python). No project files changed
- **Files modified:** none
- **Commit:** n/a (environment workaround only)

## Known Stubs

None — the change is a complete prompt rewrite with no placeholder content.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or dependencies. Pure string-literal edit, consistent with the plan's threat model (T-12-01/T-12-02/T-12-SC all accepted).

## Self-Check: PASSED

- src/llm_client.py exists and contains `<ALLOWED>`, `</ALLOWED>`, `<CONSTRAINTS>`, `</CONSTRAINTS>`, `TECHNOLOGY FIDELITY`
- Commit f6a4e13 exists on worktree-agent-a218df6d81c8177f2
- Full test suite exits 0 (104 passed, 3 skipped)
