---
phase: 12-prompt-precision
reviewed: 2026-06-10T18:16:40Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - src/llm_client.py
findings:
  critical: 2
  warning: 2
  info: 3
  total: 7
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-10T18:16:40Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Phase 12 rewrote the system prompt in `_build_messages()` (src/llm_client.py:27-102), replacing the generic `<INSTRUCTIONS>` block with explicit `<ALLOWED>` and MUST-NOT-CHANGE lists referencing the resume's actual inline LaTeX patterns, and converting the string literal to a raw string. The mechanical execution is correct: the raw string safely contains `\usepackage`, `\textit{\small ...}\\` and similar escapes; the `<ALLOWED>`/`<CONSTRAINTS>` tags required by the gating tests are present; the forbidden `\employer{` macro signature and the old `<INSTRUCTIONS>` tag are absent; no code outside the prompt string was modified.

However, the prompt — the sole deliverable of this phase, whose explicit goal was precision — contains two direct internal contradictions in its rewrite-scope instructions (CR-01, CR-02) and two weaker conflicts (WR-01, WR-02). For a phase named "prompt-precision," contradictory scope instructions are incorrect behavior of the deliverable itself: depending on which instruction the model obeys, it will either refuse a permitted rewrite (title line) or perform a forbidden one (entire contact block, or skip project bullets). These must be resolved before this prompt ships.

Tests could not be executed in the review environment (no pytest available); the plan's tag-presence acceptance criteria were verified by static inspection and all pass.

## Critical Issues

### CR-01: ALLOWED title line directly contradicts MUST-NOT-CHANGE contact block

**File:** `src/llm_client.py:54` (conflicts with `src/llm_client.py:70-71`)
**Issue:** `<ALLOWED>` grants rewrite permission for "Title line: the professional title in the contact header" (line 54). `<CONSTRAINTS>` forbids changing "Contact block: the entire \begin{center}...\end{center} block at the top of the document" (lines 70-71). Per 12-RESEARCH.md (lines 134-135, 292), the title line is the `\ {AI Engineer}\\` line *inside* that same `\begin{center}` block. The two instructions are mutually exclusive: a model honoring the stricter constraint ("entire ... block") will never rewrite the title — defeating ALLOWED item 1 — while a model honoring ALLOWED violates the byte-for-byte protection on the contact block, risking edits to name/email/phone/links that the downstream pipeline assumes immutable. The word "entire" makes this a hard logical contradiction, not an ambiguity.
**Fix:** Carve the title line out of the contact-block protection and name its exact pattern (which D-03/D-04 required for all elements):
```text
- Contact block: the \begin{center}...\end{center} block at the top of the document
  (name, email, phone, location, LinkedIn, GitHub) — EXCEPT the professional title line
  (the \ {AI Engineer}\\ line), which is the only rewritable line inside this block
```
And mirror the exact pattern in ALLOWED: `- Title line: the \ {Title}\\ line in the \begin{center} contact header`.

### CR-02: OUTPUT_FORMAT carries stale scope list that contradicts ALLOWED

**File:** `src/llm_client.py:93`
**Issue:** Line 93 states: "✅ Rewritten sections: professional summary, skills, and experience bullets only." This is leftover text from the pre-phase `<INSTRUCTIONS>` prompt (visible in 12-RESEARCH.md line 191). It contradicts the new `<ALLOWED>` list in two ways: (1) the resume has no "professional summary" section — the six ALLOWED elements are title line, employer taglines, employer bullets, project subtitle, project bullets, and skills content; (2) the word "only" excludes four of the six ALLOWED elements (title line, taglines, project subtitle, project bullets). A model that weights this later, checklist-style instruction will skip project bullet and subtitle rewrites entirely, or invent a "professional summary" to satisfy the checklist. Two competing "only" scope lists in one prompt is exactly the imprecision this phase existed to eliminate. (The plan instructed copying OUTPUT_FORMAT verbatim — the plan carried the defect; the shipped artifact still contains it.)
**Fix:**
```text
✅ Rewritten content limited to the six elements listed in <ALLOWED>.
```

## Warnings

### WR-01: Blanket "\textbf, \textit must not change" conflicts with rewriting tagline and skills content

**File:** `src/llm_client.py:78-79` (conflicts with `src/llm_client.py:55,61`)
**Issue:** The MUST-NOT-CHANGE bullet "All LaTeX commands and environments: ... \textbf, \textit, \href, and all other structural commands" omits the qualifier present in the research draft (12-RESEARCH.md line 314): "and all other commands *outside the changeable content listed in ALLOWED*." Without it, the constraint reads as protecting `\textit` wholesale — yet ALLOWED line 55 instructs rewriting the content *inside* `\textit{\small ...}` (employer taglines). A literal-minded model may refuse tagline rewrites; a loose one may take "commands stay, arguments are fair game" and edit `\textbf{EMPLOYER}` arguments too. The command-vs-argument distinction is never stated.
**Fix:** Restore the qualifier and state the distinction explicitly:
```text
- All LaTeX commands and environments: \documentclass, \usepackage, \newcommand definitions,
  \begin, \end, \vspace, \hfill, \textbf, \textit, \href, and all other structural commands —
  the commands themselves never change; only text content inside the elements listed in
  <ALLOWED> may be reworded
```

### WR-02: OUTPUT_FORMAT implicitly licenses inserting LaTeX % comments

**File:** `src/llm_client.py:99` (conflicts with `src/llm_client.py:64`)
**Issue:** "❌ Explanations, comments, or annotations outside LaTeX comment syntax (%)" forbids only comments *outside* `%` syntax, implying the model may freely add `% ...` annotation lines inside the document. Any inserted `%` line violates "Everything not listed above must remain byte-for-byte identical" (line 64), pollutes the output diff, and conflicts with the project convention of no comments. Another internal contradiction in rewrite scope, lower impact than CR-01/CR-02 because it adds noise rather than corrupting protected content.
**Fix:**
```text
❌ Explanations, annotations, or comments of any kind — including LaTeX % comment lines.
```

## Info

### IN-01: Title line is the only ALLOWED element without a concrete LaTeX pattern

**File:** `src/llm_client.py:54`
**Issue:** Decisions D-03/D-04 require referencing actual LaTeX patterns; the other five ALLOWED entries cite patterns (`\textit{\small ...}\\`, `\item`, `\textbf{ProjectName}`, `\noindent\textbf{Category:}`), but the title line is described only semantically. The actual pattern is `\ {AI Engineer}\\` (12-RESEARCH.md line 292).
**Fix:** Covered by the CR-01 fix — cite the `\ {Title}\\` pattern.

### IN-02: Project subtitle pattern omits the actual `\text{ | ...}` wrapper

**File:** `src/llm_client.py:58`
**Issue:** Described as "the descriptive text after \textbf{ProjectName}", but per 12-RESEARCH.md line 295 the subtitle lives in a `\text{ | subtitle}` wrapper following the `\href{...}{\textbf{Name}}` anchor. Naming the wrapper would tell the model exactly which braces it may edit inside and would protect the literal `| ` separator.
**Fix:** `- Project subtitle: the text inside \text{ | ...} after the \href{...}{\textbf{ProjectName}} anchor on each project line`.

### IN-03: `_validate_latex` return value discarded at call site

**File:** `src/llm_client.py:198` (function at `src/llm_client.py:138-148`)
**Issue:** `_validate_latex` returns `text` but the only call site uses it purely for its raise-on-invalid side effect, discarding the return. Pre-existing (outside the phase diff); harmless but the signature overpromises.
**Fix:** Either use the return (`content = _validate_latex(content)`) or change the function to return `None`.

---

_Reviewed: 2026-06-10T18:16:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
