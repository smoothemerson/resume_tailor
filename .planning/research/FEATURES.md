# Feature Landscape

**Domain:** Python CLI resume tailoring tool using local LLMs (Ollama)
**Researched:** 2026-05-28
**Project constraints:** stdlib + requests only, CLI only, no PDF compilation, no web server

---

## Table Stakes

Features that must exist for the tool to be usable at all. Missing any of these and the tool
either crashes, produces garbage, or requires manual intervention that defeats the purpose.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Read base `.tex` resume from configurable path | Without an input, there is nothing to tailor | Low | Path set in `config.py`; error if file missing |
| Accept job description via stdin (multiline, sentinel-terminated) | The tool has no value without a target JD; terminal input is the only interface | Low | `END` sentinel is idiomatic for multiline CLI input |
| Call Ollama REST API (`/api/generate` or `/api/chat`) | The LLM call is the entire value proposition | Low | `requests.post` to `localhost:11434`; no SDK needed |
| System prompt that preserves LaTeX structure | Without this, the model may strip environments, change commands, or emit markdown | Medium | Prompt must forbid markdown fences, require valid `.tex` output |
| Prompt instructs model not to hallucinate new experiences | Core trust requirement — output must be honest reframing, not fabrication | Medium | "Do not invent new roles, employers, or dates" must be explicit in prompt |
| Write output to timestamped `.tex` file (`resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex`) | Prevents overwrites; preserves history without a database | Low | `datetime.now()` formatting in stdlib |
| Print output file path on success | Without this the user doesn't know where to find the result | Low | One `print()` call after write |
| Explicit error on file-not-found | Silent failure or stack trace is unusable for a portfolio tool | Low | Check existence before open; print clear message |
| Explicit error on Ollama connection failure | Ollama not running is the most common failure mode | Low | Catch `requests.ConnectionError`; print actionable message ("Is Ollama running?") |
| Model and file paths configurable via `config.py` | Without this, changing the model requires editing business logic | Low | A flat `config.py` with constants is sufficient |

---

## Differentiators

Features that are not expected by default but make this tool genuinely better — and
make it a stronger portfolio piece demonstrating LLM engineering judgment.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Diff output to terminal (base vs tailored) | Lets the user immediately audit what changed without opening two files; demonstrates safety-first LLM tooling | Medium | Unified diff via `difflib.unified_diff` (stdlib); works on raw `.tex` lines |
| Section-aware prompt decomposition | Tailoring skills differently from bullet points from summary produces higher-quality output than treating the resume as a blob | High | Requires parsing LaTeX sections; adds significant prompt engineering complexity; defer to v2 unless base model quality is poor |
| Streaming output with progress indicator | Shows the model is running rather than hanging; makes the tool feel responsive | Medium | Ollama `/api/generate` supports `stream: true`; requires chunked response handling |
| `--dry-run` flag | Renders the prompt that would be sent without calling the API; invaluable for prompt debugging | Low | Conditional branch before `requests.post`; zero extra deps |
| Configurable output directory via CLI flag | Lets the user point output to a project-specific folder per application | Low | `argparse` with `--output-dir`; already using stdlib |
| Verbose / debug logging of request/response | Shows token counts, latency, model used; useful for tuning model choice | Low | `--verbose` flag that prints request body and response metadata |
| Input validation: warn if JD is below minimum length | Very short JDs produce poor tailoring; catching this early saves a wasted LLM call | Low | Word count check before API call; configurable threshold |
| Prompt template externalized to a file | Allows prompt iteration without touching Python code; demonstrates prompt-as-config pattern | Low | Load from `prompts/system_prompt.txt`; fallback to hardcoded default |
| Model availability check on startup | Fails fast with a clear error if the configured model isn't pulled yet, before sending the resume | Low | `GET /api/tags` to Ollama; check model name in response |

---

## Anti-Features (v1)

Things to deliberately NOT build in the first version. Each has a reason.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| PDF compilation (`pdflatex` subprocess) | Adds OS-level dependency (LaTeX distribution), error surface, and scope; user already has LaTeX toolchain | Print the output `.tex` path; user runs `pdflatex` themselves |
| Web server or API endpoint | Contradicts the personal CLI tool framing; adds networking security surface and dep weight | Stay as a subprocess-invocable script |
| LangChain / LlamaIndex / any LLM framework | Obscures the actual API call behind abstraction; makes the portfolio piece look like template usage rather than engineering | Direct `requests.post` to Ollama REST API |
| Multi-resume management (resume registry, base switching) | The user has one base resume; managing multiple is a different product | Single `BASE_RESUME_PATH` in `config.py` |
| GUI or TUI (curses, rich interactive mode) | Adds rendering complexity with no value for a personal tool; `rich` for static output is fine | Plain terminal output; `print()` is sufficient |
| Automatic git commit of output | Side effects on the user's repo without explicit intent; unexpected behavior is a trust issue for any tool | User controls version control |
| Cover letter generation | Separate document type with different structure and tone requirements; orthogonal problem | Separate tool if needed later |
| Job description fetching from URL | Adds HTTP complexity, HTML parsing, robots.txt considerations | User pastes JD text directly |
| Database / history tracking | Overkill for personal use; timestamped filenames are the history | Filesystem is the history |
| Resume scoring / ATS simulation | Requires ATS-specific data that is proprietary and changes constantly; false precision | Trust model quality + user judgment |
| Interactive editing loop (accept/reject/regenerate per section) | High complexity; requires section parsing + state machine | User reruns the tool if output is unsatisfactory |

---

## Feature Dependencies

```
Accept JD via stdin
    └── Call Ollama API
            └── System prompt (LaTeX preservation + no-hallucination)
                    └── Write timestamped .tex output
                            └── Print output path on success

Read base .tex file
    └── Call Ollama API (resume text is part of prompt)

Model configurable in config.py
    └── Call Ollama API (model name passed in request body)
    └── Model availability check on startup [DIFFERENTIATOR]

Explicit error handling (file-not-found, connection failure)
    └── (no downstream deps; wraps all IO operations)

--dry-run flag [DIFFERENTIATOR]
    └── Depends on: prompt construction being isolated into a function
        (i.e. prompt must be buildable without calling the API)

Diff output to terminal [DIFFERENTIATOR]
    └── Depends on: base .tex read + tailored .tex write both completing

Streaming output [DIFFERENTIATOR]
    └── Depends on: Ollama API call (replaces blocking .post with streamed response)
        └── Incompatible with: simple response capture for diff
            (diff requires full output; streaming and diff need coordination)

Prompt template externalized [DIFFERENTIATOR]
    └── No hard dependencies; drops in as a replacement for hardcoded string

Input validation (JD length) [DIFFERENTIATOR]
    └── Depends on: JD input; runs before API call
```

**Critical ordering note for v1:** The table stakes features have a strict linear dependency —
file read and JD input must both succeed before the API call is made, and the API call must
complete before the output is written. Error handling wraps each boundary. Build in that order.

**Differentiator ordering for v2+:** `--dry-run` and prompt externalization are both low
complexity and high leverage for prompt iteration — implement these first among differentiators.
Diff output is the most visible portfolio differentiator. Streaming conflicts with diff capture
and should be a separate mode or deferred.

---

## Sources

- Project context: `.planning/PROJECT.md` (HIGH confidence — canonical source)
- Ollama REST API surface: training knowledge + Ollama public docs patterns (MEDIUM confidence)
- LaTeX preservation prompt requirements: established LLM prompting patterns for structured formats (MEDIUM confidence)
- CLI tool UX conventions (`--dry-run`, `--verbose`, sentinel input): Python CLI ecosystem standards (HIGH confidence)
- Anti-feature rationale: derived from project constraints document (HIGH confidence)
