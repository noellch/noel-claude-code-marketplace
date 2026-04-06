---
name: resource-digest
description: Use when the user provides public URLs, articles, blog posts, GitHub repos, tweets, or tech news and asks to summarize, analyze, organize, or review them. Triggers on "幫我整理", "summarize this", "分析這篇", "整理重點", "看一下這個", or when user pastes URLs with analysis intent.
---

# Resource Digest

## Overview

Analyze public resources as a **critical analyst**, not a summarizer. The user wants your opinions, not just a restatement of what the resource says.

## When to Use

- User provides one or more URLs/resources and asks for analysis
- User shares articles, blog posts, GitHub repos, tweets, tech news
- User says "幫我整理", "分析", "看一下", "整理重點", "summarize"

## Core Principle

**Summarize → Opine → Advise.** Every resource analysis must contain all three layers. If you only summarize, you've done one-third of the job.

## Dispatch Strategy

**Check how many resources before starting:**

```
1 resource  → Analyze directly in this session
2+ resources → Dispatch parallel subagents (one per resource), then synthesize
```

**For 2+ resources, use `superpowers:dispatching-parallel-agents`:**

1. Dispatch one subagent per resource with the full per-resource analysis template below
2. Each subagent returns: Metadata Card + Summary + Critical Analysis + Pros/Cons + Key Insights + Recommendations
3. Collect all outputs, then produce the **Multi-Resource Synthesis** section yourself

This cuts analysis time proportionally — 3 resources analyzed in parallel takes the same time as 1.

## Per-Resource Analysis Flow

For EACH resource, produce these sections in order:

### 1. Metadata Card

Start with a quick-reference card. Adapt fields by resource type:

**Article / Blog Post:**
```
| 欄位 | 值 |
|------|-----|
| 類型 | Blog Post / Article / Guide |
| 作者 | Name — brief background if notable |
| 發布日期 | YYYY-MM-DD or approximate |
| 預估閱讀 | N min |
| 可信度 | High / Medium / Low — why |
```

**GitHub Repo:**
```
| 欄位 | 值 |
|------|-----|
| 類型 | GitHub Repository |
| 維護者 | Org/Person |
| Stars / Forks | N / N |
| 最近活躍度 | Active / Stale / Archived |
| 語言組成 | Top 3 languages with % |
| License | MIT / Apache / etc |
```

**Tweet / Social Post:**
```
| 欄位 | 值 |
|------|-----|
| 類型 | Tweet / Social Post |
| 作者 | @handle — brief background |
| 發布日期 | YYYY-MM-DD |
| 互動數據 | Likes / Retweets if available |
```

Adapt or merge fields as needed. The goal is instant context.

### 2. Content Summary (摘要)

Concise extraction of key points. Use bullet points or sub-sections.

- Focus on the CORE arguments, not every detail
- Highlight data, evidence, and concrete examples the resource provides
- For GitHub repos: focus on architecture, design philosophy, key features, and ecosystem positioning

### 3. Critical Analysis (分析觀點)

**This is the most important section.** Clearly label as your own analysis.

Use the heading: `### 我的觀點`

Address:
- **What's strong** — what arguments/evidence are compelling and why
- **What's weak or missing** — gaps in reasoning, missing evidence, unstated assumptions, potential biases
- **Counterpoints** — what the resource doesn't address, opposing viewpoints
- **Context** — how this fits into the broader landscape, what the resource's position/angle is

### 4. Pros & Cons

Structured comparison. Always include both sides.

```
**Pros:**
- ...

**Cons / Limitations:**
- ...
```

For GitHub repos, this covers: technical strengths vs weaknesses, ecosystem advantages vs lock-in risks.
For articles, this covers: argument strengths vs logical gaps.

### 5. Key Insights

Non-obvious takeaways the user might miss from a casual read. Mark clearly:

```
> 💡 **Insight:** [non-obvious observation that adds value beyond the resource itself]
```

Limit to 1-3 per resource. Quality over quantity.

### 6. Actionable Recommendations (建議)

Concrete next steps the user could take. Be specific to THEIR context when possible.

```
**建議：**
- ...
```

## Multi-Resource Synthesis

When analyzing 2+ resources, add a final synthesis section AFTER all individual analyses:

### 綜合分析

Structure:
1. **Common themes** — what these resources agree on
2. **Contradictions** — where they disagree and who has the stronger argument
3. **Landscape positioning** — how these resources relate to each other (competition, complementary, different angles on same problem)
4. **Combined insights** — insights that emerge from reading these TOGETHER that wouldn't be obvious from any single resource
5. **Overall recommendation** — what the user should take away and do

## Resource Type Adaptations

Different resource types need different analytical lenses:

| Resource Type | Primary Lens | Secondary Lens |
|---------------|-------------|----------------|
| Blog / Article | Argument quality, evidence | Author credibility, bias |
| GitHub Repo | Architecture, adoption, maintenance | Ecosystem fit, alternatives |
| Tweet / Thread | Signal vs noise, context | Author expertise, engagement |
| Tech News | Factual accuracy, implications | Source bias, hype vs substance |
| Research Paper | Methodology, reproducibility | Practical applicability |
| Documentation | Completeness, clarity | Maintenance status, gaps |

## Fetching Strategy

- Use WebFetch for URLs. If blocked (e.g., Twitter/X), try alternative endpoints (fxtwitter.com/[user]/status/[id] for tweets)
- For GitHub repos: fetch README + check repo metadata (stars, language, recent commits)
- For paywalled content: acknowledge the limitation, analyze what's available
- If a URL is dead or redirects: report this clearly, don't hallucinate content

## Language

- Default output: Traditional Chinese (繁體中文)
- Technical terms, proper nouns, code: keep original form
- Section headings: use Chinese headings as shown above

## Common Mistakes

| Mistake | Correct Approach |
|---------|------------------|
| Pure summarization without opinions | MUST include 我的觀點 section with genuine critical analysis |
| Generic insights anyone could write | Insights should be specific, non-obvious, and contextual |
| Skipping pros/cons | Always include structured pros/cons even if resource seems purely positive |
| Same template for all resource types | Adapt metadata card and analytical lens by resource type |
| Vague recommendations ("值得關注") | Specific actionable steps ("可以先 fork 這個 repo 試跑 example/") |
| Missing limitations/bias assessment | Every resource has a perspective — identify it |
