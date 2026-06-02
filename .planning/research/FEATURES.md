# Feature Research

**Domain:** Python CLI resume tailoring tool — v1.1 Output Quality Features
**Researched:** 2026-06-02
**Confidence:** HIGH (stdlib capabilities verified via Python interpreter; architectural analysis derived from existing codebase)

---

## Scope

This document covers the four v1.1 target features only. The v1.0 table stakes (LLM call, file I/O,
fence stripping, LaTeX validation, timestamped output) are already shipped and excluded.

Target features:
1. Diff view between original and tailored resume
2. JD keyword match summary
3. Two-pass LLM pipeline (JD extraction pass, then tailoring pass)
4. Output reliability guards (hallucination detection, dropped-section check, format violations)

---

## Feature Landscape

### Table Stakes (Users Expect These)

For a tool that modifies a document, these output quality signals are the minimum a user
needs to trust the output without manually diffing two `.tex` files themselves.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Diff view (original vs tailored) | User cannot trust LLM output without seeing what changed; opening two files in an editor defeats CLI convenience | LOW | `difflib.unified_diff` is stdlib; ANSI color lines by prefix (red/green); ~20 lines total. Input already available in `cli.py`: `resume_text` before call, `content` after. |
| Dropped section detection | A resume missing the Education or Experience section is a hard failure; must be caught before writing | LOW | `re.findall(r'\\(?:section|subsection)\{([^}]+)\}', text)` on both documents; diff the sets; warn on any in original but not in tailored. |
| Format violation warnings | Markdown headers/bullets inside the LaTeX body mean the model ignored the LaTeX-only constraint; fences that survive stripping are the same class of failure | LOW | Regex on the document body between `\begin{document}` and `\end{document}`: detect `^# `, `^- `, and surviving backtick fences. Prose after `\end{document}` is already caught by `_validate_latex`. |
| Hallucination warnings (new proper nouns) | New capitalized tokens (company names, tools, institutions, certifications) not in the original are the highest-signal hallucination indicators | MEDIUM | Extract capitalized token sets from original and tailored; warn on tokens present in tailored but absent in original. Imperfect (LaTeX macro names are noise) but zero deps and catches real failures. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Two-pass LLM pipeline (extract then tailor) | Pass 1 extracts structured JD data (role title, key skills, domain keywords, seniority) as JSON. Pass 2 receives that JSON as explicit context for the tailoring prompt, producing more targeted rewrites than a single prompt that must infer requirements inline. | MEDIUM | Two sequential `requests.post` calls to `/api/chat`. Pass 1 asks for JSON only; parse with `json.loads()`. Pass 2 injects the parsed data into the existing system prompt. Risk: local models often fail at strict JSON output — must have a graceful fallback (treat JD as raw text if JSON parse fails). |
| JD keyword match summary | After tailoring, report which extracted keywords appear in the tailored output and which are missing. Gives the user a signal on whether the LLM actually incorporated the JD requirements. | LOW | Requires two-pass for best quality (pass 1 provides clean keyword list). Without two-pass, a regex fallback (`\b[A-Z]{2,}\b` and camelCase patterns) works but is noisier. Match by case-insensitive substring against tailored text. |
| `--no-diff` flag to suppress diff output | Once trusted, a user may want clean output; the diff is verbose for long resumes | LOW | `argparse` boolean flag; already using `argparse` in `cli.py`. Default is diff-on for new installs. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| HTML diff output (`difflib.HtmlDiff`) | Side-by-side visual diff is easier to read | Requires writing a file, opening a browser, platform-specific shell commands; more surface than a CLI needs | Unified diff in terminal with ANSI color; same signal, zero complexity |
| Percentage "ATS score" | Sounds like actionable signal | Single number is gameable, misleading, and creates false precision; ATS algorithms are proprietary and change constantly | Show matched/missing keyword lists; let user judge relevance |
| Semantic similarity via embeddings | More accurate than keyword matching | Requires `sentence-transformers` or similar; violates the stdlib+requests constraint and adds ~500MB model download | LLM-extracted keyword list from pass 1 is higher signal than regex and needs no extra dep |
| Blocking execution on hallucination | "If hallucination detected, abort" seems safe | Too aggressive; proper noun detection has false positives (LaTeX macros, template names). Blocking on a false positive is worse than the hallucination it prevented. | Warn to stderr; let user decide; the diff is already showing all changes |
| Auto-fix hallucinations (third pass) | Sounds like a reliability improvement | A third LLM call to "remove" detected hallucinations can introduce new ones; creates a correction loop with no convergence guarantee | Users are the correction loop: diff + warning makes the problem visible |
| NLP entity recognition (spaCy/NLTK) | More accurate hallucination detection | Adds a heavy dep for marginal improvement over capitalized-token diff | Regex-based token diff; flag as heuristic in output message |
| Streaming both LLM passes | Makes tool feel responsive during 2x latency | Streaming and diff capture conflict: diff requires the full output before it can run. Adds complexity for no real gain in a sequential pipeline. | Block on both calls; print progress message before each pass |
| Caching pass-1 results | Saves one LLM call when re-running on same JD | Each run is a different application; JDs are rarely reused; cache invalidation adds complexity for personal use | No cache; always run both passes fresh |
| Three-pass pipeline (parse resume too) | Structured resume data might improve tailoring | Resume is already structured LaTeX; the model reads it directly; parsing it adds a pass and latency without meaningful benefit | Two-pass is sufficient; pass 2 receives the raw LaTeX directly |

---

## Feature Dependencies

```
[Output Reliability Guards]          [Diff View]
  dropped-section detection            difflib.unified_diff + ANSI
  format violation detection           Input: resume_text (already in cli.py)
  hallucination detection              Input: content (returned by llm_client)
  All: post-processing after           Output: printed to stdout
  generate_tailored_resume()           Independence: FULL (zero deps on other features)
  Independence: FULL

[Two-Pass Pipeline]
    └──enables──> [JD Keyword Match Summary]
                  Pass 1 JSON contains clean keyword list
                  Without two-pass: fallback to regex (lower quality)

[Two-Pass Pipeline]
    architecture change to llm_client.py:
    extract_jd_requirements(jd_text) -> dict
    generate_tailored_resume(resume, jd_text, jd_data) -> str
    cli.py threads jd_data through the call

[JD Keyword Match Summary] ──uses──> [Two-Pass Pipeline output]
    Fallback: regex if two-pass disabled/fails
```

### Dependency Notes

- **Output reliability guards have no inter-dependencies:** Each guard (dropped sections, format violations, hallucination detection) is a pure function taking `(original_text, tailored_text)` or just `tailored_text`. All can be added to `cli.py` as post-processing calls after `generate_tailored_resume()` returns. Build these first.

- **Diff view has no inter-dependencies:** `resume_text` is already read in `cli.py` before the LLM call; `content` is already returned by `generate_tailored_resume()`. The diff runs between those two values with one `difflib` call. No module restructuring needed.

- **Two-pass pipeline requires `llm_client.py` restructuring:** Currently `generate_tailored_resume()` is one function. Two-pass requires splitting into `extract_jd_requirements()` (pass 1) and `generate_tailored_resume()` (pass 2, receives `jd_data` dict). `cli.py` must thread the pass-1 result forward. This is the only architectural change in v1.1.

- **JD keyword match summary depends on two-pass for best quality:** Without pass 1's clean keyword list, keyword matching degrades to a regex heuristic (acceptable, but noisier). Implementing keyword summary before two-pass is feasible as a fallback; implementing it after two-pass enables the clean version without rework.

- **Hallucination detection and two-pass are independent:** The guards compare original and tailored LaTeX using string operations. They are not informed by pass-1 results. They should not be: the guard is a safety net that operates independently of what the LLM claims to know about the JD.

---

## MVP Definition

### Launch With (v1.1)

All four features per PROJECT.md requirements. Build order optimized for independence:

- [ ] Output reliability guards (new `output_guards.py` module, ~55 LOC) — zero deps, zero arch change, maximum safety signal per line of code
- [ ] Diff view (new `diff_view.py` or inline in `cli.py`, ~20 LOC) — zero deps, zero arch change, directly addresses "what changed"
- [ ] Two-pass LLM pipeline (refactor `llm_client.py`, ~25 LOC delta) — architectural change, enables next item
- [ ] JD keyword match summary (~20 LOC consuming pass-1 output) — depends on two-pass, completes the feedback loop

### Defer (v1.2+)

- `--no-diff` flag — useful once tool is trusted; trivial to add later
- Persistent keyword history across runs — requires state management, not a CLI pattern
- Interactive accept/reject per section — requires TUI, contradicts minimal-dep constraint

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Dropped section detection | HIGH (catches hard failures) | LOW (regex only) | P1 |
| Format violation warnings | HIGH (catches LaTeX-breaking output) | LOW (regex only) | P1 |
| Diff view | HIGH (primary audit mechanism) | LOW (difflib stdlib) | P1 |
| Hallucination warnings | MEDIUM (heuristic, false positives exist) | LOW (token set diff) | P1 |
| Two-pass pipeline | MEDIUM (better tailoring quality) | MEDIUM (arch change + JSON parsing) | P2 |
| JD keyword match summary | MEDIUM (actionable feedback post-tailoring) | LOW (depends on two-pass) | P2 |

**Priority key:** P1 = zero new deps, zero arch change, add before next commit. P2 = requires `llm_client.py` refactor, build after P1 guards are stable.

---

## Existing Architecture Integration

All four features integrate with the existing codebase without introducing new dependencies.

| Feature | New File | Modified File | Integration Point |
|---------|----------|---------------|-------------------|
| Dropped section detection | `output_guards.py` | `cli.py` | After `generate_tailored_resume()` returns; before `write_resume()` |
| Format violations | `output_guards.py` | `cli.py` | Same as above |
| Hallucination warnings | `output_guards.py` | `cli.py` | Same as above |
| Diff view | `diff_view.py` | `cli.py` | After `write_resume()`; pass `resume_text` and `content` |
| Two-pass pipeline | none | `llm_client.py`, `cli.py` | `extract_jd_requirements()` called before `generate_tailored_resume()`; `jd_data` threaded forward |
| JD keyword match summary | `jd_keywords.py` | `cli.py` | After tailoring; pass `jd_data['key_skills']` and `content` |

**No new PyPI packages required.** All guards use `re` (stdlib). Diff uses `difflib` (stdlib). JSON parsing uses `json` (stdlib). The two-pass pipeline makes one additional `requests.post` call — same code path, different prompt.

---

## Sources

- Python `difflib` module documentation verified via interpreter (`help(difflib.unified_diff)`) — HIGH confidence
- ANSI color diff pattern: [Print colored visual diff in Python — GitHub Gist by @ines](https://gist.github.com/ines/04b47597eb9d011ade5e77a068389521) — MEDIUM confidence
- Two-pass extract-then-generate pattern: [ResumeFlow: An LLM-facilitated Pipeline — arXiv 2402.06221](https://arxiv.org/abs/2402.06221) — MEDIUM confidence (academic; validates pattern, not implementation)
- LaTeX section regex and token extraction verified via Python interpreter — HIGH confidence
- Hallucination guard approach (warn, not block): derived from analysis of local model false-positive rates and project's existing "raise not exit" philosophy — HIGH confidence (internal consistency)
- Existing codebase: `/workspace/src/llm_client.py`, `/workspace/src/cli.py` — HIGH confidence

---

*Feature research for: Resume Tailor CLI v1.1 Output Quality*
*Researched: 2026-06-02*
