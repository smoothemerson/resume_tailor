# Phase 13: Guard Expansion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 13-Guard Expansion
**Areas discussed:** Skills section extraction, Protected element patterns, Test file placement, Warning message content

---

## Skills Section Extraction

| Option | Description | Selected |
|--------|-------------|----------|
| `\header{Skills}` boundary | Extract between `\header{Skills}` and next `\header{...}` — consistent with existing pattern | ✓ |
| Regex for known skills macro | Match a custom macro like `\skills{...}` | |
| No section boundary — full-text scan | Look for tokens anywhere in full text | |

**User's choice:** `\header{Skills}` boundary (Recommended)
**Notes:** Consistent with the `_check_missing_sections` pattern already in use.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Comma-separated items | Split on `,\s*` — handles multi-word tech names correctly | ✓ |
| Word-level tokens | Split on whitespace/punctuation — breaks multi-word names | |
| Line-by-line items | Each line is a technology or category | |

**User's choice:** Comma-separated items (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Strip LaTeX commands first | Remove `\textbf{}`, `\emph{}` before splitting | ✓ |
| Tokenize raw LaTeX | Split raw LaTeX as-is | |

**User's choice:** Strip LaTeX commands first (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Silent — return without warning | No Skills header = nothing to compare | ✓ |
| Warn that Skills section is missing | Treat absence as a problem | |

**User's choice:** Silent — return without warning (Recommended)
**Notes:** GARD-05 explicitly says "silent for identical or no skills section". Avoids overlap with `_check_missing_sections`.

---

## Protected Element Patterns

| Option | Description | Selected |
|--------|-------------|----------|
| Preamble block — before first `\header{}` | Everything before first `\header{...}` | |
| Custom macro — e.g. `\contact{}{}{}` | A dedicated macro call | |
| Researcher should inspect the resume | Let researcher read `resumes/english.tex` | ✓ |

**User's choice:** I'm not sure — researcher should inspect the resume
**Notes:** Contact block pattern unknown. Researcher must read `resumes/english.tex` to identify the actual LaTeX structure.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full section content comparison | Extract and compare full section between `\header` delimiters | ✓ |
| Header-only check | Just verify headers are present (redundant with GUARD-01) | |

**User's choice:** Full section content comparison (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse `_EMPLOYER_PATTERN` for employer headers | Stricter check than `_check_hallucinated_employers` | ✓ |
| Skip employer headers — covered by existing guard | Rely on GUARD-03 | |

**User's choice:** Reuse `_EMPLOYER_PATTERN` for employer header check (Recommended)
**Notes:** The existing guard catches add/remove; this one catches any mutation in the header line itself.

---

| Option | Description | Selected |
|--------|-------------|----------|
| `\project{name}{url}{date}` or similar 3-arg macro | Analogous to `\employer` | |
| `\projectentry` or another known macro | If macro name is known | |
| Unknown — researcher should find it | Let researcher grep the resume | ✓ |

**User's choice:** Unknown — researcher should find it
**Notes:** Researcher should grep `resumes/english.tex` for project entry commands and determine the right pattern.

---

## Test File Placement

| Option | Description | Selected |
|--------|-------------|----------|
| New file: `tests/unit/test_guards.py` | Matches Phase 9 pattern: `tests/unit/`, `test_*.py`, `@pytest.mark.unit` | ✓ |
| Extend `src/guards_test.py` | Add to existing file, mixing marked/unmarked tests | |
| Both — split by concern | More files, split by happy-path vs edge-cases | |

**User's choice:** New file: `tests/unit/test_guards.py` (Recommended)
**Notes:** Keeps src/ tests consistent (no markers) and tests/unit/ consistent (@pytest.mark.unit).

---

| Option | Description | Selected |
|--------|-------------|----------|
| pytest-style functions | `def test_*`, `@pytest.mark.unit` decorator | ✓ |
| `unittest.TestCase` classes | Matches src/ style | |

**User's choice:** pytest-style functions (Recommended)

---

## Warning Message Content

| Option | Description | Selected |
|--------|-------------|----------|
| Name the specific technologies | e.g. "replaced [AWS] with [Azure]" | ✓ |
| Category only | e.g. "Technology substitution detected" | |

**User's choice:** Name the specific technologies (Recommended)
**Notes:** Same level of detail as the existing employer hallucination warning.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Three separate warnings | One per GARD-05 case: substitution / removal-only / addition-only | ✓ |
| Single combined warning | Summarize all changes in one message | |

**User's choice:** Three separate warnings (Recommended)
**Notes:** Easier to test and more informative. Each test case maps to one warning call.

---

| Option | Description | Selected |
|--------|-------------|----------|
| One warning per changed element | e.g. "Education section was modified" — one per element | ✓ |
| One combined warning listing all changed elements | e.g. "Protected sections modified: Education, Languages" | |

**User's choice:** One warning per changed element (Recommended)
**Notes:** Matches existing per-section warning pattern from `_check_missing_sections`.

---

## Claude's Discretion

None — all implementation decisions were decided by the user.

## Deferred Ideas

None — discussion stayed within phase scope.
