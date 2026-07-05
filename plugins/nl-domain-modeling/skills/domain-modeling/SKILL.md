---
name: domain-modeling
description: Use when starting or reshaping a feature or module and the domain's shared language or hard-to-reverse decisions aren't pinned down yet — before or during design, or when the same concept is getting named inconsistently across code, PRs, and teams.
---

# Domain Modeling

## Overview

The domain model lives in **files**, not in the conversation. If the shared language and the decisions exist only in chat, they evaporate — three weeks later nobody can answer "what does *Plan* mean here?" or "why did we choose X?".

Two durable artifacts, each a **single source of truth**:
- a **glossary** (ubiquitous language) — one authoritative definition per term.
- **ADRs** — one durable record per hard-to-reverse decision.

## Rules

- **Harvest before you define.** Read the codebase and ask the user what the team *already* calls things. Ubiquitous language starts from the words the team uses — not a generic template you impose. Don't write a definition you assumed.
- **Ground by interrogation.** For a fuzzy or contested term, ask (one question at a time) until it means one thing to both of you. If nl-grill is available, use it to drive the questioning.
- **One term, one name.** The same concept must not be `Plan` in code, `Tier` in the PR, and `package` in support. Reconcile to a single name in the glossary.

## Steps

1. **Locate or create the glossary.** Find the repo's `CONTEXT.md` / domain-doc convention, or create one. Seed it by reading existing code and docs — real names first.
   *Done when:* the file exists and lists every load-bearing term with a one-line definition sourced from actual usage, not invented.
2. **Grill the ambiguous terms.** For each fuzzy or contested term, interrogate until the definition is agreed, then write it back to the glossary immediately.
   *Done when:* no load-bearing term carries two meanings; every entry is confirmed, not assumed.
3. **Record hard-to-reverse decisions as ADRs.** For each decision costly to undo (money representation, aggregate boundaries, build-vs-buy, state machine), write an entry: **status · decision · rationale · rejected alternatives · consequences**.
   *Done when:* every hard-to-reverse decision has a durable ADR entry; none live only in chat.
4. **Keep it the single source of truth.** When a term or decision changes, edit the file — not just the reply. Point code, PRs, and specs at the glossary/ADRs.
   *Done when:* the glossary + ADRs are where you'd send anyone to answer "what does X mean / why did we choose Y".

## Red flags — STOP

- Defined terms before reading the codebase or asking what the team already calls them
- The glossary or a decision lives only in the chat transcript
- A decision expensive to reverse was left as conversation, not an ADR
- The same concept appears under two different names

## What goes where

- **Term meaning →** glossary. **Decision + rationale →** ADR. Both are files; both are the single source of truth.

## Pairs with

Use alongside **nl-grill**: grilling produces the questions and the shared understanding; domain-modeling captures the answers as durable docs. That combination is the "grill-with-docs" pattern.
