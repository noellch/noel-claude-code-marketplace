---
name: kb-compile
description: Use when compiling raw knowledge base materials into structured wiki. Triggers on "compile kb", "整理知識庫", "kb-compile", or when ~/knowledge/raw/ has accumulated enough materials for organization.
---

# kb-compile

## Overview

Compile `~/knowledge/raw/` into a structured, searchable wiki in `~/knowledge/wiki/`. Reads all raw materials and produces organized, cross-referenced knowledge.

## When to Use

- `raw/` has accumulated 10+ files and needs organization
- User says "整理知識庫", "compile", "build wiki"
- User says `/kb-compile`

## Flow

1. **Inventory raw/**
   - Read all files in `~/knowledge/raw/`
   - List files with dates, tags, brief descriptions
   - Show user the inventory and estimated scope

2. **Detect topics**
   - Analyze tags and content to identify natural topic clusters
   - Propose wiki structure to user for confirmation:
     ```
     wiki/
     ├── index.md                    ← Master index
     ├── bigquery-optimization.md    ← Topic page
     ├── django-patterns.md          ← Topic page
     └── ...
     ```

3. **Compile each topic page:**

```markdown
# <Topic Name>

## Core Concepts
<Concept> — <2-3 sentence explanation>

## Concept Relationships
<How concepts connect to each other>

## Practical Decision Guide
<When to choose X vs Y — decision tables, rules of thumb>

## Key Evidence & Data Points
<Specific numbers, benchmarks, examples from raw materials>

## Sources
- [filename](../raw/filename.md) — what it contributed

## Knowledge Gaps
<What's missing, what to collect next>
```

4. **Generate index.md** — master page linking all topics

5. **Report** — topics generated, cross-references found, gaps identified

## Rules

- **Preserve provenance** — every claim traces back to a raw/ source
- **Flag contradictions** — if raw materials disagree, make it explicit
- **Suggest gaps** — note what's missing for completeness
- **Incremental updates** — if wiki/ already has content, merge new info into existing pages
- **Never delete raw/** — raw/ is source of truth, wiki/ is derived

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Overwriting existing wiki pages | Merge new content into existing pages |
| Losing source attribution | Every section references which raw/ files informed it |
| Too many small pages | Group related concepts into one topic page |
| Ignoring contradictions | Flag disagreements — they're valuable signals |
