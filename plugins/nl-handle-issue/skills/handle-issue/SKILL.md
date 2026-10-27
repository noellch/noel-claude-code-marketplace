---
name: handle-issue
description: Use when assigned an issue, bug report, error message, traceback, or support ticket — classifies scope, routes to the owning nl-* skill, and makes sure every step runs to completion. Not for feature requests (those start at nl-grill or nl-research-plan-execute).
---

# Handle Issue

Single entry point for issue resolution: **intake → classify → route → ensure completion**.

**Boundaries:** this skill is a router. It does not teach debugging, planning, execution, review, verification, or PR mechanics — each flow delegates to the owning skill and only checks that the step actually happened:

| Step | Owner |
|------|-------|
| root-cause investigation | `nl-debug` |
| Asana support-ticket intake + diagnosis | `cl-support:triage` |
| plan → tickets → execute → verify (large) | `nl-research-plan-execute` |
| verification before any "done" claim | `nl-verify` |
| commit / PR | `nl-create-pr` (FoD scope gate) |

## Phase 1: Intake

| Input | Action |
|-------|--------|
| Asana **support** ticket URL (Support project, or a customer-reported bug — when unsure, ask) | Run `cl-support:triage` first — it owns intake and diagnosis. Its root cause **replaces** the flow's Investigate step: resume at Phase 2, then go straight to the Investigation Report. |
| Other Asana task URL | Fetch via Asana MCP |
| GitHub issue URL | `gh issue view` |
| Sentry issue URL | Fetch via Sentry MCP — event, stack, frequency |
| Slack thread link | Read the thread; keep the link as the issue's key (ticket numbers in the thread may be reused) |
| Error message / traceback | Identify the service from the stack |
| Verbal description | Ask clarifying questions if ambiguous |

If intake shows nothing is broken — the request is for new behaviour — stop: that is a feature, hand it to `nl-grill` (unclear requirements) or `nl-research-plan-execute` (spec exists).

**Output:** one-paragraph problem statement — what's broken, which service(s), who's affected.

## Phase 2: Classify Scope

Classify on signals visible **at intake**, not on file counts you can't know yet:

| Size | Signals |
|------|---------|
| **SMALL** | Single service; the error or report already points at a location; no new API, page, or migration |
| **MEDIUM** | Single service; cause unknown, needs investigation; no new API, page, or migration |
| **LARGE** | Crosses services, needs a new API / page / DB migration, or decomposes into 3+ independent tasks |

Tell the user, in their language: *"This looks like a [SMALL/MEDIUM/LARGE] issue — using the [flow] workflow."* If uncertain, ask.

Classification is provisional until the Investigation Report — see **Re-scope** below.

## Flow A: Quick Fix (SMALL)

```
1. Debug     → nl-debug (root cause, not symptom)
2. Report    → Investigation Report (2-sentence version is fine)
3. Fix       → edit code directly
4. Verify    → nl-verify
5. Deliver   → nl-create-pr, only when asked
```

No plan. Small fixes need a correct diagnosis, not a document.

## Flow B: Investigate & Fix (MEDIUM)

```
1. Investigate → nl-debug (errors / tracebacks)
                 or nl-asana-ticket:analyze-issue (tickets not already triaged)
2. Report      → Investigation Report — get user confirmation
3. Plan        → 3-7 steps in the conversation: files to change, what each change does
                 Get user confirmation before touching code
4. Fix         → work through the plan
5. Verify      → nl-verify
6. Deliver     → nl-create-pr, only when asked
```

Step 4 has no built-in test cadence — project rules and `nl-verify` decide when checks run.

## Flow C: Plan & Build (LARGE)

```
1. Investigate → as Flow B step 1
2. Report      → Investigation Report — get user confirmation
3. Hand off    → nl-research-plan-execute, with the report as input
                 It owns research → plan → tickets → execute → verify
                 (fresh implementer + reviewer per task; never self-review)
4. Ensure      → confirm the pipeline reached nl-verify; delivery happens only from its menu, only when asked
```

Nothing else. If you find yourself writing execution or review steps here, you are duplicating the owning skill.

## Investigation Report (all flows)

Present this **before** any fix, and do not enter Plan / Fix until root cause is attributed. If attribution is still open after a focused ~30-minute effort, say so and ask — do not start designing a fix around a guess.

```
## Investigation Report

**Root Cause:** [one sentence — the cause, not the symptom]

**Measured:** [facts with evidence — file:line, command output, log excerpt]
**Inferred:** [conclusions drawn from the measured facts, labelled as inference]

**Ruled out:** [what was checked and why it is not the cause]

**Confidence:** [High / Medium / Low — tied to what is measured vs inferred]

**Affected files:** [path:line for each change point]
```

Two purposes: the user validates the reasoning before code changes, and the record survives the session.

## Re-scope

Re-check after the Investigation Report, in either direction:

| Current flow | Finding | Action |
|--------------|---------|--------|
| SMALL | 5+ files to change | → MEDIUM |
| SMALL or MEDIUM | Root cause is in another service | → LARGE |
| SMALL or MEDIUM | Needs a new API, page, or DB migration | → LARGE |
| MEDIUM | Investigation ends in a one-line fix with a known location | → SMALL |

Tell the user: *"Scope changed — moving to [flow]."*

## Deliver (all flows)

Never auto-commit. `nl-verify`'s finishing menu owns the deliver prompt; this skill only guarantees that nothing is committed or pushed until the user picks "deliver" or says "commit" / "PR".

## What NOT to Do

| Temptation | Why it's bad |
|------------|-------------|
| Skip debugging, jump to fixing | Fixes the symptom, not the cause |
| Skip the plan for a MEDIUM issue | Changes cascade without a map |
| Self-review or self-verify the changeset | Owner skills dispatch fresh reviewers |
| Re-describe execution / review steps in Flow C | Duplicates `nl-research-plan-execute` and drifts from it |
| Auto-commit after fixing | User may want to review first |
| Stay in Quick Fix when it's clearly bigger | Scope creep without structure |
| Write a 20-step plan for a 2-file fix | Over-engineering the process |
