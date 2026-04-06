---
name: kb-compile
description: Use when compiling raw knowledge base materials into structured wiki. Triggers on "compile kb", "整理知識庫", "kb-compile", or when ~/knowledge/raw/ has accumulated enough materials for organization.
---

# kb-compile

## Overview

Compile `~/knowledge/raw/` into structured knowledge in `~/knowledge/wiki/`. Generates per-source summaries, extracts cross-source concepts, and builds indexes. Incremental by default — only processes new files.

## When to Use

- `raw/` has accumulated new uncompiled files
- User says "整理知識庫", "compile", "build wiki"
- User says `/kb-compile`

## Flow

### Step 1: Inventory

Scan `raw/` subdirectories for `.md` files. Compare against `wiki/summaries/` to find uncompiled sources. Matching is by **exact filename** — `raw/articles/2026-04-06-foo.md` maps to `wiki/summaries/2026-04-06-foo.md`.

Show user:
- New files count
- Total files in raw/
- List of new files to compile

### Step 2: Generate summaries (`wiki/summaries/`)

One summary per raw source. **Filename must match the source exactly** — do NOT add prefixes like `article--` or `note--`.

```
raw/articles/2026-04-06-karpathy-ai-knowledge-base-workflow.md
→ wiki/summaries/2026-04-06-karpathy-ai-knowledge-base-workflow.md
```

Each summary uses this **exact** structure:

```markdown
# <Title>

**Source:** [filename](../../raw/<category>/<filename>)
**Origin:** external | self
**Compiled:** YYYY-MM-DD

## Core Conclusions
<Main arguments and findings — 3-5 bullets>

## Key Evidence
<Data points, examples, quotes that support the conclusions>

## Open Questions
<Doubts, gaps, things to verify, contradictions with other sources>

## Terms
<Domain-specific terminology introduced or used — term: definition>
```

**Origin rules:**
- `external` — articles, books, papers, repos (someone else's work)
- `self` — notes, projects, artifacts (user's own insights)

**Do NOT add fields or sections beyond what is shown above.** No `TL;DR`, no `Actionable Takeaways`, no `Relations`. Those are compile's internal concerns, not the output format.

### Step 3: Extract concepts (`wiki/concepts/`)

A concept gets its own entry **only when it appears in 2 or more summaries**. This threshold is strict.

**Single-source findings do NOT get concept entries.** They live in their summary until a second source mentions them.

Each concept uses this **exact** structure:

```markdown
# <Concept Name>

## Definition
<What this concept means — 2-3 sentences>

## External Perspectives
<What sources say, with links to summaries>
- [source-title](../summaries/filename.md) — what it says about this concept

## My Practice
<User's personal experience and observations, drawn from self-origin summaries. Leave blank if none.>

## Tensions & Gaps
<Contradictions between sources, or between external views and personal practice. This is the most valuable section — never skip it.>

## Related Concepts
<Links to other concept entries>
- [concept-name](concept-name.md)
```

### Step 4: Update indexes (`wiki/indexes/`)

**Exactly 2 index files. No more.**

**`All-Sources.md`:**

```markdown
# All Sources

| Date | Title | Category | Summary |
|------|-------|----------|---------|
| 2026-04-06 | Karpathy AI Knowledge Base | articles | [link](../summaries/2026-04-06-karpathy-ai-knowledge-base-workflow.md) |
| ... | ... | ... | ... |
```

**`All-Concepts.md`:**

```markdown
# All Concepts

| Concept | Sources | Link |
|---------|---------|------|
| Knowledge Management | 3 | [link](../concepts/knowledge-management.md) |
| ... | ... | ... |
```

Do NOT create additional index files (no `chronological.md`, no `by-source-type.md`, no `by-concept.md`). Two indexes only.

### Step 5: Report

Tell the user:
- Summaries created (count + list)
- Concepts created or updated (count + list)
- Contradictions found
- Knowledge gaps identified

## Rules

- **Raw is readonly** — NEVER modify files in `raw/`. Not even to add frontmatter. If you feel the urge to "improve" a raw file, stop. That is a violation.
- **Incremental** — only compile new/changed sources. Do not regenerate existing summaries unless the user explicitly says "recompile".
- **Summary filename = raw filename** — no prefixes, no transformations. The mapping must be mechanical.
- **Concept threshold: 2+ sources** — single-source ideas stay in their summary. Do not create concept entries for ideas mentioned in only one source, even if the idea seems "important enough."
- **Exactly 2 index files** — `All-Sources.md` and `All-Concepts.md`. No additional indexes.
- **Preserve provenance** — every claim in wiki must trace to a specific raw source.
- **Flag contradictions** — when sources disagree, surface it in concept Tensions & Gaps. This is the most valuable part of compilation.
- **Separate external vs self** — use the Origin field to distinguish.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Adding prefix to summary filename (`article--foo.md`) | Summary filename = raw filename exactly |
| Creating concept for single-source idea | Concept threshold is 2+ sources. No exceptions. |
| Creating extra index files | Only `All-Sources.md` and `All-Concepts.md` |
| Modifying raw/ files | Raw is readonly. Never touch it. |
| Adding extra sections to summaries | Use the exact 4 sections: Core Conclusions, Key Evidence, Open Questions, Terms |
| Recompiling already-compiled sources | Only process new files unless user says "recompile" |
| Proposing to add frontmatter to raw/ | That violates readonly. Do not even suggest it. |
| Creating `maturity` or `status` fields | Not in the schema. Do not invent fields. |
