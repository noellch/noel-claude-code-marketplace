---
name: kb-collect
description: Use when saving a resource (URL, article, session insight) to the personal knowledge base at ~/knowledge/raw/. Triggers on "save to kb", "收進知識庫", "存到知識庫", "kb-collect", or when user wants to preserve a URL or current session findings for later compilation.
---

# kb-collect

## Overview

Save resources to `~/knowledge/raw/<category>/` with zero friction. Two modes: URL fetch (auto-extract content) or session insight extraction.

## When to Use

- User shares a URL and wants to save it
- User says "存到知識庫", "save to kb", "收進 raw"
- After a deep analysis, user wants to preserve key findings
- User says `/kb-collect`

## Usage

```
/kb-collect <url>              → Fetch URL, classify, save to raw/<category>/
/kb-collect <url> <notes>      → Fetch URL + append user notes
/kb-collect                    → Extract key insights from current session
```

## Knowledge Base Structure

```
~/knowledge/
├── raw/                  ← Readonly source material
│   ├── articles/           Web articles, blog posts
│   ├── books/              Book notes, highlights
│   ├── papers/             Academic papers
│   ├── repos/              GitHub repos worth studying
│   ├── notes/              Quick thoughts, session insights
│   └── projects/           Project-related materials
├── wiki/                 ← LLM-compiled knowledge (kb-compile output)
│   ├── summaries/          One summary per source
│   ├── concepts/           Cross-source concept entries
│   └── indexes/            All-Sources.md, All-Concepts.md
├── brainstorming/        ← Exploration and QA
│   ├── chat/               AI conversation logs
│   └── health/             Knowledge base health reports
└── artifacts/            ← Finished works
    └── projects/           Articles, presentations, analyses
```

## Flow

1. **Determine mode**
   - URL provided → Fetch mode
   - No URL → Session insight mode

2. **Extract content**
   - **URL mode:** WebFetch the URL. Extract full content preserving key details, data points, code examples. Do NOT over-summarize — this is raw material for later compilation.
   - **Session mode:** Review current conversation. Identify key insights, findings, decisions, or discoveries worth preserving. Ask user to confirm what to save if unclear.

3. **Classify into category**
   - `articles/` — web articles, blog posts, tutorials
   - `books/` — book notes, highlights, chapter summaries
   - `papers/` — academic papers, research
   - `repos/` — GitHub repositories worth studying
   - `notes/` — quick thoughts, session insights, personal observations
   - `projects/` — project-related materials, specs, design docs
   - Default: `articles/` for URLs, `repos/` for GitHub URLs, `notes/` for session insights

4. **Generate filename**
   - Format: `YYYY-MM-DD-<descriptive-slug>.md`
   - Slug: lowercase kebab-case, descriptive enough to recognize at a glance

5. **Write file** to `~/knowledge/raw/<category>/`:

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

6. **Confirm** to user: category, filename, word count, tags

## Rules

- **Preserve detail** — this is raw material, not a summary. Keep data points, examples, code
- **Always include source** in frontmatter
- **Tags** — 3-5 relevant topic tags for future compilation
- **Raw is readonly** — once saved, raw files are never modified by compilation
- If URL fetch fails (paywalled, blocked), report clearly and save whatever was accessible

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Over-summarizing content | raw/ stores raw material — keep the details |
| Vague filename | Must be descriptive enough to recognize at a glance |
| Missing source | Always include source in frontmatter |
| Wrong category | Articles = web content, Notes = personal insights, Papers = academic |
