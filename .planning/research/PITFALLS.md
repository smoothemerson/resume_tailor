# Pitfalls Research

**Domain:** Python CLI tool — output quality features for LaTeX resume tailoring via local Ollama LLM
**Researched:** 2026-06-02
**Confidence:** HIGH for LaTeX diff and two-pass LLM pitfalls (grounded in difflib behavior, Ollama API, and known LLM output patterns); MEDIUM for keyword scoring and hallucination detection (heuristic approaches vary, limited authoritative sources for stdlib-only constraints)

---

## Scope

This document covers pitfalls specific to **v1.1 output quality features** being added to an existing single-pass pipeline:

1. LaTeX diff view using `difflib`
2. JD keyword match scoring
3. Two-pass Ollama pipeline (analysis pass + tailoring pass)
4. Programmatic hallucination and dropped-section detection

Pitfalls from v1.0 (markdown fences, timeout hangs, context truncation, encoding, etc.) are documented in the original PITFALLS.md. This file extends that document — do not re-implement the same guards.

---

## Critical Pitfalls

### Pitfall 1: LaTeX Diff Drowns in Whitespace and Formatting Noise

**What goes wrong:**
`difflib.unified_diff()` operates on lines. LaTeX files have significant semantic content in whitespace: `\vspace*{-9pt}`, indented macro arguments, empty lines between environments, and wrapped long lines. The LLM almost certainly reformats indentation and whitespace throughout the document even when instructed not to. A naive line-level diff shows hundreds of "changed" lines when only three bullet points changed substantively. The output is unreadable noise that obscures real changes.

Example: the existing `english.tex` uses `\newcommand{\employer}[3]` with multi-line argument indentation. A model that reformats to single-line or re-wraps at 80 characters generates a diff that looks like every line changed.

**Why it happens:**
Developers reach for `difflib.unified_diff(original.splitlines(), tailored.splitlines())` because it is the obvious stdlib approach. It treats every line as equal weight. LaTeX structural whitespace and content text are indistinguishable at the line level.

**How to avoid:**
1. Normalize both sides before diffing: strip trailing whitespace from each line with `line.rstrip()`, collapse runs of blank lines to a single blank, before splitting into lines. Do not strip leading whitespace — indentation can be semantically meaningful in some LaTeX environments.
2. Filter the diff output: only display changed lines that contain actual text tokens — lines matching `r'\w'` — and skip lines whose only change is whitespace rearrangement. A line that changed from `    text` to `  text` is structural noise.
3. Consider a two-step filter: first strip-and-compare to detect whether changes are purely whitespace; if so, skip that hunk entirely. If the hunk contains non-whitespace deltas, include it.
4. Show a summary count first: "N lines changed" before the full diff. If N is large, warn the user that reformatting occurred.

**Warning signs:**
- Running `difflib.unified_diff` on the raw original and raw output shows 50+ changed lines on a 149-line resume.
- Every `\vspace` or custom command argument appears as a changed line.
- The diff is longer than the resume itself.

**Phase to address:** Phase implementing the diff view. Normalize before diffing; do not defer normalization to a later phase.

---

### Pitfall 2: JD Keyword Scoring Is Gamed by Repetition and Substrings

**What goes wrong:**
A naive keyword scorer splits the JD by whitespace, deduplicates into a set, then counts how many tokens appear in the tailored resume. This fails in multiple ways:

- **Substring false positives**: "Python" matches inside "CPython", "IronPython", and "pythonic". "ML" matches inside "XML". Simple `in` membership on string produces wrong counts.
- **Case mismatch**: "kubernetes" in the JD, "Kubernetes" in the resume — missed unless lowercased on both sides.
- **Stop word noise**: The JD contains "the", "and", "our", "team", "you", "will", "be" — all high-frequency tokens that appear everywhere and inflate the score artificially.
- **Abbreviation explosion**: "CI/CD" tokenizes as "CI/CD", "CI", "CD" depending on the tokenizer. "Machine Learning" and "ML" are treated as unrelated tokens. The resume that uses "ML" when the JD uses "Machine Learning" scores zero on that keyword even though they are semantically identical.
- **Over-counting multiplicity**: Counting raw occurrences rather than presence means "Python" appearing 10 times in the JD counts as 10 matches, inflating the denominator.

The result is a score that looks precise (e.g., "72% keyword match") but is meaningless because stop words dominate the numerator and substring matches create false positives.

**Why it happens:**
Keyword scoring feels simple. The first implementation naturally reaches for `set(jd.split())` and `sum(1 for kw in kw_set if kw in resume)`. The tests pass on obvious inputs but the score is wrong in practice.

**How to avoid:**
1. Use a hardcoded stop word list. The NLTK stop word list is not available (project is stdlib + requests). Maintain a minimal list of 30-50 English stop words relevant to job descriptions: `{"the", "and", "or", "a", "an", "in", "of", "to", "for", "with", "is", "are", "will", "be", "as", "at", "by", "on", "we", "our", "you", "your", "this", "that", "have", "from", "not", "but", "it"}`. Filter these out before building the keyword set.
2. Use whole-word matching: `re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE)` rather than `keyword in resume_text`. This eliminates substring false positives.
3. Normalize before tokenizing: lowercase both JD and resume, replace `/` with space, strip punctuation at token boundaries. This catches "CI/CD" → ["ci", "cd"] matching "ci" and "cd" in resume.
4. Deduplicate at keyword level, not occurrence level: build `{keyword: bool}` presence, not `{keyword: count}`. Score = matched / total unique meaningful keywords.
5. Keep multi-word phrases: extract 2-grams from the JD keyword list ("machine learning", "deep learning", "software engineer") so that phrase-level terms are tested as units, not exploded into individual tokens that match anywhere.
6. Report the keyword list shown to the user — make the scoring transparent. Print "Keywords extracted: [Python, Kubernetes, MLOps, ...]" so the user can see what was scored and judge the output quality themselves.

**Warning signs:**
- Score above 90% on an untailored resume against any JD (stop words inflating score).
- "ML" and "Machine Learning" both in the JD, resume uses one of them, score shows 50% match on that domain.
- Score changes drastically when the JD is copy-pasted with vs. without trailing punctuation.

**Phase to address:** Phase implementing the keyword scorer. Write a test with a known minimal JD ("Python developer with experience in Kubernetes and CI/CD") and a known resume, and verify the score reflects only meaningful tokens.

---

### Pitfall 3: The Analysis Pass Returns Unstructured Text That the Tailoring Pass Ignores

**What goes wrong:**
The two-pass design has the first Ollama call analyse the JD and return key requirements, then feeds that analysis as context to the second (tailoring) call. The most common failure: the analysis pass returns free-form prose ("The job emphasizes Python, distributed systems, and leadership...") that is simply appended to the tailoring prompt. The tailoring model receives a long context it was not specifically prompted to use, and either ignores the analysis section or blends it inconsistently with the original instructions.

The analysis output is unstructured, variable-length, and unpredictable. Sometimes it returns 3 bullet points. Sometimes it returns 500 words. Sometimes it returns JSON. Sometimes it writes a cover letter.

**Why it happens:**
The natural instinct is to run the analysis pass with a vague prompt ("analyse this job description and tell me the key requirements") and then concatenate the result into the tailoring prompt. There is no contract between the two passes.

**How to avoid:**
1. Define a strict output contract for the analysis pass. Prompt the model to return a structured list — use XML-delimited format since this is already the pattern in the existing system prompt: `<keywords>Python, Kubernetes, MLOps</keywords><seniority>Senior</seniority><domain>distributed systems</domain>`. Validate that the output matches this structure before passing it downstream.
2. If the analysis response does not contain the expected structure (missing XML tags), do not abort — fall back to the single-pass approach with a warning: "Analysis pass returned unexpected format, proceeding with single-pass tailoring."
3. Keep the analysis prompt minimal and deterministic. "Return ONLY a comma-separated list of technical keywords from this job description. No prose, no explanation." is more reliable than "tell me the key requirements."
4. Cap the analysis output. The tailoring prompt is already large (full resume + JD + system prompt ≈ 3500-5000 tokens). Adding 500 tokens of analysis prose risks hitting the 8192 `num_ctx` limit. Budget the analysis output to under 200 tokens.
5. Structure the tailoring prompt to use the analysis output explicitly: "The following keywords were extracted from the job description. Prioritize surfacing these in the tailored resume: {extracted_keywords}." This makes the analysis an injection point, not background context.

**Warning signs:**
- Analysis pass output varies wildly in length between runs (50 words vs. 500 words).
- Tailored output quality is identical whether the analysis pass ran or not (analysis is being ignored).
- Total prompt token count exceeds the `num_ctx` budget, triggering `done_reason: length` on the second call.

**Phase to address:** Phase implementing the two-pass pipeline. The output contract of pass 1 must be defined before pass 2 is written — not retrofitted.

---

### Pitfall 4: Two Serial Ollama Calls Double Latency Without Consistent Timeout Handling

**What goes wrong:**
The existing pipeline has one Ollama call with a `(10, 300)` timeout. Adding a second serial call doubles worst-case latency to 600 seconds. The health check at startup covers the first call but not the state of Ollama mid-pipeline. Between the two calls, Ollama may unload the model from memory (default `OLLAMA_KEEP_ALIVE` is 5 minutes, but with local hardware, the first generation may exhaust VRAM and the second call triggers a reload).

If the first call succeeds but the second call fails (timeout, OOM, model reload delay), the tool exits with a RuntimeError but has not written any output. The user spent 3 minutes and got nothing. No partial output, no way to retry just the tailoring pass.

**Why it happens:**
Two-call error handling is often copy-pasted from the single-call pattern without considering what "partial success" means. The first call is the analysis pass; its output has no user value on its own. If the second call fails, the entire run is wasted.

**How to avoid:**
1. Apply the same timeout tuple `(connect_timeout, read_timeout)` to both calls. Use the same constant from `config.py` — do not hardcode a different timeout for the analysis pass.
2. Re-run the health check between calls only if the first call took over 60 seconds (possible model reload was triggered). Otherwise skip it — the overhead of an extra GET is negligible but unnecessary on fast hardware.
3. Log (print to stderr) elapsed time after the first call: "Analysis complete (12.4s), starting tailoring pass..." This tells the user the pipeline is progressing, not hung.
4. Wrap both calls in the same try/except block at the `cli.py` boundary. The error message should distinguish which pass failed: "Tailoring pass failed after analysis completed — try increasing TIMEOUT in config.py."
5. Do not cache the analysis output to disk between calls. The pipeline is short-lived; caching adds complexity and the analysis result has no standalone use.

**Warning signs:**
- Second call times out more often than the first (model was evicted after first call's long generation).
- No progress message between calls — user cannot distinguish "analysis running" from "hung."
- Timeout error message does not say which pass failed.

**Phase to address:** Phase implementing the two-pass pipeline. Timeout and progress output must be designed into the two-call structure, not added after.

---

### Pitfall 5: Dropped-Section Detection Misidentifies Custom LaTeX Macros as Section Headers

**What goes wrong:**
The resume uses `\header{Experience}` rather than `\section{Experience}`. A naive dropped-section check that scans for `\section{...}` patterns will find zero sections in the original and conclude that all sections are "present" in the output (vacuously true). Meanwhile, a model that drops the `\header{Languages}` block goes undetected.

Alternatively, if the checker is written to look for `\header{...}`, it works for this specific resume template but silently breaks for any other resume that uses `\section{}` or a different macro. The checker becomes template-specific without being documented as such.

**Why it happens:**
Developers write dropped-section detection against the known resume structure during development, test it on `english.tex`, and mark it as working. The assumption that the resume uses `\section{}` is baked in silently.

**How to avoid:**
1. Extract section headers from the original resume dynamically, not from a hardcoded list. Scan the original for both `\section{...}` and `\header{...}` and any other macro call that appears to introduce a section (heuristic: macro on its own line, argument is a short capitalized phrase like "Experience", "Skills", "Education").
2. Build the expected section list from the original at runtime: `re.findall(r'\\(?:section|header|subsection)\{([^}]+)\}', original_text)`. This returns `["Experience", "Projects", "Skills", "Education", "Languages"]` from `english.tex`.
3. Check the tailored output against the same set of section names using case-insensitive comparison. A section is "dropped" if its name does not appear anywhere in the tailored output at all (even as text, not just as a macro argument).
4. Warn, do not abort. A warning like "Warning: section 'Languages' not found in tailored output — verify before compiling" is appropriate. Aborting on a false positive would be worse than missing a true positive.
5. Document that the section detector is heuristic-based and cannot catch sections that the model renamed (e.g., "Experience" → "Work Experience").

**Warning signs:**
- Dropped-section check returns "all sections present" on a clearly broken output.
- Check hard-codes `["Experience", "Skills", "Education"]` rather than extracting from original.
- Check breaks silently when run against a resume that uses `\section{}` instead of `\header{}`.

**Phase to address:** Phase implementing output reliability guards. Extract section list from the original before comparing — never hardcode.

---

### Pitfall 6: Hallucination Detection Flags Legitimate Rewrites as New Content

**What goes wrong:**
Hallucination detection via string-level comparison between original and output will produce false positives because the prompt explicitly instructs the model to rewrite bullet points. A bullet that was:

```
Developed ML pipelines for fraud detection
```

and becomes:

```
Built end-to-end machine learning pipelines for real-time fraud detection and risk scoring
```

contains the new tokens "end-to-end", "real-time", and "risk scoring". A naive detector that checks whether every word in the output exists in the original will flag this as hallucination. The feature will fire on almost every tailoring run, destroying user trust in the warning.

**Why it happens:**
Hallucination detection for LLM output is an unsolved research problem at the semantic level. The tempting implementation is string set difference: words in output not in original = hallucinated. This conflates rewriting (acceptable) with invention (not acceptable). The project constraint is to detect *fabricated facts* (new companies, dates, titles, credentials, skills not in original), not new phrasing.

**How to avoid:**
1. Define exactly what the hallucination checker is looking for. For this project, the specific risks are: new company names, new job titles, new employment dates, new certification names, new skill tokens that appear in the skills section but not in the original. Not: new adjectives, new connecting words, rephrased bullet text.
2. Limit detection to structured fields. Extract: company names (lines matching `\employer{...}` macro), employment dates (4-digit year patterns), certification tokens (lines in the skills section). Compare these specific fields between original and output. Do not compare running prose.
3. For skills section hallucination: extract the skills listed under `\header{Skills}` in the original, then check whether any tokens in the output skills section are absent from the original skills section AND absent from the full job description. A skill absent from both original and JD is a hallucination candidate.
4. Accept false negative risk over false positive risk. A false negative (missed hallucination, user reviews) is recoverable. A false positive (legitimate rewrite flagged as hallucination) destroys trust in the feature and causes users to ignore all warnings.
5. Label the warning accurately: "Possible new content detected: [token] — verify this was in your original resume." Do not write "hallucination detected" which implies certainty.

**Warning signs:**
- Hallucination checker fires on every single run with legitimate output.
- Checker flags rewritten bullet words ("accelerated", "streamlined", "cross-functional") as new content.
- False positive rate above 50% in informal testing means the feature is useless.

**Phase to address:** Phase implementing output reliability guards. Write a test that runs the checker against a known-good rewrite and confirms zero false positives before shipping.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode expected sections ["Experience", "Skills", "Education"] | Ships fast, works for current resume | Silently breaks for any other resume structure; brittle | Never — extract from original at runtime, costs 2 lines |
| Use `word in resume_text` for keyword scoring | One line, obvious | Substring false positives ("ML" in "XML"); wrong scores | Never — use `\bword\b` regex, costs 1 line |
| Run analysis pass but don't validate its output format | Ships the two-pass pipeline faster | Analysis pass garbage propagates into tailoring prompt undetected; quality degrades silently | Never — add a 3-line check for expected XML tags |
| Show raw `difflib.unified_diff()` output | No extra code | Whitespace noise makes diff unreadable; user ignores the feature | Never — normalize before diffing, costs 5 lines |
| Use `words_in_output - words_in_original` as hallucination signal | Simple set operation | False positive on every rewritten bullet; feature is noise | Never — scope detection to structured fields only |
| Duplicate health check call at start of two-pass | Defensive, feels safe | Adds connect latency before both calls; wastes 200ms | Acceptable only if second call follows the first by >5 minutes (unlikely in practice) |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `difflib.unified_diff` | Passing raw `.splitlines()` including trailing whitespace | Normalize with `[line.rstrip() for line in text.splitlines()]` before passing to `unified_diff` |
| `difflib.unified_diff` | Forgetting `lineterm=""` parameter | Set `lineterm=""` or output lines carry embedded newlines and print double-spaced |
| Two Ollama calls in sequence | Using a single flat `try/except` that can't distinguish which call failed | Wrap each call separately; error messages should name the failing pass |
| Analysis pass output | Passing raw analysis string into tailoring prompt without structure | Use XML delimiters; extract `<keywords>` tag content before injecting |
| Ollama second call after long first call | Model may be evicted from VRAM between calls | Print elapsed time between calls; use same `(10, 300)` timeout tuple — do not tighten timeout for "analysis" call just because it's shorter |
| Keyword set construction | `set(jd.split())` tokenizes on spaces only; does not handle `Python,` vs `Python` | Strip punctuation from token boundaries: `re.findall(r'\b\w[\w+#.-]*\b', jd.lower())` |
| Section regex | `r'\\section\{([^}]+)\}'` only matches `\section` | Use `r'\\(?:section|subsection|header)\{([^}]+)\}'` to cover custom macros; extend as needed |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Two serial Ollama calls with no progress output | User sees no feedback for 3-6 minutes; kills process | Print "Analysis complete (Xs)" between calls | Every run when model is cold-loaded |
| Analysis pass prompt includes full resume + full JD | Analysis call consumes 3000+ tokens; leaves little headroom for tailoring pass context | Truncate or summarize JD before analysis pass if over 2000 tokens | When JD is pasted from a verbose multi-page posting |
| Diff computed on original + output without normalization | Diff takes O(n²) time on long sequences with many matches | Difflib is fast enough for a 149-line resume; not a real perf risk at this scale | Not a trap at this scale — note for documentation only |
| Keyword scorer iterates full resume string per keyword | Linear scan per keyword; for 50 keywords × 5000 char resume = 250,000 comparisons | Compile all keywords into a single `re.compile(r'\b(?:kw1|kw2|...)\b', re.I)` | Not a real trap at this scale — but `re.compile` is still better practice |

---

## "Looks Done But Isn't" Checklist

- [ ] **Diff view:** Shows only content-meaningful changes — verify that a whitespace-only reformat produces an empty or minimal diff, not a 100-line diff.
- [ ] **Keyword scorer:** Test that common stop words ("the", "and", "will", "be") are absent from the keyword set being scored.
- [ ] **Keyword scorer:** Test that `\bpython\b` does not match inside "cpython" or "pythonic" — confirm word-boundary matching is active.
- [ ] **Two-pass pipeline:** Test that if the analysis pass returns garbage (no XML tags), the tailoring pass still runs and the tool does not abort.
- [ ] **Two-pass pipeline:** Test that the total prompt token budget for the tailoring pass (system prompt + analysis output + JD + resume) does not exceed `num_ctx`. Add a rough token estimate check.
- [ ] **Dropped-section detection:** Confirm it extracts section names from the *original* at runtime rather than matching against a hardcoded list.
- [ ] **Dropped-section detection:** Confirm it detects the `\header{}` macro used in `english.tex`, not just `\section{}`.
- [ ] **Hallucination detection:** Run it against a known-good tailored output and confirm zero false positives before it is shipped.
- [ ] **Hallucination detection:** Confirm warning message uses hedged language ("possible new content") not definitive language ("hallucination detected").
- [ ] **All new features:** Each new feature degrades gracefully — if it fails internally, print a warning and continue; do not abort the main tailoring pipeline.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Diff is all whitespace noise | LOW | Add normalization step before diffing; re-test |
| Keyword score is nonsense (>90% on any input) | LOW | Add stop word filter and word-boundary matching; re-test with known inputs |
| Analysis pass output format is wrong | MEDIUM | Add XML tag validation + fallback to single-pass; requires restructuring two-pass flow |
| Second Ollama call fails partway through | LOW | Error already raised; no partial write. Add descriptive error message naming the failing pass |
| Hallucination checker fires every run | MEDIUM | Rewrite detection to target structured fields only; requires defining field extraction regexes per resume template |
| Dropped-section check misses custom macros | LOW | Replace hardcoded section list with dynamic extraction; one regex change |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Whitespace noise in LaTeX diff | Diff view phase | Run diff on original vs. whitespace-reformatted copy — assert 0 changed lines shown |
| JD keyword stop words inflating score | Keyword scorer phase | Score "the and or will be as" against any resume — assert score is 0% |
| JD keyword substring false positives | Keyword scorer phase | Score "ML" against resume containing "XML" only — assert 0% match |
| Analysis pass unstructured output propagates | Two-pass pipeline phase | Mock analysis pass to return "garbage text" — assert tailoring pass still runs |
| Two-pass latency and timeout | Two-pass pipeline phase | Confirm progress print between calls; confirm same timeout constant used both times |
| Dropped-section macro mismatch | Output guards phase | Run on `english.tex` — assert "Experience", "Skills", "Education", "Languages" all detected via `\header{}` |
| Hallucination false positives on rewrites | Output guards phase | Run on known-good tailored output — assert zero false positive warnings |

---

## Sources

- Python `difflib` documentation — https://docs.python.org/3/library/difflib.html — official; whitespace-as-junk filtering behavior documented there
- `SequenceMatcher` junk filtering — https://pymotw.com/3/difflib/index.html — `IS_CHARACTER_JUNK` and `IS_LINE_JUNK` filters explained
- ATS keyword matching failure modes — https://scale.jobs/blog/resume-keywords-how-ats-systems-read — substring and case sensitivity pitfalls in resume scanners
- NLP keyword extraction stop-word issues — https://www.analyticsvidhya.com/blog/2021/06/resume-screening-with-natural-language-processing-in-python/ — naive frequency counting inflates scores on common tokens
- Structured LLM output failure rates — https://tokenmix.ai/blog/structured-output-json-guide — 8-15% unstructured failure rate without schema enforcement on local models
- Local LLM JSON output failure patterns — https://explore.n1n.ai/blog/local-llm-json-output-failure-patterns-fix-2026-04-24 — local models require explicit format contracts; prose injection common
- Ollama keepalive and model eviction — https://docs.ollama.com/faq — model unloads after 5 minutes inactivity; relevant to inter-call latency
- Two-pass LLM pipeline error propagation — https://arxiv.org/pdf/2604.01029 — second-pass gains are bottlenecked by first-pass quality; error cascades documented
- LLM hallucination detection challenges — https://arxiv.org/pdf/2403.02889 — false positive / negative tradeoffs require calibrated probability scores, not binary flags
- `english.tex` resume structure — `/workspace/resumes/english.tex` — uses `\header{}` custom macro, not `\section{}`; section list: Experience, Projects, Skills, Education, Languages

---

*Pitfalls research for: Resume Tailor CLI v1.1 — output quality features*
*Researched: 2026-06-02*
