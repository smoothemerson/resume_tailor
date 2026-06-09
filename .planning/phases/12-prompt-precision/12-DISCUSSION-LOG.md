# Phase 12: Prompt Precision - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 12-prompt-precision
**Areas discussed:** Tag naming vs. test, LaTeX command precision, Anti-fabrication rule placement

---

## Tag Naming vs. Test

| Option | Description | Selected |
|--------|-------------|----------|
| Keep `<CONSTRAINTS>` as outer tag | Rename inner prose but keep the XML tag so the existing test passes unchanged | ✓ |
| Rename to `<MUST_NOT_CHANGE>` | Use the exact tag that matches the requirement name; test would need updating | |
| Nest inside existing structure | Keep `<INSTRUCTIONS>` + `<CONSTRAINTS>` as outer containers, add inner subsections | |

**User's choice:** Keep `<CONSTRAINTS>` as the outer XML tag; restructure content to MUST-NOT-CHANGE list.

Second question in area — ALLOWED section tag:

| Option | Description | Selected |
|--------|-------------|----------|
| Rename `<INSTRUCTIONS>` to `<ALLOWED>` | Makes two-section structure clear; no test covers this tag | ✓ |
| Keep `<INSTRUCTIONS>`, add ALLOWED header inside | Preserves tag name; slightly less clean | |

**User's choice:** Rename `<INSTRUCTIONS>` to `<ALLOWED>`.

**Notes:** The success criterion "all existing tests pass without modification" is a hard constraint, not a guideline. Only `<CONSTRAINTS>` is tested; `<INSTRUCTIONS>` is not, giving free rename there.

---

## LaTeX Command Precision

| Option | Description | Selected |
|--------|-------------|----------|
| Use `\employer` and `\header` in the prompt | Cite actual commands; guards already parse these exact patterns | ✓ |
| Semantic only | Plain English descriptions only | |
| Both — semantic label + LaTeX command in parentheses | Maximum clarity, more verbose | |

**User's choice:** Use actual LaTeX command names (`\employer{}{}{}`, `\header{}`).

Second question — project/contact commands:

| Option | Description | Selected |
|--------|-------------|----------|
| Researcher finds them in `resumes/english.tex` | Let researcher extract exact macros from the actual resume | ✓ |
| Projects use `\project` or similar | N/A — user deferred to researcher | |
| Contact block is standard LaTeX | N/A — user deferred to researcher | |

**User's choice:** Researcher reads `resumes/english.tex` to extract project and contact block macro names.

**Notes:** `\employer{name}{dates}{title}` (3-arg) and `\header{SectionName}` are known from guards.py regexes. Unknown: project macros, contact block structure.

---

## Anti-Fabrication Rule Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inside `<CONSTRAINTS>` as a named rule | All prohibitions in one place; named bullet (e.g., TECHNOLOGY FIDELITY) | ✓ |
| Its own `<ANTI_FABRICATION>` section | Separate XML section between `<CONSTRAINTS>` and `<OUTPUT_FORMAT>` | |
| Folded into `<ALLOWED>` with a caveat | Co-located with skills reordering rule | |

**User's choice:** Inside `<CONSTRAINTS>` as a prominently labeled named rule.

**Notes:** Suggested label `TECHNOLOGY FIDELITY`. Example language from PRMP-03: "if Azure is in the original it must appear; if AWS is not in the original it must not appear."

---

## Claude's Discretion

- Exact prose/wording within `<ALLOWED>` and `<CONSTRAINTS>` sections
- Whether to use bullet list, numbered list, or sub-headers inside those sections

## Deferred Ideas

None — discussion stayed within phase scope.
