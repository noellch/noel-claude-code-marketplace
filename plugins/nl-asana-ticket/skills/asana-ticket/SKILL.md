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

Use `notes` (plain text), NOT `html_notes`. Keep it short — Context + DoD only.

### Standard Task
```
Context:
- Background: Why this task exists
- Goal: What we want to achieve
- Impact: Who benefits and how

DoD:
- Done criteria 1
- Done criteria 2
```

### Bug Report
```
Context:
- Background: Where/when the issue was found
- Impact: How it affects users/business

Steps:
1. ...
2. ...

Expected: ...
Actual: ...

DoD:
- Bug fixed
- Tests pass
```

### Technical Debt
```
Context:
- Background: Current problem
- Goal: What improvement we want
- Impact: Why this matters

DoD:
- Improvement completed
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
| Using html_notes | Use plain text `notes` |
| 6-section description | Context + DoD only |
| QA bug missing Severity/Bug Status | Both are mandatory |
| Mixing fields across projects | Each project has its own fields |
