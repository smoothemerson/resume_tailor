# Phase 07: JD Keyword Match Summary - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 07-jd-keyword-match-summary
**Areas discussed:** Display format, Stop word scope, Module placement

---

## Display format

### What should the match summary show?

| Option | Description | Selected |
|--------|-------------|----------|
| Count + matched list | "Keyword match: 14/20\n  ✓ Python, FastAPI, RAG, Docker..." — clear signal plus actual matched words | ✓ |
| Count only | "Keyword match: 14/20" — minimal, just the number | |
| Matched + unmatched | Shows both matched and unmatched — full gap analysis, more verbose | |

**User's choice:** Count + matched list

---

### Should keywords be grouped by category or shown as a flat list?

| Option | Description | Selected |
|--------|-------------|----------|
| Flat list | All matched keywords in one line — "Python, FastAPI, RAG, Docker" — compact | ✓ |
| By category | Three labeled groups: "Technologies: ... \| Requirements: ... \| Emphasis: ..." | |
| You decide | Leave grouping decision to the planner | |

**User's choice:** Flat list

---

### Where in the output flow does the match summary appear?

| Option | Description | Selected |
|--------|-------------|----------|
| After diff, before final path | show_diff() → match summary → "Tailored resume written to: ..." | ✓ |
| After final path | "Tailored resume written to: ..." → match summary | |
| You decide | Leave position to the planner | |

**User's choice:** After diff, before final path

---

## Stop word scope

### How comprehensive should the stop word filter be?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal (~15 words) | Filter only the most common function words: a, an, the, and, or, of, in, to, for, with, is, are, be, on, at | ✓ |
| Standard English (~100 words) | Full NLTK-style list covering pronouns, prepositions, conjunctions, auxiliaries | |
| You decide | Leave exact word count to the planner | |

**User's choice:** Minimal (~15 words)

---

### Where should the stop word set be defined?

| Option | Description | Selected |
|--------|-------------|----------|
| Module-level frozenset constant | STOP_WORDS = frozenset({...}) at top of file — named, findable, easy to extend | ✓ |
| Inline in function | Defined inside the matching function body — simpler, slightly less visible | |
| You decide | Leave placement to the planner | |

**User's choice:** Module-level frozenset constant (STOP_WORDS)

---

## Module placement

### Where should the keyword matching logic live?

| Option | Description | Selected |
|--------|-------------|----------|
| New keyword_matcher.py | Matches single-concern pattern: guards.py, diff_view.py, jd_analyzer.py | ✓ |
| Inline in cli.py | Matching logic in main() — fewer files but breaks established module pattern | |
| You decide | Leave the module decision to the planner | |

**User's choice:** New keyword_matcher.py

---

### What should the public entry point signature look like?

| Option | Description | Selected |
|--------|-------------|----------|
| show_keyword_match(analysis, tailored_text) | Single function, matches show_diff(original, tailored) pattern | ✓ |
| Two functions: match() + show() | Separate match_keywords() and show_keyword_match() for testability | |
| You decide | Leave the signature to the planner | |

**User's choice:** show_keyword_match(analysis, tailored_text)

---

## Claude's Discretion

- Minimum keyword length cutoff (e.g., skip single-char tokens like "C") — left to the planner
- Exact behavior when 0 keywords match — planner decision (show "0/N" with no list line)
- Whether `show_keyword_match()` wraps its body in `try/except Exception` (expected: yes, per non-fatal guard pattern)

## Deferred Ideas

None — discussion stayed within phase scope.
