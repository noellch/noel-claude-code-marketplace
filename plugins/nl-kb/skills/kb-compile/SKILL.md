---
name: kb-compile
description: Use when compiling raw knowledge base materials into structured wiki. Triggers on "compile kb", "整理知識庫", "kb-compile", or when ~/knowledge/raw/ has accumulated enough materials for organization.
---

# kb-compile

## Overview

Compile `~/knowledge/raw/` into structured knowledge in `~/knowledge/wiki/`. Generates per-source summaries, extracts cross-source concepts, and builds indexes.

## When to Use

- `raw/` has accumulated new uncompiled files
- User says "整理知識庫", "compile", "build wiki"
- User says `/kb-compile`

## Knowledge Base Structure

```
~/knowledge/
├── raw/                  ← Readonly source material (input)
│   ├── articles/
│   ├── books/
│   ├── papers/
│   ├── notes/
│   └── projects/
├── wiki/                 ← LLM-compiled knowledge (output)
│   ├── summaries/          One summary per source
│   ├── concepts/           Cross-source concept entries
│   └── indexes/            All-Sources.md, All-Concepts.md
├── brainstorming/        ← Exploration records
│   ├── chat/
│   └── health/
└── artifacts/            ← Finished works
```

## Flow

1. **Inventory raw/**
   - Scan all subdirectories for files
   - Compare against existing `wiki/summaries/` to find uncompiled sources
   - Show user: new files count, total files, last compile date

2. **Generate summaries** (`wiki/summaries/`)
   - One summary per raw source file
   - Filename mirrors source: `wiki/summaries/<source-filename>.md`
   - Each summary includes:

```markdown
# <Title>

**Source:** [filename](../../raw/<category>/<filename>)
**Origin:** external | self
**Compiled:** YYYY-MM-DD

## Core Conclusions
<Main arguments and findings>

## Key Evidence
<Data points, examples, quotes>

## Open Questions
<Doubts, gaps, things to verify>

## Terms
<Domain-specific terminology defined>
```

3. **Extract concepts** (`wiki/concepts/`)
   - A concept gets its own entry when it appears in **2+ summaries**
   - Each concept entry includes:

```markdown
# <Concept Name>

## Definition
<What this concept means>

## External Perspectives
<What sources say — with links to summaries>

## My Practice
<Personal experience and observations, if any>

## Tensions & Gaps
<Contradictions between sources, or between theory and practice>

## Related Concepts
<Links to other concept entries>
```

4. **Update indexes** (`wiki/indexes/`)
   - `All-Sources.md` — table of all sources with category, date, summary link
   - `All-Concepts.md` — alphabetical list of concepts with brief description and source count

5. **Report** — new summaries created, new/updated concepts, contradictions found

## Rules

- **Raw is readonly** — never modify files in `raw/`
- **Incremental** — only compile new/changed sources, don't redo existing summaries
- **Preserve provenance** — every claim traces back to a raw source
- **Flag contradictions** — when sources disagree, surface it in concept Tensions & Gaps
- **Separate external vs self** — distinguish external sources from user's own notes/artifacts

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Modifying raw/ files | Raw is readonly — all output goes to wiki/ |
| Recompiling everything | Only process new/changed files |
| Missing concept links | Concepts must reference which summaries mention them |
| Ignoring contradictions | Tensions are the most valuable part — always surface them |
