---
name: lecture-walkthrough
description: Use when user provides a PDF lecture, presentation, or slide deck and wants to learn the content through guided page-by-page teaching. Triggers on "teach me", "walk me through", "help me study", or when a PDF slide path is given with learning intent.
---

# Lecture Walkthrough

Guided page-by-page teaching from PDF slide decks, with project-contextualized insights and comprehensive study notes generation.

---

## When to Use

- User provides a PDF path and wants to **learn** (not just summarize)
- User says "teach me", "walk me through", "help me study", "bring me through each page"
- PDF is a lecture/presentation (slide aspect ratio, image-based content)

> 🚫 **Not for:** API docs, reference manuals, text-heavy PDFs → use `resource-digest` instead

---

## Process

### 📥 Phase 1 — Ingest PDF

| Step | Action | Command |
|:----:|--------|---------|
| 1 | Check `pdftoppm` availability | `which pdftoppm` — if missing, offer `brew install poppler` |
| 2 | Get PDF metadata | `pdfinfo <file>` — page count, dimensions |
| 3 | Convert to PNG (batches of 5) | `pdftoppm -png -r 100 -f N -l M <file> /tmp/<slug>_pages/page` |
| 4 | Store images | `/tmp/<slug>_pages/` |
| 5 | **Read ALL pages visually** | Use Read tool on each PNG before proceeding |

---

### 🗺️ Phase 2 — Overview

Provide a high-level summary so the user knows what they're about to learn:

```
┌─────────────────────────────────────────────────┐
│  📄 Metadata Card                               │
│  Source · Page count · Topic · Audience · Cred.  │
├─────────────────────────────────────────────────┤
│  📑 Page-by-Page Topic Table                    │
│  | Page | Title | One-line summary |             │
├─────────────────────────────────────────────────┤
│  🔍 Critical Analysis                           │
│  Strengths · Weaknesses · Missing · Context      │
└─────────────────────────────────────────────────┘
```

---

### 📖 Phase 3 — Page-by-Page Walkthrough

> ⚠️ **Hard rule:** Go one page at a time. **Wait for user confirmation before advancing.**

For each page, output this template:

```markdown
## 📄 Page N — [Title]

[Core concept explanation]
- Use ASCII diagrams to visualize structures
- Use real-world analogies (building/room/desk, highway/city driving)
- Show before/after comparisons when applicable

★ Insight ─────────────────────────────────────
- 🎯 Non-obvious takeaway specific to the concept
- 🔗 How this connects to user's codebase/tech stack
  (auto-detect from CLAUDE.md, project structure, conversation)
- 💻 Practical command or code snippet they can try
─────────────────────────────────────────────────

➡️ "Page N+1 will cover [preview]. Ready?"
```

#### 💬 Handling Q&A

When the user asks a question mid-walkthrough:
1. Answer thoroughly with the same teaching style
2. Connect back to the current slide's context
3. Resume walkthrough position after answering — don't lose your place

---

### 📝 Phase 4 — Study Notes Generation

When all pages are covered, generate a comprehensive Markdown file.

| Property | Value |
|----------|-------|
| **Location** | Same directory as the source PDF |
| **Filename** | `<PDF_name_without_extension>_Notes.md` |

**Required sections in the notes file:**

```
📋 Table of Contents (with anchor links)
├── Per-page sections (full explanations + diagrams + insights)
├── Q&A sections (all questions asked during walkthrough)
├── 🧠 Complete Mental Model (diagram connecting all concepts)
├── 🛠️ Practical Takeaways (symptoms table, commands, design rules)
└── 📚 Further Reading (specific resources, not generic)
```

---

## Key Patterns

### 🎯 Project Context Detection

Read CLAUDE.md and conversation history to identify:

| Signal | How to use it |
|--------|---------------|
| Tech stack (e.g. Django/Postgres) | Relate to DB internals, ORM implications |
| Services user works on (e.g. Rubato) | Mention Django ORM edge cases |
| Current concerns (e.g. performance) | Emphasize optimization angles |

Use these to make **every insight actionable and relevant** to the user's actual work.

### 📊 ASCII Diagrams

Prefer text-based diagrams for:

| Concept Type | Example |
|-------------|---------|
| Data structures | Page layout, tuple structure |
| Hierarchies | Architecture stacks, nesting |
| Flows | Query execution path, I/O patterns |
| Comparisons | Before/after, good/bad |

### ⏱️ Pacing

```
Pages 1-2 (cover + intro)  → combine in one message (usually light)
Content-heavy slides        → one page per message
Every message               → end with preview of next page
Always                      → let user control pace, never auto-advance
```

---

## Common Mistakes

| | Mistake | ✅ Fix |
|:--:|---------|--------|
| 🔴 | Dumping all pages at once | One page at a time, wait for user |
| 🔴 | Generic textbook explanations | Always tie to user's specific tech stack |
| 🔴 | Skipping the overview phase | User needs the map before the journey |
| 🔴 | Notes file missing Q&A content | Include all mid-walkthrough questions and answers |
| 🔴 | Insights that are obvious | Focus on non-obvious connections to user's actual work |
| 🔴 | Forgetting to generate notes | Always offer notes generation after completing all pages |

---

## Language

- 🇹🇼 All teaching output in **Traditional Chinese** (繁體中文)
- Technical terms, code, and commands stay in original form
- Study notes follow the same language convention
