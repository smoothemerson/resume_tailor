# Phase 5: Diff View - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 05-diff-view
**Areas discussed:** Output order, Color output, Diff header labels, Module structure

---

## Output Order

| Option | Description | Selected |
|--------|-------------|----------|
| Diff then confirmation | Diff first, then "Tailored resume written to:" as final line. Confirmation easy to spot at the bottom. | ✓ |
| Confirmation then diff | File path prints first, diff follows below. | |

**User's choice:** Diff then confirmation
**Notes:** None — selected the recommended option.

---

## Color Output

| Option | Description | Selected |
|--------|-------------|----------|
| Colorized | Green for + lines, red for - lines. ANSI escape codes only, no new deps. | ✓ |
| Plain text | Standard +/- prefix, no color. | |

**User's choice:** Colorized
**Notes:** TTY-gated diff makes color always safe — won't leak into pipes.

---

## Diff Header Labels

| Option | Description | Selected |
|--------|-------------|----------|
| --- original / +++ tailored | Simple human-readable labels. | ✓ |
| Actual filenames | Full file paths in headers — long but precise. | |
| Suppress headers | Omit --- / +++ lines entirely. | |

**User's choice:** `--- original` / `+++ tailored`
**Notes:** None — context is obvious, short labels are cleaner.

---

## Module Structure

| Option | Description | Selected |
|--------|-------------|----------|
| New diff_view.py module | Separate src/diff_view.py with single show_diff() function. Follows guards.py pattern. | ✓ |
| Inline in cli.py | Helper function inside cli.py. Fewer files but harder to unit-test. | |

**User's choice:** New `diff_view.py` module
**Notes:** Testability in isolation aligns with Phase 9 unit test goals.

---

## Claude's Discretion

- Context lines for `unified_diff()`: use default of 3.
- No label or header before the diff block — `--- original / +++ tailored` is self-explanatory.
- Normalization: strip trailing whitespace per line + collapse 3+ consecutive blank lines to 2.

## Deferred Ideas

None — discussion stayed within phase scope.
