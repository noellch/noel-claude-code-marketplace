---
name: kb-collect
description: Use when saving a resource (URL, article, session insight) to the personal knowledge base at ~/knowledge/raw/. Triggers on "save to kb", "收進知識庫", "存到知識庫", "kb-collect", or when user wants to preserve a URL or current session findings for later compilation.
---

# kb-collect

## Overview

Save resources to `~/knowledge/raw/<category>/` with zero friction. Two modes: URL fetch or session insight extraction.

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

## Flow

### Step 1: Determine mode

- URL provided → Fetch mode
- No URL → Session insight mode

### Step 2: Extract content

- **URL mode:** WebFetch the URL. Extract full content preserving key details, data points, code examples. Do NOT over-summarize — this is raw material for later compilation.
- **Session mode:** Review current conversation. Identify key insights, findings, decisions, or discoveries worth preserving. Ask user to confirm what to save if unclear.

### Step 3: Classify into category

| Category | What goes here | Default for |
|----------|---------------|-------------|
| `articles/` | Web articles, blog posts, tutorials | Non-GitHub URLs |
| `books/` | Book notes, highlights, chapter summaries | — |
| `papers/` | Academic papers, research | — |
| `repos/` | GitHub repositories worth studying | `github.com` URLs |
| `notes/` | Quick thoughts, session insights, personal observations | Session mode |
| `projects/` | Project-related materials, specs, design docs | — |

### Step 4: Generate filename

**Format: `YYYY-MM-DD-<descriptive-slug>.md`**

- Date prefix is **mandatory** — enables chronological sorting
- Slug: lowercase kebab-case, descriptive enough to recognize at a glance
- Examples:
  - `2026-04-06-karpathy-ai-knowledge-base-workflow.md`
  - `2026-04-07-bq-partition-pruning-timestamp-cast.md`
  - `2026-04-07-llm-knowledge-base-gatelynch.md`

**Without date prefix = wrong.** Every filename must start with `YYYY-MM-DD-`.

### Step 5: Write file

Write to `~/knowledge/raw/<category>/` with this **exact** structure:

```markdown
---
source: <url or "session">
collected: YYYY-MM-DD
tags: [tag1, tag2, tag3]
---

# <Title>

<Full extracted content>

## Key Takeaways

- <bullet 1>
- <bullet 2>
- <bullet 3>
```

**Frontmatter has exactly 3 fields. No more, no less:**
- `source` — the URL, or `"session"` for session insights
- `collected` — date in YYYY-MM-DD
- `tags` — 3-5 relevant topic tags

Do NOT add: `title`, `type`, `status`, `domain`, `author`, `language`, `stars`, `license`, `topics`, `description`, `saved_at`, `date`, `source_url`, or any other field. These pollute the schema and make compilation unreliable.

**Content must include a `## Key Takeaways` section** at the end with 3-5 bullet points. This is mandatory for all modes (URL, session, repo).

### Step 6: Confirm

Tell the user: category, full file path, word count, tags.

## Rules

- **Date prefix is mandatory** on every filename — `YYYY-MM-DD-slug.md`
- **Exactly 3 frontmatter fields** — `source`, `collected`, `tags`. Nothing else.
- **Always include `## Key Takeaways`** — even for repos, even for session notes
- **Preserve detail** — this is raw material, not a summary. Keep data, examples, code
- **Raw is readonly** — once saved, raw files are never modified by compilation
- If URL fetch fails (paywalled, blocked), report clearly and save whatever was accessible
- **Do NOT fetch metadata for repos** (stars, language, license) — that is kb-compile's job. Just fetch the README and save it.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Filename without date prefix | Every file: `YYYY-MM-DD-slug.md`. No exceptions. |
| Extra frontmatter fields | Only `source`, `collected`, `tags`. Delete everything else. |
| Missing Key Takeaways | Always add `## Key Takeaways` with 3-5 bullets at the end. |
| Over-summarizing content | raw/ stores raw material — keep the details |
| Fetching repo metadata (stars, etc.) | Just save the README. Metadata extraction is compile's job. |
| Wrong category | articles/ = web, repos/ = github.com, notes/ = session insights |
