# Architecture Patterns

**Domain:** Python CLI tool — LaTeX resume tailoring via local Ollama LLM
**Researched:** 2026-06-02 (v1.1 output quality update)
**Confidence:** HIGH — derived from actual codebase inspection and verified stdlib capabilities

---

## v1.1 Integration: New vs Modified Modules

### What Exists (v1.0 baseline)

| Module | LOC | Responsibility |
|--------|-----|----------------|
| `cli.py` | 59 | Orchestrator: arg parsing, stdin loop, try/except, progress/success prints |
| `llm_client.py` | 169 | Health check, prompt assembly, single POST to /api/chat, strip fences, validate LaTeX |
| `resume_reader.py` | 8 | Read .tex file, raise FileNotFoundError if missing |
| `resume_writer.py` | 10 | Write timestamped .tex to output_dir, return Path |
| `config.py` | 9 | Constants: OLLAMA_BASE_URL, OLLAMA_MODEL, BASE_RESUME_PATH, OUTPUT_DIR, TIMEOUT |
| `log_manager.py` | 15 | Simple logger: info/warning/error to stderr |

Note: The milestone context mentioned `prompt_builder.py` but it does not exist. Prompt assembly lives inside `llm_client.py` as `_build_messages()`. No change needed to that boundary.

### New Modules Required (v1.1)

| Module | Responsibility | Why New (not extend existing) |
|--------|---------------|-------------------------------|
| `jd_analyzer.py` | Extract keywords from job description; score match against resume text | Pure text analysis, no HTTP — new concern, clean isolation |
| `output_guard.py` | Dropped-section check, hallucination check (new LaTeX environments/companies), format violation check | Post-LLM validation — distinct from `_validate_latex` which only checks doc structure |
| `diff_viewer.py` | Generate and print unified diff of original vs tailored to stdout | Display concern — no reason to put it in cli.py (keeps orchestrator readable) |

### Modified Modules (v1.1)

| Module | What Changes | Why Here |
|--------|-------------|----------|
| `llm_client.py` | Add `_build_analysis_messages()` for pass 1; add `analyze_job_description()` public function that returns `str` (analysis text); `generate_tailored_resume()` gains optional `analysis: str` parameter that injects analysis into user message | All LLM HTTP calls live here — adding pass 1 as a second public function maintains the raise-not-exit contract and is directly mockable in tests |
| `cli.py` | Add calls to `analyze_job_description()`, `check_output()`, `show_diff()` in the orchestration block; add two new progress messages; surface warnings from guards to stderr | Orchestrator owns the sequencing — all new steps plug in here |

---

## Two-Pass Pipeline Data Flow

```
[Disk: english.tex]
        |
        v
resume_reader.read_resume(path) -> resume_text: str
        |
cli.py collects job description via stdin -> job_description: str
        |
        v
[PASS 1 — Analysis]
llm_client.analyze_job_description(job_description, model) -> analysis: str
        |  POST /api/chat with analysis-focused system prompt
        |  Returns: "Key requirements: Python 3.11+, MLOps, Kubernetes, ..."
        |
        v  analysis: str
        |
[PASS 2 — Tailoring]
llm_client.generate_tailored_resume(resume_text, job_description, analysis, model) -> tailored_text: str
        |  POST /api/chat with tailoring system prompt
        |  User message now includes: <analysis>{analysis}</analysis> block
        |  Returns: full compilable LaTeX document
        |
        v  tailored_text: str
        |
[OUTPUT GUARDS — all stdlib, no LLM calls]
output_guard.check(resume_text, tailored_text) -> list[str] (warnings, may be empty)
        |  dropped_section_check: re.findall(r'\\\\section\{([^}]+)\}') on both
        |  hallucination_check: structural elements in tailored not in original
        |  format_violation_check: markdown fence detection, prose-before-documentclass
        |
        v  warnings: list[str]
        |
[DIFF VIEW — stdlib difflib]
diff_viewer.show(resume_text, tailored_text) -> None (prints to stdout)
        |  difflib.unified_diff(original_lines, tailored_lines, fromfile='original', tofile='tailored', lineterm='')
        |  Prints each line with +/- prefix; skipped if output is not a TTY
        |
        v
resume_writer.write_resume(tailored_text, output_dir) -> output_path: Path
        |
cli.py prints warnings (stderr), success message + path (stdout)
```

Key property: all data between modules is plain `str` or `list[str]`. No shared mutable state introduced.

---

## Where Each Feature Plugs into cli.py

The `main()` function in `cli.py` has a single `try` block. The new steps slot in sequence:

```python
# existing
resume_text = read_resume(resume_path)

# NEW: pass 1
print("Analyzing job description...", flush=True)
analysis = analyze_job_description(job_description, model=args.model)

# existing (signature change: add analysis param)
print("Tailoring resume — this may take a minute...", flush=True)
content = generate_tailored_resume(resume_text, job_description, analysis=analysis, model=args.model)

# NEW: output guards (before write)
warnings = check_output(resume_text, content)

# NEW: diff view (before write, after guards)
show_diff(resume_text, content)

# existing
output_path = write_resume(content, output_dir)

# NEW: surface warnings after path printed
print(f"Tailored resume written to: {output_path.resolve()}")
for w in warnings:
    print(f"Warning: {w}", file=sys.stderr)
```

The `except` block is unchanged — `analyze_job_description` raises the same `RuntimeError`/`ValueError` contract as `generate_tailored_resume`.

---

## Component Boundaries (v1.1)

### jd_analyzer.py

```python
def extract_keywords(job_description: str) -> list[str]
def score_match(keywords: list[str], resume_text: str) -> dict[str, bool]
def format_match_summary(scored: dict[str, bool]) -> str
```

- No imports outside stdlib (`re`, `collections`).
- `extract_keywords` uses `re.findall(r'\b[A-Za-z][A-Za-z0-9\+\#\.]*\b', jd)` filtered by a hard-coded stopword set. Tokens under 3 chars dropped. Case-normalized.
- `score_match` checks each keyword against `resume_text.lower()` — presence/absence only.
- `format_match_summary` returns a printable string (not printed itself — cli.py owns I/O).
- This module has no dependency on `llm_client.py` or HTTP.

### output_guard.py

```python
def check_output(original: str, tailored: str) -> list[str]
```

Single public function returns a (possibly empty) list of warning strings. Callers decide whether to print or raise. Three internal checks:

1. **Dropped sections:** `re.findall(r'\\\\section\{([^}]+)\}', text)` on both sides. Anything in original not in tailored → warning string.
2. **Hallucination check:** Extract structural markers that should be invariant — `\\subsection{}`, `\employer{}`, date patterns `\d{4}` adjacent to company-like text. New markers in tailored not in original → warning.
3. **Format violation:** If tailored contains ` ``` ` (markdown fence remnant) or has text before `\documentclass` → warning. This is distinct from `_validate_latex` which raises; guards warn without aborting.

Note: `_validate_latex` in `llm_client.py` stays as the hard abort guard (raises `ValueError`). `output_guard.check_output` is the soft-warning layer for things that compiled but look suspicious.

### diff_viewer.py

```python
def show_diff(original: str, tailored: str) -> None
```

- Calls `difflib.unified_diff(original.splitlines(keepends=True), tailored.splitlines(keepends=True), fromfile="original.tex", tofile="tailored.tex", lineterm="")`.
- Skips output if `not sys.stdout.isatty()` (piped output, CI environments).
- Optionally gate behind a `--diff` CLI flag (add to `cli.py` argparser) to avoid forcing diff on every run.
- Prints to stdout (not stderr) — it is informational output, not an error.

### llm_client.py changes

Two public functions instead of one:

```python
def analyze_job_description(job_description: str, model: str | None = None) -> str
def generate_tailored_resume(resume_text: str, job_description: str, analysis: str | None = None, model: str | None = None) -> str
```

`analyze_job_description` calls `_check_ollama_health()` then sends a focused analysis prompt:
- System: "You are a technical recruiter. Extract and list the top 10 technical requirements from this job description. Be concise and specific."
- User: `<job_description>{jd}</job_description>`
- Returns raw text (not LaTeX) — no fence stripping, no `_validate_latex`.

`generate_tailored_resume` gains optional `analysis: str | None`. If provided, the user message gains an `<analysis>` block before the resume. The existing `_build_messages` becomes `_build_tailoring_messages(resume_text, job_description, analysis)`.

The health check fires in `analyze_job_description` (first LLM call). `generate_tailored_resume` skips the duplicate health check — already known healthy from pass 1. Add a `skip_health_check: bool = False` internal param or just remove the health check from `generate_tailored_resume` since `analyze_job_description` always precedes it in the pipeline.

---

## Build Order (v1.1 phases)

Build in dependency order — leaf modules first, orchestrator changes last.

### Phase 1 — jd_analyzer.py (no deps)

Pure stdlib text module. No HTTP, no file I/O. Fully unit-testable with string fixtures. Build and test in isolation before touching any LLM code.

Deliverable: `extract_keywords`, `score_match`, `format_match_summary` all passing unit tests. `cli.py` not yet modified.

### Phase 2 — output_guard.py (no deps)

Pure stdlib regex module. Operates on two strings. Unit-testable with synthetic LaTeX fragments — no real LLM needed.

Deliverable: `check_output` returning correct warnings for dropped sections, hallucinated subsections, and fence remnants. `cli.py` not yet modified.

### Phase 3 — diff_viewer.py (depends on difflib only)

One function, easily tested by capturing stdout. Add `--diff` flag to `cli.py` argparser at this step (argparser change is trivial and doesn't break existing tests).

Deliverable: `show_diff` working. `--diff` flag parsed. Tests confirm diff output format.

### Phase 4 — llm_client.py two-pass extension

Add `analyze_job_description`. Extend `generate_tailored_resume` signature with `analysis` param. Update `_build_messages` -> `_build_tailoring_messages`. Existing 11 unit tests still pass (signature is backward-compatible: `analysis=None` preserves old behavior).

New tests: mock `analyze_job_description` to verify analysis text appears in tailoring user message; verify analysis-only call does not invoke `_validate_latex`.

Deliverable: both LLM functions working, tests green.

### Phase 5 — cli.py orchestration wiring

Wire all new modules into `main()`. Add progress messages. Add warning surfacing. Existing 5 cli tests still pass (they mock `generate_tailored_resume` — the new `analyze_job_description` call needs a mock too, add to test setup).

Deliverable: end-to-end pipeline working with two-pass LLM, guards, diff, and match summary.

---

## Error Handling: New Cases

| New Error | Where Raised | Who Catches | Behavior |
|-----------|-------------|-------------|----------|
| Pass 1 LLM failure | `analyze_job_description` raises `RuntimeError` | `cli.py` existing `except` block | Same as current: print to stderr, exit 1 |
| Guard warnings | `check_output` returns non-empty list | `cli.py` after write | Print each as `Warning:` to stderr, do NOT exit — output was written |
| Diff failure | `difflib` internal error | Not expected; difflib is pure Python, never raises on valid strings | N/A |
| Analysis empty/garbage | `analyze_job_description` returns unusable text | Not an exception; tailoring pass uses it as-is — model degrades gracefully | Consider: if analysis is under 20 chars, log a warning and proceed without it |

---

## Testing Strategy

### Unit Test Coverage Targets

| Module | Test File | What to Test |
|--------|-----------|--------------|
| `jd_analyzer.py` | `jd_analyzer_test.py` | keyword extraction from realistic JD text; score_match presence/absence; format_summary string format |
| `output_guard.py` | `output_guard_test.py` | dropped section detection; hallucinated subsection detection; fence remnant detection; clean pass returns empty list |
| `diff_viewer.py` | `diff_viewer_test.py` | verify stdout output contains +/- lines; verify no output when stdout not a tty |
| `llm_client.py` | `llm_client_test.py` (extend) | verify analysis request uses different system prompt; verify analysis injected into tailoring user message; backward compat (analysis=None) |
| `cli.py` | `cli_test.py` (extend) | verify `analyze_job_description` mocked and called; verify warnings printed to stderr; verify `--diff` flag parsed |

All mocking follows established pattern: `@patch('module.requests.post')` and `@patch('module.requests.get')`. New `jd_analyzer` and `output_guard` need no mocking — pure functions on strings.

---

## What NOT to Change

- `resume_reader.py` — no changes needed. It returns a string. v1.1 has no new file I/O requirements.
- `resume_writer.py` — no changes needed. It writes the tailored text. Guards warn before write but do not prevent it.
- `config.py` — no new constants needed for v1.1. Model and URL are already there. If a `SHOW_DIFF_DEFAULT` flag is desired, add `SHOW_DIFF: bool = False` here.
- `log_manager.py` — warnings from `output_guard` print via `print(..., file=sys.stderr)` directly in `cli.py`, consistent with the existing pattern. Do not route through `logger` — it adds indirection for no gain.

---

## Component Map (v1.1)

```
cli.py (orchestrator)
  ├── config.py                  (reads constants: paths, model, url)
  ├── resume_reader.py           (read_resume -> str)
  ├── llm_client.py              (analyze_job_description -> str, generate_tailored_resume -> str)
  ├── jd_analyzer.py             (extract_keywords, score_match, format_match_summary)
  ├── output_guard.py            (check_output -> list[str])
  ├── diff_viewer.py             (show_diff -> None)
  └── resume_writer.py           (write_resume -> Path)
```

`llm_client.py` still imports `config.py` for `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `TIMEOUT`.
`jd_analyzer.py`, `output_guard.py`, and `diff_viewer.py` import nothing outside stdlib.
No circular imports. No module except `cli.py` imports another project module.

---

## Sources

- Codebase inspection: `/workspace/src/` (all 7 modules read directly — HIGH confidence)
- Python stdlib `difflib.unified_diff`: verified signature and output format via runtime test
- Python stdlib `re` for LaTeX section extraction: verified regex pattern `r'\\\\section\{([^}]+)\}'` against real LaTeX string content
- Ollama `/api/chat` multi-message support: confirmed in existing `llm_client.py` implementation and Ollama API docs (https://github.com/ollama/ollama/blob/main/docs/api.md)
