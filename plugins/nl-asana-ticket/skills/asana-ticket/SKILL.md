---
name: asana-ticket
description: Use when creating Asana tasks, tickets, or bugs. Triggers on "create ticket", "open bug", "add task to Asana", or when discussing issues that need tracking.
userInvocable: asana-ticket
---

# Asana Ticket Creation

Standardized workflow for Crescendo Lab Asana tickets. Every ticket MUST follow this skill — do not invent formats, guess GIDs, or add extra sections.

## Defaults (ALWAYS set)

- **Assignee**: Noel Lo (`1208315391502342`)
- **Workspace**: `1184020052539844`
- **Team**: Engineering (`1184810254601745`)

## Project Routing (MANDATORY)

```
QA found the bug?
  → Yes: QA Bug Tracking (1204020418145442)
  → No: Technical debt / refactoring?
    → Yes: Technical Debt (1185615876101081)
    → No: MAAC (1206764649948244) [DEFAULT]
```

Do NOT put tech debt in MAAC. Do NOT put QA bugs in MAAC.

## Title Format (EXACT prefixes)

```
[FE] Task description      # Frontend task
[BE] Task description      # Backend task
[Bug] Issue description    # Bug report
[Debt] Improvement         # Technical debt
```

Use exactly ONE prefix per title. Not `[Tech Debt]`, not `[Issue Ticket]-[...]`, not `[PoC]`, not `[FE][Debt]`. One bracket, one prefix.

## Description Format

Always render the body as `html_notes` (rich text) — plain `notes` collapses all formatting. Must be well-formed XML with a single `<body>` root; Asana allows only `<body> <h1> <h2> <ol> <ul> <li> <strong> <em> <u> <s> <code> <a> <blockquote> <pre>`.

**The body sections depend on who is calling this skill:**

- **Caller-provided body** — when another skill hands you a body (e.g. `plan-to-tickets` provides a capability template: Goal / Scope / Acceptance / Dependencies), render THAT body as-is. Do NOT rewrite it into Context + DoD.
- **Standalone ticket** — when you are creating a bug / debt / task directly (no caller body), use the default **Context + DoD** structure below.

This skill owns the Asana **mechanics** — defaults, project routing, title prefix, custom fields, GIDs, `html_notes` rendering, and the create call — NOT one fixed body shape. Context + DoD is only the default for standalone tickets.

### Standard Task (default standalone body)
```html
<body><h2>Context</h2>
<ul>
<li><strong>Background</strong>: why this task exists</li>
<li><strong>Goal</strong>: what we want to achieve</li>
<li><strong>Impact</strong>: who benefits and how</li>
</ul>
<h2>DoD</h2>
<ul><li>Done criteria 1</li><li>Done criteria 2</li></ul></body>
```

### Bug Report
```html
<body><h2>Context</h2>
<ul>
<li><strong>Background</strong>: where/when the issue was found</li>
<li><strong>Impact</strong>: how it affects users/business</li>
</ul>
<h2>Steps</h2>
<ol><li>...</li><li>...</li></ol>
<h2>Expected / Actual</h2>
<ul><li><strong>Expected</strong>: ...</li><li><strong>Actual</strong>: ...</li></ul>
<h2>DoD</h2>
<ul><li>Bug fixed</li><li>Tests pass</li></ul></body>
```

### Technical Debt
```html
<body><h2>Context</h2>
<ul>
<li><strong>Background</strong>: current problem</li>
<li><strong>Goal</strong>: what improvement we want</li>
<li><strong>Impact</strong>: why this matters</li>
</ul>
<h2>DoD</h2>
<ul><li>Improvement completed</li></ul></body>
```

Do NOT add extra sections (Requirements, Scope, Technical Considerations, References, etc.). Context + DoD is enough.

## Required Custom Fields by Project

### MAAC (Default)
- **Pod** (`1208604841142299`): Pod1 (`1208604841142300`) — ALWAYS set
- **Priority** (`1208995072777850`): optional
- **Scope** (`1207875081141332`): optional
- **Story point** (`1208990990125330`): optional, 1 point = half day

### QA Bug Tracking
- **Severity** (`1204009725716403`): MUST set — see `references/custom-fields.md`
- **Bug Status** (`1204009725716412`): MUST set to "New" (`1204009725716413`)
- **Tester** (`1204009725716409`): MUST set to QA who found it

Do NOT use Issue Ticket fields (Priority, Service Level, Type, Product, Feature) for QA bugs. They are different projects with different fields.

### Technical Debt
- **Priority** (`1199571543088674`): MUST set — see `references/custom-fields.md`
- **Scale** (`1199571543088662`): MUST set
- **Type** (`1199571543088684`): MUST set
- **Group** (`1202588865650178`): MUST set

All GID mappings are in `references/custom-fields.md`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Assignee left null | Always set Noel Lo (`1208315391502342`) |
| Pod not set for MAAC | Always set Pod1 (`1208604841142300`) |
| Tech debt in MAAC project | Use Technical Debt (`1185615876101081`) |
| `[Tech Debt]` prefix | Use `[Debt]` |
| `[Issue Ticket]-[...]` format | Use `[Bug]` |
| `[FE][Debt]` double prefix | Use `[Debt]` only — one prefix per title |
| Using plain text `notes` | Use `html_notes` (rich text) |
| 6-section description | Context + DoD only |
| QA bug missing Severity/Bug Status | Both are mandatory |
| Mixing fields across projects | Each project has its own fields |
