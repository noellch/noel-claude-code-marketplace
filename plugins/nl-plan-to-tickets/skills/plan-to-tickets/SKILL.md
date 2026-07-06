---
name: plan-to-tickets
description: Slice an agreed feature plan or spec into independently-shippable, vertically-sliced (tracer-bullet) tickets and publish them to the tracker in dependency order. Use when an approved plan or spec needs breaking into work items — e.g. right after nl-research-plan-execute or nl-grill produces a plan, or when the user asks to slice a plan into tickets, break down a plan, create tickets/tasks from a plan, or make Asana tasks from a plan. Also invocable directly as /nl-plan-to-tickets.
---

# Plan to Tickets

## Overview

Turn an agreed plan into tickets a team (or agent) can each grab and ship alone. The one decision that matters: **slice vertically (tracer bullets), not by layer.**

A **tracer bullet** is a thin slice that goes all the way through — model + endpoint + UI for ONE capability — and ships something demoable on its own. The opposite (a "do all the DB" ticket, a "do all the API" ticket) back-loads every bit of value to the last ticket and blocks everyone until then.

## The core rule

```
✗ Horizontal (by layer):    [all DB] → [all API] → [all client] → [all UI]   value arrives last
✓ Vertical (by capability): [save a filter, end-to-end] · [load one] · [delete one]   each ships value
```

Slice by **user-visible capability**, not by architectural layer or repo. A slice may cross repos (backend + frontend) — that's fine; the *ticket* is the capability, and the PRs under it can still be per-repo.

## Steps

1. **Find the walking skeleton** — the smallest slice that goes end-to-end and proves the whole path works (e.g. "save one filter and see it appear in the list"). It's ticket 1; it's allowed to be ugly, but it ships.
   *Done when:* ticket 1 is a thin end-to-end slice, not a layer.
2. **Slice the rest by capability** — each remaining ticket a demoable user action (load, delete, rename, share…), touching whatever layers it needs.
   *Done when:* every ticket ships something a user or PM could see demoed; none is a pure layer.
3. **Order by TRUE dependency only** — most slices run in parallel once the skeleton exists. Don't invent a straight chain.
   *Done when:* the dependency graph is as flat as the real constraints allow.
4. **Write each ticket** using the [ticket template](references/ticket-template.md) — goal (user-visible), scope (layers/repos it touches), acceptance (how you'd demo it), dependencies, PRs-under-it. Fill the template's sections, then hand it to `nl-asana-ticket` to render as `html_notes` and publish.
   *Done when:* each ticket is grabbable cold, is a small reviewable PR (or a short per-repo PR stack), and they're in the tracker in dependency order.

## The ticket template

Every ticket follows [`references/ticket-template.md`](references/ticket-template.md). The template exists to force the vertical framing: the **title is a capability** (a user action), **Goal** is user-visible, **Acceptance** is a concrete demo, and per-repo PRs live *under* the one capability ticket. If a filled template's title reads like a layer ("add the model"), the slice is wrong — re-slice before publishing.

## Red flags — STOP

- A ticket named "the model" / "the endpoints" / "the client" — that's a layer, not a slice
- Nothing is demoable until the last ticket (value back-loaded)
- A straight N-deep dependency chain when the slices are actually parallel
- Splitting horizontally "because it makes cleaner PRs" or "because it's two repos"

## Rationalization table

| Excuse | Reality |
|---|---|
| "Layers make small, clean PRs" | Vertical slices are also small and reviewable — AND each ships value. You don't trade one for the other. |
| "The backend must be fully built first" | Only the *slice's* backend, not all of it. Build the one endpoint this capability needs. |
| "It's two repos, so split backend and frontend tickets" | The ticket is the capability; it can span repos and still be one vertical slice. Per-repo PRs live under it. |
| "Chain everything to be safe" | A chain kills parallelism. Order only by real dependency; let the rest run in parallel. |

## Pairs with

Upstream: `nl-grill` / `nl-research-plan-execute` produce the plan. Downstream: `nl-asana-ticket` formats each ticket; `nl-create-pr` / `nl-stack-pr` ship them.
