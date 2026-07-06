---
name: index
description: Map of the nl-* skills — which one to reach for in a given situation, how they chain, and where they collide or leave gaps. Type /nl-index when you're unsure which skill fits.
disable-model-invocation: true
---

# nl-index — which skill, when

A map from situation → skill. Several nl-* skills are **user-invoked** (grill, handoff, writing-skills, this one) — the agent can't see or auto-fire them, so this is how you remember they exist and pick the right one.

## The feature flow (happy path, in order)

```
idea → spec → domain → plan → build → deliver → review
```

- `/nl-grill` — rough idea → approved written spec (relentless one-at-a-time questioning)
- `nl-domain-modeling` — capture the terms + hard-to-reverse decisions as glossary/ADR (runs *alongside* grill)
- `nl-research-plan-execute` — spec → researched, annotated plan → subagent execution (3+ task features)
- `/nl-plan-to-tickets` — slice the plan into vertical-slice (tracer-bullet) tickets, in dependency order
- `nl-create-pr` → `nl-stack-pr` — ship as FoD PRs; manage the stack as they merge
- `nl-pr-comment-resolve` — address review feedback

## Situation → skill

| When you're… | Reach for | Don't confuse with |
|---|---|---|
| unsure of requirements for a new feature | `/nl-grill` | RPE (comes *after* grill, not instead) |
| pinning down domain terms / hard decisions | `nl-domain-modeling` | grill (grill *elicits*, this *records*) |
| planning a 3+ task feature | `nl-research-plan-execute` | grill (spec first, then this) |
| learning an article to **retain** it | `nl-learn` | resource-digest (opinion) / lecture-walkthrough (slides) |
| wanting a **critical take** on a public URL/repo | `nl-resource-digest` | learn (retention) |
| studying **PDF slides** page-by-page | `nl-lecture-walkthrough` | learn / resource-digest |
| saving / compiling knowledge for later | `nl-kb` | learn (one-off study) |
| fixing a **tracked issue** end-to-end | `nl-handle-issue` | — |
| debugging a **hard / intermittent** bug or perf regression | `nl-debug` | handle-issue (whole lifecycle; this is the debug engine) |
| reviewing code / a PR | `nl-code-review` | repo-specific rubato/grazioso reviewers |
| creating / stacking PRs | `nl-create-pr` / `nl-stack-pr` | — |
| breaking an approved plan into tickets | `/nl-plan-to-tickets` | asana-ticket (formats ONE ticket; this decides the slices) |
| checking docs vs code drift | `nl-living-docs` | — |
| querying BigQuery | `nl-bq-analysis` | — |
| drawing a diagram in the terminal | `nl-terminal-diagrams` | — |
| creating an Asana ticket | `nl-asana-ticket` | — |
| wrapping up mid-task for a fresh session | `/nl-handoff` | — |
| authoring / editing a skill | `/nl-writing-skills` | — |
| curating a Spotify playlist | `nl-playlist-curation` | — |

## Collision notes (the pairs that actually get mixed up)

- **learn vs resource-digest vs lecture-walkthrough** — same input (content), different *intent*: **retain** / **critique** / **slide-teach**. Match on the verb, not the input.
- **grill vs domain-modeling vs research-plan-execute** — a pipeline, not rivals: grill (elicit the spec) → domain-modeling (record terms + decisions) → RPE (plan + execute).

## Known gaps (no skill yet)

- No open gaps in the core flow. Debugging → `nl-debug` (loop-first for hard bugs, extends `superpowers:systematic-debugging`); plan → tickets → `/nl-plan-to-tickets`. Add new gaps here as they surface.

## Invocation cheat-sheet

- **You must type these** (user-invoked, agent can't auto-fire): `/nl-index`, `/nl-grill`, `/nl-handoff`, `/nl-writing-skills`
- **Auto-fire or reference** (model-invoked): everything else, including `nl-domain-modeling`

*Keep this map in sync when you add, remove, or repurpose an nl-* skill.*
