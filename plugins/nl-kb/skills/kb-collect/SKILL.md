---
name: kb-collect
description: Use when saving a resource (URL, article, session insight) to the personal knowledge base at ~/knowledge/raw/. Triggers on "save to kb", "收進知識庫", "存到知識庫", "kb-collect", or when user wants to preserve a URL or current session findings for later compilation.
---

# kb-collect

## Overview

Save resources to `~/knowledge/raw/` with zero friction. Two modes: URL fetch (auto-extract content) or session insight extraction.

## When to Use

- User shares a URL and wants to save it
- User says "存到知識庫", "save to kb", "收進 raw"
- After a deep analysis, user wants to preserve key findings
- User says `/kb-collect`

## Usage

```
/kb-collect <url>              → Fetch URL, extract content, save to raw/
/kb-collect <url> <notes>      → Fetch URL + append user notes
/kb-collect                    → Extract key insights from current session
```

## Flow

1. **Determine mode**
   - URL provided → Fetch mode
   - No URL → Session insight mode

2. **Extract content**
   - **URL mode:** WebFetch the URL. Extract full content preserving key details, data points, code examples. Do NOT over-summarize — this is raw material for later compilation.
   - **Session mode:** Review current conversation. Identify key insights, findings, decisions, or discoveries worth preserving. Ask user to confirm what to save if unclear.

3. **Generate filename**
   - Format: `YYYY-MM-DD-<descriptive-slug>.md`
   - Slug: lowercase kebab-case, descriptive enough to recognize at a glance
   - Examples: `2026-04-06-karpathy-knowledge-base-workflow.md`

4. **Write file** to `~/knowledge/raw/`:

```markdown
---
source: <url or "session">
collected: YYYY-MM-DD
tags: [auto-generated, relevant, tags]
---

# <Title>

<Full extracted content — preserve detail>

## Key Takeaways

- <most important points as bullets>
```

5. **Confirm** to user: filename, word count, tags

## Rules

- `raw/` is **flat** — no subdirectories, no categorization
- **Preserve detail** — this is raw material, not a summary. Keep data points, examples, code
- **Always include source** in frontmatter
- **Tags** — 3-5 relevant topic tags for future compilation
- If URL fetch fails (paywalled, blocked), report clearly and save whatever was accessible

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Over-summarizing content | raw/ stores raw material — keep the details |
| Creating subdirectories | raw/ stays flat, categorization is kb-compile's job |
| Vague filename | Must be descriptive enough to recognize at a glance |
| Missing source | Always include source in frontmatter |
