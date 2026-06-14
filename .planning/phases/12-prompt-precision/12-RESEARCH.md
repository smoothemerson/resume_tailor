# Phase 12: Prompt Precision - Research

**Researched:** 2026-06-09
**Domain:** LLM system prompt engineering — restructuring `_build_messages()` in `src/llm_client.py`
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Rename `<INSTRUCTIONS>` to `<ALLOWED>`. No existing test checks for `<INSTRUCTIONS>`, so this is a free rename.
- **D-02:** Keep `<CONSTRAINTS>` as the outer XML tag name. One existing test (`test_build_messages_system_contains_constraints_tag`) asserts the `<CONSTRAINTS>` tag is present — renaming would break it. The *content* inside `<CONSTRAINTS>` is restructured to a MUST-NOT-CHANGE list, but the tag name stays.
- **D-03:** The ALLOWED and MUST-NOT-CHANGE sections must reference actual LaTeX command names where known. Confirmed macros: `\employer{name}{dates}{title}` (3-arg, all three args protected) and `\header{SectionName}` (protected).
- **D-04:** For project macros and the contact block, the researcher reads `resumes/english.tex` to extract exact LaTeX commands — planner must reference those by name.
- **D-05:** Technology anti-fabrication rule lives inside `<CONSTRAINTS>` as a named, prominently labeled bullet — label: `TECHNOLOGY FIDELITY`. Rule: technologies present in the original must appear; technologies absent from the original must not appear, even if present in the JD.
- **D-06:** Final section order: `<PERSONA>` → `<TASK>` → `<CONTEXT>` → `<ALLOWED>` → `<CONSTRAINTS>` → `<OUTPUT_FORMAT>`.

### Claude's Discretion

- Exact prose/wording within each section.
- Whether to use a bulleted list, numbered list, or sub-headers inside `<ALLOWED>` and `<CONSTRAINTS>`.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRMP-01 | `_build_messages()` system prompt defines an explicit ALLOWED list: title line, employer taglines, employer bullets, project subtitle and bullets, skills reordering/reweighting | Resume structure extracted below; exact elements mapped to LaTeX patterns |
| PRMP-02 | `_build_messages()` system prompt defines an explicit MUST-NOT-CHANGE list: candidate name, contact block, education section, languages section, employer header lines, project name/URL/date, all LaTeX structural commands | Resume macros catalogued below; every protected element identified by LaTeX command name |
| PRMP-03 | System prompt includes an anti-fabrication rule: do not substitute one named technology for another | Placement confirmed inside `<CONSTRAINTS>` tag; TECHNOLOGY FIDELITY label specified |

</phase_requirements>

---

## Summary

Phase 12 is a pure text-edit to the system prompt string inside `_build_messages()` at `src/llm_client.py:26–121`. No logic, no tests, no call sites, and no other files change. The work is: (1) rename the XML tag `<INSTRUCTIONS>` to `<ALLOWED>`, (2) rewrite the content of both the new `<ALLOWED>` section and the existing `<CONSTRAINTS>` section to use explicit, concrete lists referencing real LaTeX macro names from the actual resume, and (3) add a prominently labeled TECHNOLOGY FIDELITY rule inside `<CONSTRAINTS>`.

The resume `resumes/english.tex` uses a flat-structure LaTeX document (no `\begin{section}` environments). Structure is provided entirely through custom commands: `\header{}`, `\employer{}{}{}`, `\contact{}{}{}`, `\schoolwithcourses{}{}{}{}`, `\school{}{}{}{}`, and `\area{}{}`. Projects are NOT wrapped in a custom macro — each project is a raw `\href{url}{\textbf{Name}}\text{ | subtitle}` line followed by an `itemize` environment. The contact block is raw `\begin{center}` LaTeX, not a macro call with named arguments.

The single binding test constraint is `test_build_messages_system_contains_constraints_tag` (line 35 of `tests/unit/test_llm_client.py`), which asserts `<CONSTRAINTS>` and `</CONSTRAINTS>` are present. No test checks for `<INSTRUCTIONS>`, `<ALLOWED>`, or any prompt content beyond tag presence and user-message structure.

**Primary recommendation:** Write the ALLOWED list as a concrete bulleted list naming each changeable element; write the MUST-NOT-CHANGE list as a concrete bulleted list naming each protected element by its LaTeX command or literal pattern; place TECHNOLOGY FIDELITY as a named rule at the end of `<CONSTRAINTS>`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| System prompt construction | `_build_messages()` function | — | Pure Python string; no framework layer |
| Prompt structure / XML tagging | `_build_messages()` string literal | `tests/unit/test_llm_client.py` (asserts tags exist) | Tests enforce the tag contract |
| LaTeX macro knowledge | Resume source file `resumes/english.tex` | `src/guards.py` (confirms `\employer` and `\header` patterns) | Resume is the single source of truth for what macros exist |
| Test pass/fail gate | `tests/unit/test_llm_client.py` | `src/llm_client_test.py` | Both suites must pass unchanged |

---

## Standard Stack

This phase introduces no new packages. The only dependency surface is the existing codebase.

| File | Role | What Changes |
|------|------|--------------|
| `src/llm_client.py` | Only file modified | `_build_messages()` system prompt string (lines 27–95) |
| `resumes/english.tex` | Read-only reference | Provides exact macro names for prompt content |
| `src/guards.py` | Read-only reference | Confirms `\employer` and `\header` regex patterns |

### No new packages

This phase is a text edit. No `npm install`, `pip install`, or package changes of any kind.

---

## Package Legitimacy Audit

Not applicable — no packages are installed in this phase.

---

## Architecture Patterns

### Data Flow

```
_build_messages(resume_text, job_description, analysis)
    |
    |-- system_prompt (string literal, fully rewritten by Phase 12)
    |       <PERSONA>   [unchanged]
    |       <TASK>      [unchanged]
    |       <CONTEXT>   [unchanged]
    |       <ALLOWED>   [renamed from <INSTRUCTIONS>; content rewritten]
    |       <CONSTRAINTS> [tag name kept; content rewritten with MUST-NOT-CHANGE list + TECHNOLOGY FIDELITY]
    |       <OUTPUT_FORMAT> [unchanged]
    |
    |-- user_message (assembled from job_description + resume_text + optional analysis)
    |       [NOT TOUCHED by Phase 12]
    |
    v
    [{"role": "system", "content": system_prompt},
     {"role": "user",   "content": user_message}]
```

### Exact Resume LaTeX Macro Inventory

Extracted directly from `resumes/english.tex` [VERIFIED: read from source file]:

**Structural macros (protected — must not change their arguments):**

| Macro | Signature | Where Used | Phase 12 Status |
|-------|-----------|-----------|-----------------|
| `\header` | `\header{SectionName}` | All section headings: Education, Experience, Projects, Skills, Languages | MUST-NOT-CHANGE |
| `\employer` | `\employer{name}{dates}{title}` | NOT USED in `english.tex` — employer entries use raw `\textbf{NAME}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES` inline markup | See note below |
| `\contact` | `\contact{name}{line2}{line3}` | NOT USED — contact block is raw `\begin{center}` HTML with `{\Huge \scshape {Emerson Rocha Faria}}\\` | MUST-NOT-CHANGE (as the entire center block) |
| `\schoolwithcourses` | `\schoolwithcourses{school}{location}{degree}{courses}` | NOT USED — education section uses raw `\textbf{Catholic University...}` inline markup | MUST-NOT-CHANGE (entire education block) |
| `\school` | `\school{school}{location}{degree}{extra}` | NOT USED in this resume | N/A |
| `\area` | `\area{label}{content}` | NOT USED in this resume | N/A |

**IMPORTANT FINDING:** The `english.tex` resume does NOT use `\employer{}{}{}` or `\contact{}{}{}` as macro calls in the document body, even though those macros are defined in the preamble. The resume uses raw LaTeX inline markup for employer entries and the contact block. This matters for Phase 12 prompting: the MUST-NOT-CHANGE list should reference the actual patterns that appear in the file, not the macro names.

**Actual patterns in the resume body:**

| Element | Actual LaTeX Pattern |
|---------|---------------------|
| Candidate name | `{\Huge \scshape {Emerson Rocha Faria}}\\` inside `\begin{center}` |
| Contact block | Entire `\begin{center}...\end{center}` block at top of document (lines 75–85) |
| Employer header | `\textbf{SERPRO}\textbf{ | AI Engineering Intern} \hfill Bras\'{i}lia, Brazil\ $\cdot$\ Feb 2024 -- Feb 2026\\` |
| Employer tagline | `\textit{\small Owned AI projects end-to-end; ...}\\` |
| Employer bullets | `\begin{itemize} \itemsep -3pt` + `\item ...` entries |
| Project anchor | `\href{https://github.com/smoothemerson/ragscope}{\textbf{RAGScope}}\text{ | ...} \hfill Mar 2026\\` |
| Project bullets | `\begin{itemize} \itemsep -3pt` + `\item ...` entries |
| Skills lines | `\noindent\textbf{AI:} LangChain, ChromaDB, ...\\` (one line per category) |
| Section headers | `\header{Education}`, `\header{Experience}`, `\header{Projects}`, `\header{Skills}`, `\header{Languages}` |
| Education block | Raw `\textbf{Catholic University...}` + degree + GPA + coursework lines |
| Languages block | `\noindent\textbf{English:} Professional Working Proficiency\\` etc. |

**Guards.py cross-reference:**

`src/guards.py` defines `_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')`. This pattern would match macro calls in the form `\employer{name}{dates}{title}` — but `english.tex` does not use that macro call form in its body. The guard is defined for resumes that do use the macro form. The prompt's MUST-NOT-CHANGE list should describe the actual inline patterns actually present in `english.tex`, not the macro signature. [VERIFIED: read from source files]

---

## Current `_build_messages()` System Prompt — Complete Structure

[VERIFIED: read directly from `src/llm_client.py` lines 27–95]

```
<PERSONA>
  "Alexandra" persona — senior technical recruiter / resume strategist
  ATS expertise, honest rewrites only
</PERSONA>

<TASK>
  Tailor candidate's LaTeX resume to job description
  Return ONLY complete compilable LaTeX (starts with \documentclass, ends with \end{document})
</TASK>

<CONTEXT>
  Resume = single source of truth
  Job description = optimization target
</CONTEXT>

<INSTRUCTIONS>   <-- RENAME TO <ALLOWED> (D-01)
  1. Rewrite professional summary (role alignment + seniority/domain language)
  2. Rewrite skills section (surface JD keywords, only existing skills)
  3. Rewrite experience bullets (emphasize outcomes, metrics, relevance)
  4. Preserve order/weight of bullets; do not reorder jobs or add/remove bullets
  5. Integrate ATS-critical keywords where they map to existing content
  6. Do not alter LaTeX structural commands, environments, formatting macros
</INSTRUCTIONS>

<CONSTRAINTS>   <-- TAG NAME STAYS (D-02); CONTENT REWRITTEN
  - Only reword existing content; all facts verbatim from original
  - Do NOT invent/add/imply/upgrade experience/skill/tool/credential not in original
  - Do NOT alter: education, contact, company names, job titles, dates, project names, LaTeX structural commands
  - Do NOT change number of bullet points
  - Do NOT convert passive to active if underlying claim would be inflated
  - Limit rewriting to: professional summary, skills section, experience bullets
</CONSTRAINTS>

<OUTPUT_FORMAT>
  Return: complete compilable LaTeX, rewritten sections only (summary, skills, experience bullets)
  Do NOT return: text before \documentclass or after \end{document}, markdown fences, prose/comments, new facts
</OUTPUT_FORMAT>
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML tag parsing / validation | Custom regex for tags | None needed — this is string content, not parsed | The prompt is a string literal the LLM reads; no runtime parsing of the prompt itself |
| Resume LaTeX parsing | Custom `.tex` parser | Read the file directly with `Path.read_text()` | The prompt receives `resume_text` as a raw string; no structured parsing |

**Key insight:** This phase is entirely a prose-editing task on a Python string. There is no library, algorithm, or framework involved. The only "technical" work is knowing the correct LaTeX macro names to write into the prompt text.

---

## Common Pitfalls

### Pitfall 1: Describing Macros That Are Not Used in the Document Body

**What goes wrong:** The prompt writes "do not change `\employer{name}{dates}{title}` arguments" — but `english.tex` uses inline `\textbf{NAME}\textbf{ | ROLE} \hfill ...` for employer entries, not a `\employer{}{}{}` macro call. The LLM receives the raw `.tex` file and will not recognise the disconnect.

**Why it happens:** The preamble defines `\employer` but the document body never uses it. Guards rely on this pattern but the actual `.tex` doesn't exercise it.

**How to avoid:** Reference the actual inline patterns from the resume: employer headers are `\textbf{...}\textbf{ | ...} \hfill ...` lines. Contact block is a raw `\begin{center}...\end{center}`. Use descriptive language ("employer header lines", "the \begin{center} block at the top") rather than macro-call syntax when the macro isn't actually invoked in the body.

**Warning signs:** Rereading the prompt and noticing macro-call syntax (`\employer{}{}{}`), then checking `english.tex` and not finding that pattern in the body.

### Pitfall 2: Breaking the `<CONSTRAINTS>` Tag Test

**What goes wrong:** Renaming `<CONSTRAINTS>` to something like `<MUST_NOT_CHANGE>` to match the semantic goal — breaks `test_build_messages_system_contains_constraints_tag`.

**Why it happens:** Naturalizing the prompt to match its content category.

**How to avoid:** Per D-02, the outer XML tag name stays `<CONSTRAINTS>`. Only the inner content changes. The MUST-NOT-CHANGE heading can appear as a section header or bold label inside the tag.

**Warning signs:** Searching the prompt for `<CONSTRAINTS>` and not finding it in the output.

### Pitfall 3: Editing Lines Outside the System Prompt String

**What goes wrong:** Accidentally modifying the user message assembly block (lines 97–121), the `generate_tailored_resume()` function signature, or any test file.

**Why it happens:** The phase is described as "one function, one file" but the function has two sections (system prompt and user message).

**How to avoid:** Only lines 27–95 (the `system_prompt` string) change. Lines 97 onward are the user message assembly — do not touch.

**Warning signs:** A diff that shows changes outside the string literal on lines 27–95.

### Pitfall 4: Losing Existing Prompt Value While Restructuring

**What goes wrong:** The ALLOWED section becomes so terse it loses instructional precision (e.g., "rewrite bullets" without specifying "preserve bullet count and order"). Important behavioral constraints from the old `<INSTRUCTIONS>` section get dropped.

**Why it happens:** The rename/restructure tempts treating the old content as throw-away.

**How to avoid:** Map every instruction in the old `<INSTRUCTIONS>` to either ALLOWED or MUST-NOT-CHANGE. Carry forward the "do not change bullet count" constraint. The old `<INSTRUCTIONS>` point 4 ("Preserve the order and relative weight...") is a MUST-NOT-CHANGE rule.

---

## Test Constraint Inventory

[VERIFIED: read directly from `tests/unit/test_llm_client.py` and `src/llm_client_test.py`]

### Tests That Constrain Phase 12 Changes

| Test | File | Assertion | Phase 12 Impact |
|------|------|-----------|-----------------|
| `test_build_messages_system_contains_persona_tag` | `tests/unit/test_llm_client.py:28` | `<PERSONA>` and `</PERSONA>` in system content | Must keep `<PERSONA>` tag |
| `test_build_messages_system_contains_constraints_tag` | `tests/unit/test_llm_client.py:35` | `<CONSTRAINTS>` and `</CONSTRAINTS>` in system content | Must keep `<CONSTRAINTS>` tag — this is the binding constraint |
| `test_build_messages_returns_two_element_list` | `tests/unit/test_llm_client.py:15` | `len(result) == 2` | No structural change to return value |
| `test_build_messages_role_ordering` | `tests/unit/test_llm_client.py:21` | `result[0]["role"] == "system"`, `result[1]["role"] == "user"` | No change to message role structure |
| `test_build_messages_user_contains_job_description_xml_tag` | `tests/unit/test_llm_client.py:42` | `<job_description>` in user message | User message unchanged |
| `test_build_messages_user_embeds_job_description_content` | `tests/unit/test_llm_client.py:49` | JD string in user content | User message unchanged |
| `test_build_messages_user_contains_resume_xml_tag` | `tests/unit/test_llm_client.py:56` | `<resume>` in user content | User message unchanged |
| `test_build_messages_user_embeds_resume_content` | `tests/unit/test_llm_client.py:63` | Resume string in user content | User message unchanged |
| `test_build_messages_with_analysis_includes_jd_analysis_tag` | `tests/unit/test_llm_client.py:221` | `<jd_analysis>` in user message when analysis passed | User message unchanged |
| `test_build_messages_without_analysis_omits_jd_analysis_tag` | `tests/unit/test_llm_client.py:228` | No `<jd_analysis>` when analysis=None | User message unchanged |

### Tests That Do NOT Constrain Phase 12

No test asserts:
- The presence or absence of `<INSTRUCTIONS>` or `</INSTRUCTIONS>`
- The presence or absence of `<ALLOWED>` or `</ALLOWED>`
- Any specific text content within `<CONSTRAINTS>`
- Any specific text content within `<INSTRUCTIONS>` / `<ALLOWED>`
- Any specific text content within `<OUTPUT_FORMAT>`
- Any specific text content within `<TASK>` or `<CONTEXT>`

### In-Src Test File (`src/llm_client_test.py`)

Contains 14 tests covering `_strip_fences`, `_validate_latex`, `generate_tailored_resume` (via mock), and `TailorResult`. None of these tests call `_build_messages()` directly or assert anything about system prompt content. All will pass unchanged. [VERIFIED: read from source file]

---

## ALLOWED Section Content Design

Based on PRMP-01 requirements and the actual resume structure:

**Elements the LLM MAY rewrite (ALLOWED list):**

1. **Title line** — the `\ {AI Engineer}\\` line in the contact header
2. **Employer taglines** — the `\textit{\small ...}\\` line below each employer header
3. **Employer bullet points** — `\item` entries inside `\begin{itemize}` under each employer (reword only; count stays fixed)
4. **Project subtitle** — the `\text{ | subtitle}` portion of each `\href{...}{\textbf{Name}}\text{ | subtitle} \hfill date\\` line
5. **Project bullet points** — `\item` entries inside `\begin{itemize}` under each project (reword only; count stays fixed)
6. **Skills section content** — the technology lists on the `\textbf{Category:} item1, item2, ...\\` lines (reorder within categories, reweight categories); must stay within skills already in original

---

## MUST-NOT-CHANGE Section Content Design

Based on PRMP-02 requirements and the actual resume structure:

**Elements the LLM must NOT change:**

1. **Candidate name** — `{\Huge \scshape {Emerson Rocha Faria}}\\` inside the `\begin{center}` block
2. **Contact block** — entire `\begin{center}...\end{center}` block (email, phone, location, LinkedIn, GitHub)
3. **Education section** — everything under `\header{Education}` including institution name, degree, dates, GPA, coursework
4. **Languages section** — everything under `\header{Languages}` (English/Portuguese entries)
5. **Employer header lines** — `\textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\` lines (company name, role title, dates, location)
6. **Project name, URL, and date** — the `\href{url}{\textbf{ProjectName}}` and `\hfill date` portions of project lines
7. **All `\header{...}` calls** — section headings (Education, Experience, Projects, Skills, Languages)
8. **All LaTeX structural commands** — `\documentclass`, `\usepackage`, `\newcommand`, `\begin`, `\end`, `\vspace`, `\hfill`, `\textbf`, `\textit`, `\hspace`, `\href`, `\noindent`, and all other commands outside the changeable content listed in ALLOWED
9. **Bullet point count** — do not add or remove `\item` entries in any list

---

## Code Examples

### Current `<INSTRUCTIONS>` block (to be renamed and replaced)

```python
# Current lines 52–68 of src/llm_client.py (the string content):
        <INSTRUCTIONS>
        1. Rewrite the professional summary to open with the most relevant role alignment and
        mirror the seniority/domain language used in the job description.
        2. Rewrite the skills section to surface keywords and technologies that appear in the
        job description, but only include skills already present (explicitly or implicitly)
        in the original resume.
        3. Rewrite experience bullet points to emphasize outcomes, metrics, and responsibilities
        that are most relevant to the job description. Prioritize action verbs and quantified
        impact where they already exist in the original.
        4. Preserve the order and relative weight of bullet points, do not reorder jobs or
        add/remove bullet points, only reword them.
        5. Scan the job description for ATS-critical keywords (e.g. specific tools, frameworks,
        methodologies, certifications). Where those keywords map to existing content in the
        resume, integrate them naturally into the rewritten sections.
        6. Do not alter any LaTeX structural commands, environments, formatting macros, or
        custom commands. Preserve whitespace and line breaks in non-content areas.
        </INSTRUCTIONS>
```

### Target structure for `<ALLOWED>` (replaces `<INSTRUCTIONS>`)

```python
        <ALLOWED>
        You may ONLY rewrite the following elements:
        - Title line: the professional title (e.g., "AI Engineer") in the contact header
        - Employer taglines: the italic summary line below each employer header
        - Employer bullet points: the \item entries under each employer (reword only — count stays fixed)
        - Project subtitle: the descriptive text after the project name on each project line
        - Project bullet points: the \item entries under each project (reword only — count stays fixed)
        - Skills content: the technology lists within each skills category (reorder/reweight; use only skills already present)

        Everything not listed above must remain byte-for-byte identical.
        </ALLOWED>
```

### Target structure for `<CONSTRAINTS>` (outer tag stays; content rewritten)

```python
        <CONSTRAINTS>
        MUST NOT CHANGE:
        - Candidate name: the {\Huge \scshape {Name}} in the \begin{center} block
        - Contact block: the entire \begin{center}...\end{center} block (email, phone, location, LinkedIn, GitHub)
        - Education section: everything under \header{Education}
        - Languages section: everything under \header{Languages}
        - Employer header lines: company name, role title, location, and date range on each employer header line
        - Project anchors: the \href{url}{\textbf{ProjectName}} and \hfill date on each project line
        - Section headers: all \header{...} commands
        - All LaTeX commands and environments: \documentclass, \usepackage, \newcommand definitions, \begin, \end, \vspace, \hfill, \textbf, \textit, \href, and all other structural commands
        - Bullet point count: do not add or remove \item entries in any list

        TECHNOLOGY FIDELITY:
        Do not substitute one named technology for another. If a technology appears in the original resume, it must appear in the output. If a technology is absent from the original resume, it must not appear in the output — even if it appears in the job description. (Example: if the resume mentions Azure, Azure must remain; if the resume does not mention AWS, AWS must not be added.)
        </CONSTRAINTS>
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3+ |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest -m unit -x` |
| Full suite command | `pytest` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRMP-01 | `<ALLOWED>` tag is present in system prompt | unit | N/A — no test checks this tag | No existing test; no new test required (success criteria only requires tag content, not test coverage) |
| PRMP-02 | `<CONSTRAINTS>` tag present in system prompt | unit | `pytest tests/unit/test_llm_client.py::test_build_messages_system_contains_constraints_tag -x` | YES |
| PRMP-03 | TECHNOLOGY FIDELITY rule inside `<CONSTRAINTS>` | unit | N/A — no test checks prompt content | No test required per success criteria 4 ("all existing tests pass") |

### Sampling Rate

- **Per task commit:** `pytest -m unit -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all phase requirements. The only binding test (`test_build_messages_system_contains_constraints_tag`) already exists and will pass as long as `<CONSTRAINTS>` tag remains.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 12 is a pure string-content edit inside a Python source file. No external tools, services, CLIs, or runtimes beyond what is already installed are required.

---

## Runtime State Inventory

Not applicable — this is a greenfield edit to prompt content. No rename/refactor/migration.

---

## Security Domain

Not applicable — this phase modifies only a string literal inside a local Python file. No authentication, session, access control, input validation, cryptography, or network-facing changes.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Numbered instructions list | Explicitly labeled ALLOWED / MUST-NOT-CHANGE sections | LLMs perform more reliably when allowed vs. prohibited actions are separate, labeled sections |
| Generic "don't alter LaTeX" instruction | Named concrete elements by their actual LaTeX pattern | Reduces ambiguity about which elements are meant |
| Anti-fabrication as buried constraint bullet | Named TECHNOLOGY FIDELITY rule with example | Labeled rules are harder for LLMs to miss than unmarked list items |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The resume file used at runtime is `resumes/english.tex` in the main worktree (not the phase12 worktree) | Resume Macro Inventory | If runtime uses a different resume, the macro names referenced in the prompt may be wrong — but prompts are written generically enough to apply to any resume with the same macro set |

**All other claims in this research were verified by direct source file reads.**

---

## Open Questions

None — all decisions from CONTEXT.md are locked and all source files have been read.

---

## Sources

### Primary (HIGH confidence)

- `src/llm_client.py` lines 26–121 — read directly; complete current `_build_messages()` function
- `tests/unit/test_llm_client.py` — read directly; all 23 tests catalogued
- `src/llm_client_test.py` — read directly; all 14 in-src tests catalogued
- `resumes/english.tex` — read directly from `/workspace/resumes/english.tex`; all LaTeX macros extracted
- `src/guards.py` — read directly; `\employer` and `\header` regex patterns confirmed
- `.planning/phases/12-prompt-precision/12-CONTEXT.md` — read directly; all decisions locked
- `.planning/REQUIREMENTS.md` — read directly; PRMP-01, PRMP-02, PRMP-03 definitions

### Secondary (MEDIUM confidence)

None required — all research was from primary source file reads.

---

## Metadata

**Confidence breakdown:**
- LaTeX macro inventory: HIGH — read directly from source file
- Test constraint inventory: HIGH — read directly from both test files
- Current prompt structure: HIGH — read directly from `llm_client.py`
- ALLOWED/MUST-NOT-CHANGE design: HIGH — derived from REQUIREMENTS.md + actual resume patterns
- Architecture: HIGH — single-function, single-file scope confirmed

**Research date:** 2026-06-09
**Valid until:** Stable — until `resumes/english.tex` or test files change
