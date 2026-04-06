---
name: handle-issue
description: Use when assigned an issue, bug report, error message, or feature request — classifies scope and orchestrates the full lifecycle from investigation to PR creation
---

# Handle Issue

Single entry point for issue resolution. Classifies scope, selects the right workflow, and ensures every step is completed.

## Phase 1: Intake

Gather context from whatever the user provides:

| Input | Action |
|-------|--------|
| Asana ticket URL | Fetch ticket details via Asana MCP |
| Error message / traceback | Note the error, identify service |
| Verbal description | Ask clarifying questions if ambiguous |
| GitHub issue URL | Fetch issue via `gh issue view` |

**Output:** One-paragraph problem statement with: what's broken, which service(s), who's affected.

## Phase 2: Classify Scope

```
Assess the issue
  │
  ├─ Touches 1-2 files, clear fix?
  │   └─ SMALL — go to Quick Fix flow
  │
  ├─ Touches 3-10 files, needs investigation?
  │   └─ MEDIUM — go to Investigate & Fix flow
  │
  └─ Crosses services, needs new APIs/pages, or 3+ independent tasks?
      └─ LARGE — go to Plan & Build flow
```

Tell the user: **"This looks like a [SMALL/MEDIUM/LARGE] issue. I'll use the [flow name] workflow."**

If uncertain, ask the user.

## Flow A: Quick Fix (Small)

```
1. Debug          → Use: systematic-debugging
                     Find root cause, not just symptoms
2. Fix            → Edit code directly
3. Verify         → Run relevant tests
4. Deliver        → Use: commit (when asked)
```

**Skip planning.** Small fixes don't need plans — they need correct diagnosis.

## Flow B: Investigate & Fix (Medium)

```
1. Investigate    → Use: analyze-issue (if Asana ticket)
                     or systematic-debugging (if error/traceback)
                     If classified as bug: apply 5 Whys (see below)
                     Output: root cause + affected files list
2. Plan           → Write a short plan (3-7 steps) in the conversation
                     List files to change and what each change does
                     Get user confirmation before proceeding
3. Execute        → Fix step by step, verify after each change
4. Verify         → Run tests, type-check if relevant
5. Deliver        → Use: commit (when asked)
```

## Flow C: Plan & Build (Large)

```
1. Research       → Use: analyze-issue (if ticket)
                     Explore codebase to understand existing patterns
                     Identify all services/repos involved
2. Plan           → Use: research-plan-execute
                     Produces structured plan with independent tasks
                     User MUST confirm plan before execution
3. Execute        → Parallel subagents for independent tasks
                     Sequential for dependent tasks
4. Review         → Self-review the full changeset
5. Verify         → Run all relevant tests and checks
6. Deliver        → Use: commit-push-pr (when asked)
```

## 5 Whys — Bug Root Cause Depth Check (Flows A & B)

When the issue is classified as a **bug**, after identifying a candidate root cause, validate its depth before declaring it final:

Ask "Why did [X] happen?" up to 5 times. Stop early when you reach:
- A system/service boundary (external API, OS, network)
- A deliberate policy or business decision
- An external constraint outside your codebase

**If the 5th Why points to a different file or module than your initial diagnosis → re-scope the fix.** The original candidate was a symptom, not the cause.

Example:
```
Bug: "Checkout returns 500"
Why 1: payment service threw an exception
Why 2: exchange rate was None
Why 3: FX API returned empty response
Why 4: API key had expired
→ Root cause: key rotation was never automated (policy gap)
Fix scope: add key expiry monitoring, not just catch the exception
```

Show the Why chain in the Investigation Report's "How I reached this conclusion" section.

## Investigation Report (All Flows)

After completing the investigation/debug phase of ANY flow, present a structured report BEFORE moving to the fix:

```
## Investigation Report

**Root Cause:** [One-sentence description of the actual cause]

**Investigation Process:**
1. [First thing I checked and what I found]
2. [Second thing I checked and what I found]
3. [Key clue that led to the root cause]

**How I reached this conclusion:**
[Explain the reasoning chain — what evidence pointed where, what was ruled out, and why this is the root cause rather than a symptom]

**Confidence:** [High/Medium/Low — and why]

**Affected files:** [List of files that need changes]
```

This report serves two purposes:
1. The user can validate your reasoning before you start changing code
2. It creates a record of the investigation for future reference

**Do NOT skip this report.** Even for small fixes, a 2-sentence version is required.

## Deliver Phase (All Flows)

After the fix is verified, **do NOT auto-commit**. Instead:

1. Summarize what was changed and why
2. Wait for user to say "commit", "PR", or similar
3. Then use the appropriate commit/PR skill

## Red Flags — Upgrade the Flow

If during a Quick Fix you discover:
- The root cause is in a different service → upgrade to MEDIUM or LARGE
- There are 5+ files to change → upgrade to MEDIUM
- You need to create new APIs or pages → upgrade to LARGE

Tell the user: **"This is bigger than expected. Upgrading to [flow name]."**

## What NOT to Do

| Temptation | Why it's bad |
|------------|-------------|
| Skip debugging, jump to fixing | May fix symptom, not cause |
| Skip planning for medium issues | Changes cascade without a map |
| Auto-commit after fixing | User may want to review first |
| Stay in Quick Fix when it's clearly bigger | Scope creep without structure |
| Write a 20-step plan for a 2-file fix | Over-engineering the process |
