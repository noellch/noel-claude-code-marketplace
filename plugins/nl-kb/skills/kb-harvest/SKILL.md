---
name: kb-harvest
description: Decide what — if anything — from the current session is worth persisting as memory, kb, or docs. High bar: keeping nothing is the expected result. User-invoked (/kb-harvest).
disable-model-invocation: true
---

# kb-harvest

## Overview

End-of-session triage: decide what, if anything, from this session deserves to persist — and refuse to force low-value saves. Front door only. Survivors are routed to their existing owners (the memory protocol in `~/.claude/CLAUDE.md`, `kb-collect`, `claude-md-management`); this skill does not re-implement their formats.

## The frame

Two rules override the instinct to capture:

**Do no harm.** A wrong or unverified memory makes future sessions *worse* — the opposite of the goal. Wrong knowledge costs more than no knowledge. So an unverifiable claim is never saved as fact.

**Earn its keep.** Nothing persists by default. "Nothing worth keeping this session" is the *expected* outcome, not a failure. Burden of proof is on saving, never on skipping. You are the skeptic reviewing candidates, not their advocate.

## Process

### Step 1 — List raw candidates
Skim the session. Enumerate every discrete thing that *could* be knowledge: a discovered fact, a decision, a preference Noel stated, a debugging conclusion, a project-state change. Don't filter yet.
*Done when:* every candidate is written as a one-line claim.

### Step 2 — Filter: Durable?
Drop anything that won't matter in a *different future session*:
- one-off trivia, conversational scaffolding
- a fix that now lives in git / the diff (the code is the record)
- anything true only for this specific task
*Done when:* only cross-session-relevant claims remain.

### Step 3 — Filter: New?
For each survivor, search before you trust — the memory index (MEMORY.md + files), the relevant CLAUDE.md, and `~/knowledge`:
- already there → drop, or mark "update existing X" (never duplicate)
- derivable from code / git / the CLAUDE.md service map → drop
*Done when:* each remaining claim is confirmed absent from all three stores.

### Step 4 — Gate: True? (the gate that stops harm)
Verify each survivor against ground truth, not the conversation:
- code/behavior claim → grep the code / read the file
- "we shipped X" / branch / status claim → check git
- doc/architecture claim → read the doc

If it can be verified only by "someone said so this session" → **do not save it as fact.** At most, record it as an explicitly-marked open question in kb — never as a memory reference.
*Done when:* every survivor is verified true, or dropped/demoted.

### Step 5 — Defend each survivor
Each remaining item must fill all three, one line each:
- (a) which future decision it changes
- (b) where it was verified true (step 4 evidence)
- (c) why it is not derivable from code / git / CLAUDE.md

Any blank → drop it.
*Done when:* every survivor has all three, or is gone.

### Step 6 — Route + persist
| Survivor kind | Destination | How |
|---|---|---|
| How to work with Noel / this env; should load every session | **memory** (user/feedback/project/reference) | write per the memory protocol in `~/.claude/CLAUDE.md`; the memory dir is self-editable → write directly, then report |
| Reusable, cross-project technical conclusion | **kb** `~/knowledge/raw/` | hand to `kb-collect`; do not hand-format |
| Project/architecture fact belonging with the code & team | **docs / CLAUDE.md** | propose the diff, wait for go (maintenance protocol) |

**Confirmation gate:** memory-dir writes may proceed autonomously. kb, repo docs, and any CLAUDE.md / settings change → show the proposed content and wait for Noel's explicit go.

### Step 7 — Report
State what was saved and where, and — always — what was considered and dropped, with the reason. If nothing survived, say "nothing worth keeping this session" plainly. That is a valid, common result.

## Rationalization table
| Excuse | Reality |
|---|---|
| "Capture everything so I improve" | Wrong saves make you worse. The bar exists *to* improve you. |
| "It was a hard-won insight" | Hard-won ≠ verified. If you can't confirm it against code/git/docs, it's a rumor. |
| "If in doubt, save it" | If in doubt, drop it. Doubt is a fail, not a tiebreak toward saving. |
| "It came up, so it's worth a note" | Coming up ≠ durable. Most of a session is scaffolding. |
| "I'll write it now and verify later" | Unverified goes in as an open question at most, never as a memory fact. |
| "There must be *something* to save" | No. Empty is the expected outcome for most sessions. |

## Red flags — STOP
- About to write a memory/kb entry sourced only from "the conversation said so"
- Producing a save for every topic that came up
- Feeling you must find at least one thing to keep
- Re-saving something already in MEMORY.md / CLAUDE.md / kb
- Writing to kb / docs / CLAUDE.md without showing Noel first
