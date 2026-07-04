---
name: grill
description: Relentless, one-question-at-a-time interrogation that turns a rough idea into an approved, written spec — pressure-tests intent, separates problem from solution, and refuses to build until shared understanding is reached. Type /nl-grill before building a feature.
disable-model-invocation: true
---

# Grill

## Overview

Turn a rough idea into an approved spec by **grilling** — relentless, one-question-at-a-time interrogation down the decision tree, refusing to build until you and the user share the same picture.

Two disciplines fused:
- **The grill** (depth) — no vague assumption survives the interview.
- **The pipeline** (breadth) — context → approaches → sectioned design → written spec → handoff.

## The gate (HARD)

Do NOT write code, scaffold, or take any implementation action until a design is presented AND the user approves it. "Too simple to need a design" is the trap: simple-sounding features are where unexamined assumptions cost the most. The design can be short; approval is never optional.

## Grilling — the rules

- **One question at a time.** Never batch. Multiple questions in one message is bewildering — ask, wait for the answer, then ask the next. (This is the rule that breaks first under pressure; hold it hardest.)
- **Separate problem from solution.**
  - **Problem questions** (purpose, who it's for, success criteria, hard constraints): grill these FIRST, with **no recommended default** — a default here anchors the user and smuggles a solution before the problem is agreed. Make them answer.
  - **Solution questions** (tech, storage, phasing, trade-offs): only after the problem is locked. Each carries your **recommended answer + why**, so the user edits instead of authors.
- **Walk the decision tree in dependency order** — resolve upstream choices before the ones that depend on them.
- **Explore, don't ask, when the codebase can answer.** Read the code instead of spending a question.
- **Relentless until shared understanding.** Don't stop at the first plausible answer. "Simple" is the user's *hope* about complexity, not a *fact* about scope — grill the scope anyway (how many, naming, edit/delete, defaults, edge cases).

## Process (the spine)

Each step ends on a checkable completion criterion.

1. **Explore context** — read files, docs, recent commits; assess scope. Multiple independent subsystems? Decompose first, then grill the first piece.
   *Done when:* you can state the goal + constraints in one paragraph, or you've flagged the decomposition.
2. **Grill the problem** — interrogate purpose / users / success / constraints per the rules, one at a time, no defaults, until no material ambiguity remains.
   *Done when:* you and the user share one problem statement; nothing load-bearing is left as "we'll figure it out later".
3. **Propose 2-3 approaches** — trade-offs + your recommendation; lead with the recommended one.
   *Done when:* the user picks or refines an approach.
4. **Present design in sections** — scale each to its complexity (architecture, components, data flow, errors, testing); get approval per section.
   *Done when:* the user approves every section.
5. **Write the spec** — save to `docs/**/YYYY-MM-DD-<topic>-design.md` (or the repo's convention). Self-review for placeholders, contradictions, scope creep, ambiguity; fix inline. Ask the user to review the file.
   *Done when:* the spec is committed and the user approves the written spec.
6. **Hand off to planning** — point to `nl-research-plan-execute` (or `superpowers:writing-plans`). Do NOT start implementing here.

## Red flags — STOP

- Asked more than one question in a single message
- Attached a recommended default to a problem/purpose question (anchoring)
- Let the word "simple" shrink how much you grilled the scope
- Started designing before context was explored, or building before the spec was approved
- Asked something the codebase already answers
- Skipped the written spec because "it's obviously simple"

## Rationalization table

| Excuse | Reality |
|---|---|
| "I'll batch the questions to save round-trips" | Batching is bewildering and lets the user skip the hard ones. One at a time, every time. |
| "The user said it's simple, so keep it light" | "Simple" is their hope about complexity, not a fact about scope. Grill the scope anyway. |
| "I'll give a default so they can just confirm" | Fine for solution choices; on the *problem* a default anchors them and hides an unmade decision. No defaults on purpose/constraints. |
| "It's small, we don't need a written spec" | Small features hide the most unexamined assumptions. Short spec — but written and approved. |

## YAGNI

Cut unneeded features from every design. The spec captures the smallest thing that meets the goal — nothing speculative.

---

*Synthesizes superpowers `brainstorming` (the context → approaches → sectioned design → spec → review pipeline) and Matt Pocock's `grilling` / `grill-me` / `grill-with-docs` (relentless one-at-a-time interrogation down the decision tree). The problem-vs-solution split — no defaults on problem questions — is a refinement surfaced by baseline testing, and improves on both sources.*
