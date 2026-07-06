---
name: execute
description: Use when executing an approved plan of mostly-independent tasks in the current session — dispatch a fresh implementer subagent per task, review each (spec compliance + code quality), then a broad final review. The execute stage of research-plan-execute. Triggers on "execute the plan", "implement these tasks", "run the plan".
---

# Execute

Execute a plan by dispatching a **fresh implementer subagent per task**, a **task review** (spec + quality) after each, and a **broad final review** at the end.

**Why subagents:** you delegate each task to an agent with isolated context. You construct exactly what it needs — it never inherits your session history. This keeps each implementer focused and preserves your own context for coordination.

**Core principle:** fresh subagent per task + per-task review (spec + quality) + broad final review = high quality, fast iteration.

**Continuous execution:** do not pause to check in between tasks. Execute all tasks without stopping. Stop only for: a BLOCKED status you cannot resolve, genuine ambiguity, or all tasks complete. "Should I continue?" prompts waste the human's time — they asked you to execute.

Model-agnostic by design: a strong model improvises some of this; a weaker one, or a long/post-compaction session, drops tasks, pastes history, and re-does completed work. The discipline holds regardless.

## When to use

- Have an approved plan? → yes
- Tasks mostly independent? → yes; tightly coupled → reconsider slicing
- Staying in this session? → yes (for a separate parallel session, that's a different workflow)

Don't use for a single-file change or a plan that isn't approved yet.

If the plan's tasks span more than one repo, also apply **Multi-repo execution** below.

## The process

Per task:

1. Dispatch an **implementer subagent** with [references/implementer-prompt.md](references/implementer-prompt.md) — the task brief (as a file), the interfaces it touches, the global constraints, and the report-file path.
2. It asks questions? Answer completely before it proceeds.
3. It implements, tests (TDD), commits, self-reviews, writes its report file.
4. Generate the diff (below), dispatch a **task reviewer** with [references/task-reviewer-prompt.md](references/task-reviewer-prompt.md) — brief, report, diff, global constraints.
5. Reviewer reports two verdicts: **spec compliance** and **code quality**. Not approved → dispatch a fix subagent for Critical/Important findings → re-review. Loop until both pass.
6. Mark the task complete in the todo list and the progress ledger.

After all tasks: **broad final review** — hand the whole-branch diff to `nl-code-review`. Then hand off to `nl-verify` for verification + finishing.

## Pre-flight plan review

Before dispatching task 1, scan the plan once for conflicts: tasks that contradict each other or the global constraints; anything the plan mandates that the review rubric would flag as a defect. Present all findings as one batched question — each beside the plan text that mandates it — before execution, not one interrupt per discovery. Clean scan → proceed silently.

## Model selection

Use the least powerful model that can do each role.

- **Mechanical implementation** (1-2 files, complete spec, code in the plan): cheapest tier.
- **Integration / judgment** (multi-file, pattern-matching, debugging): standard tier.
- **Architecture / design, and the final broad review**: most capable tier.
- **Reviewers**: match the diff's size and risk; a mid-tier model is the floor.

**Always specify the model explicitly when dispatching** — an omitted model inherits your session's (often the most expensive), silently defeating this. Turn count beats token price: the cheapest models take 2-3× the turns on multi-step work, so use a mid-tier floor for prose-driven implementers and reviewers.

## Handling implementer status

- **DONE** — generate the diff, dispatch the task reviewer.
- **DONE_WITH_CONCERNS** — read the concerns first. Correctness/scope → address before review. Observations → note and proceed.
- **NEEDS_CONTEXT** — provide the missing context, re-dispatch.
- **BLOCKED** — assess: context problem → more context, same model; needs more reasoning → more capable model; too large → split; plan is wrong → escalate to the human. Never force the same model to retry unchanged.

## Handling reviewer "cannot verify from diff" items

The reviewer may flag requirements that live in unchanged code or span tasks. These don't block the rest of the review, but you resolve each yourself before marking the task complete — you hold the cross-task context the reviewer lacks. A confirmed gap is a failed spec review: send it back.

## Constructing reviewer prompts

- Do NOT add open-ended directives ("check all uses") without a concrete reason.
- Do NOT ask a reviewer to re-run tests the implementer already ran on the same code.
- **Do NOT pre-judge findings.** Never instruct a reviewer to ignore or downgrade an issue. If your prompt contains "do not flag", "at most Minor", or "the plan chose" — stop: you are pre-judging to spare yourself a loop. Let the reviewer raise it; adjudicate in the loop.
- The **global-constraints block** is the reviewer's attention lens: copy the binding requirements verbatim from the plan (exact values, formats, stated relationships).
- Dispatch fix subagents for **Critical and Important** findings. Record Minor findings in the ledger and point the final review at them. A roll-up nobody reads is a silent discard.
- A **plan-mandated** finding (or any finding that conflicts with the plan) is the human's call: present the finding and the plan text, ask which governs. Don't dismiss it, don't fix against the plan without asking.

## File handoffs

Everything you paste into a dispatch — and everything a subagent prints back — stays in your context for the rest of the session and is re-read every turn. Hand artifacts over as files:

- **Task brief** — extract the task's full text (from `plan.md`) to its own file; the dispatch points at it as "read this first — your requirements, exact values verbatim." Exact numbers, magic strings, signatures, and test cases live only in the brief.
- **Report file** — named after the brief (`task-N-brief.md` → `task-N-report.md`); the implementer writes the full report there and returns only status, commits, a one-line test summary, and concerns.
- **Reviewer inputs** — the brief, the report, and the diff file, plus the global constraints.
- **Never paste accumulated prior-task summaries** into later dispatches. A fresh subagent needs its task, the interfaces it touches, and the global constraints — nothing else.

### Diffs without bundled scripts (pure git)

Some skill frameworks ship helper scripts for this; this skill uses plain git so it stays self-contained. Write the review diff to a uniquely named file — the reviewer reads one file instead of re-deriving it, and the output never enters your context:

```bash
BASE=<commit recorded BEFORE dispatching the implementer>   # never HEAD~1 — it drops all but the last commit
{ git log --oneline "$BASE"..HEAD; echo; git diff --stat "$BASE" HEAD; echo; git diff -U10 "$BASE" HEAD; } > /tmp/review-task-N.diff
```

For the final broad review, use the branch's merge base: `BASE=$(git merge-base main HEAD)`.

## Durable progress ledger

Conversation memory does not survive compaction; controllers that lose their place re-dispatch completed tasks — the most expensive failure. Track progress in a file, not only in todos.

- At start, check for a ledger: `cat "$(git rev-parse --show-toplevel)/.nl-execute/progress.md"`. Tasks marked complete are DONE — resume at the first that isn't.
- When a task's review comes back clean, append one line: `Task N: complete (commits <base7>..<head7>, review clean)`.
- After compaction, trust the ledger and `git log` over your own recollection. `git clean -fdx` destroys the ledger (git-ignored scratch); recover from `git log`.

## Multi-repo execution

When the plan's tasks span more than one repository (a set of services, cross-repo
feature work), the single-branch assumptions above break. Apply these on top of the
per-task loop:

- **Detect early.** Tasks naming files in different repos, or a plan that states a
  cross-repo dependency graph = multi-repo mode. Say so in the pre-flight.
- **Per-repo branch + BASE.** Each task commits in *its own repo's* feature branch.
  Record `BASE` per repo, from that repo's HEAD, before the first task that touches
  it — never one shared working tree, never a single `git merge-base main HEAD`
  across all of them.
- **One ledger at the orchestration root**, keyed by repo AND task:
  `Task N (rubato): complete (commits …, review clean)`. You need one place that
  survives to resume from when work is spread across repos.
- **Order by contract-freeze, not git.** A cross-repo chain (producer endpoint →
  consumer) is NOT a git stack — git cannot stack across repos. Order tasks so a
  producer's contract (enum values, endpoint request/response shape) is frozen
  before its consumer starts; note whether the consumer needs it *merged* or just
  *agreed*. The dependency is the contract, not a branch.
- **Make the cross-repo contract an artifact — the highest-risk gap.** A shared
  contract (an enum used in 3 repos, an endpoint shape one produces and another
  consumes) is exactly what a per-task reviewer flags "cannot verify from diff" — it
  lives in another repo. Give it a mechanism: when the producer task defines it,
  write the contract to a **contract file** in the ledger dir; forward that file to
  every consumer task's dispatch AND its reviewer's global-constraints, so both
  sides review against the *same* written contract. For a value contract (an enum),
  add a test in each repo asserting its literal values — drift trips a test, not
  production.
- **Final review is per repo, plus one cross-repo pass.** Run `nl-code-review` once
  per touched repo (each against its own merge-base). Then one extra pass whose only
  job is: do the shared contracts match across repos (identical enum values,
  agreeing endpoint shapes)?
- **Soft / data dependencies are DONE-with-note, not BLOCKED.** A consumer that can
  ship against a mock or an existing endpoint while the producer's real data isn't
  live yet is DONE — record "real data pending Task M live" in the report; do not
  mark it BLOCKED.

## Subagents use TDD

The implementer prompt requires red-green-refactor: write a failing test, make it pass, refactor. Tests-first is non-negotiable in execution. (Inlined here so this skill carries no external TDD dependency.)

## Red flags — Never

- Start on main/master without explicit consent
- Skip a task review, or accept a report missing either verdict (spec AND quality)
- Proceed with unfixed Critical/Important findings
- Dispatch multiple implementers in parallel (conflicts)
- Make a subagent read the whole plan (hand it the brief)
- Paste prior-task history into a dispatch
- Tell a reviewer what not to flag, or pre-rate severity
- Dispatch a reviewer without a diff file
- Re-dispatch a task the ledger already marks complete (check after any compaction)
- Treating a side-effect step with no diff (publishing i18n to a sheet, manual cross-browser QA) as covered by the review loop — it isn't; record it in the report and carry it to `nl-verify`
- Assuming one repo when the plan spans several (see Multi-repo execution)

## Integration

- **nl-research-plan-execute** — calls this skill as its execute stage; supplies `plan.md` (task briefs) and `research.md` (per-task context to extract).
- **nl-code-review** — the broad final whole-branch review after all tasks pass.
- **nl-verify** — verification + branch finishing after the final review.
