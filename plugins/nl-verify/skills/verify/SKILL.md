---
name: verify
description: Use when about to claim work is complete, fixed, or passing — before committing, delivering, or moving on — and when finishing a development branch. Requires fresh verification evidence before any success claim, then guides completion (deliver / merge / keep / discard). Also the verify stage of the research-plan-execute pipeline. Triggers on "is it done", "tests pass", "ready to ship", "wrap it up", finishing a branch.
---

# Verify

Two jobs, in order: **prove the work before you claim it**, then **finish the branch cleanly**.

**Core principle:** evidence before claims, always. Then present clear completion options — never open-ended.

This skill is model-agnostic on purpose: a capable model self-verifies on a good day, but a weaker model, or the same model deep in a long or post-compaction session under real pressure, does not. The gate holds regardless.

## Part 1 — The verification gate

### The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not run the verification command *in this message*, you cannot claim it passes. **Violating the letter of this rule violates its spirit** — paraphrases, synonyms, and implications of success all count.

### The gate function

Before claiming any status or expressing satisfaction:

1. **IDENTIFY** — what command proves this claim?
2. **RUN** — execute the FULL command, fresh and complete.
3. **READ** — full output; check exit code; count failures.
4. **VERIFY** — does the output confirm the claim?
   - No → state the actual status with evidence.
   - Yes → state the claim WITH the evidence.
5. **ONLY THEN** — make the claim.

Skip any step = claiming, not verifying.

### Claim → requires → not sufficient

| Claim | Requires | NOT sufficient |
|---|---|---|
| Tests pass | Test command output: 0 failures | A previous run; "should pass" |
| Linter clean | Linter output: 0 errors | Partial check; extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing; "logs look fine" |
| Bug fixed | Original symptom re-tested: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Subagent completed | VCS diff shows the changes | The agent's "success" report |
| Requirements met | Line-by-line checklist vs the spec/plan | Tests passing |

### Red-green for regression tests

A test that passes on both the buggy and fixed code guards nothing.

```
write test → run (pass) → revert the fix → run (MUST FAIL) → restore fix → run (pass)
```

Only after seeing it fail on the pre-fix code have you verified it catches the regression.

### Spirit over letter

The rule binds exact phrases, paraphrases, synonyms, and any wording that *implies* success. "Looks good", "should be fine", "that's done" without fresh evidence are all violations.

### Red flags — STOP

- "should", "probably", "seems to", "looks correct"
- Expressing satisfaction before verifying ("Great!", "Perfect!", "Done!")
- About to commit / push / PR without verification
- Trusting a subagent's success report instead of checking the diff
- Relying on a partial or stale check
- "Just this once" / tired and wanting it over

### Rationalization table

| Excuse | Reality |
|---|---|
| "Should work now" | RUN the verification. |
| "I'm confident" | Confidence ≠ evidence. |
| "Just this once" | No exceptions. |
| "Linter passed" | Linter ≠ compiler ≠ tests. |
| "The subagent said success" | Verify independently — check the diff, run the suite. |
| "I'm tired" | Exhaustion ≠ excuse. |
| "Partial check is enough" | Partial proves only the part. |
| "Different words, so the rule doesn't apply" | Spirit over letter. |

### Plan-aware verification (pipeline bonus)

When invoked as the verify stage of `nl-research-plan-execute`, the approved
`plan.md` is available. Verify against it, not only against tests:

- Re-read each task's **acceptance criteria**; build a checklist; confirm each line with evidence.
- Report any requirement that is missing, partial, or implemented differently from the plan.
- Tests passing is necessary, not sufficient — the plan is the spec.

## Part 2 — Finish the branch

Only after Part 1 passes.

### Step 1 — Verify tests (gate)

Run the project's suite. If it fails:

```
Tests failing (<N>). Must fix before finishing:
<failures>
```

Stop. Do not present options on a red suite.

### Step 2 — Detect environment

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
```

| State | Menu |
|---|---|
| `GIT_DIR == GIT_COMMON` (normal repo) | 4 options |
| `GIT_DIR != GIT_COMMON`, named branch | 4 options, provenance-based cleanup |
| `GIT_DIR != GIT_COMMON`, detached HEAD | 3 options (no local merge), no cleanup |

### Step 3 — Determine base

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main — correct?"

### Step 4 — Present options (structured, never open-ended)

Normal repo / named-branch worktree:

```
Implementation verified. What next?
1. Deliver as a Pull Request
2. Merge back to <base> locally
3. Keep the branch as-is
4. Discard this work
```

Detached HEAD (drop local merge):

```
1. Deliver as a Pull Request
2. Keep as-is
3. Discard this work
```

Don't add explanation — keep options concise.

### Step 5 — Execute the choice

- **Deliver as PR** — hand off to `nl-create-pr` (it owns FoD splitting, branch/commit
  conventions, and the PR body). Do NOT reimplement push/PR here. Keep the worktree
  alive for review iteration.
- **Merge locally** —
  ```bash
  MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
  cd "$MAIN_ROOT"
  git checkout <base> && git pull && git merge <feature-branch>
  <run test command on the merged result>
  ```
  Then clean up the worktree (Step 6), then `git branch -d <feature-branch>`.
- **Keep as-is** — report "Keeping branch <name>. Worktree preserved at <path>." No cleanup.
- **Discard** — require typed confirmation:
  ```
  This permanently deletes branch <name>, commits <list>, and worktree <path>.
  Type 'discard' to confirm.
  ```
  Only on exact "discard": clean up the worktree (Step 6), then `git branch -D <feature-branch>`.

### Step 6 — Clean up workspace (only Merge and Discard)

```bash
WORKTREE_PATH=$(git rev-parse --show-toplevel)
```

- `GIT_DIR == GIT_COMMON` → normal repo, nothing to clean.
- Worktree path under `.worktrees/` or `worktrees/` → we own it:
  ```bash
  MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
  cd "$MAIN_ROOT"                 # never run worktree remove from inside the worktree
  git worktree remove "$WORKTREE_PATH"
  git worktree prune
  ```
- Otherwise → the harness owns this workspace; do NOT remove it.

### Quick reference

| Option | Verify tests | Merge | PR | Keep worktree | Delete branch |
|---|---|---|---|---|---|
| Deliver PR | yes | — | via nl-create-pr | yes | — |
| Merge local | yes | yes | — | — | yes |
| Keep as-is | yes | — | — | yes | — |
| Discard | yes | — | — | — | yes (force, typed confirm) |

## Red flags — Part 2

- Presenting options on a failing suite
- Open-ended "what do you want to do?" instead of the structured menu
- Reimplementing PR creation instead of delegating to `nl-create-pr`
- Removing a worktree you did not create (provenance check)
- Running `git worktree remove` from inside the worktree
- Deleting the branch before removing its worktree
- Discarding without an exact typed "discard"
- Force-pushing without an explicit request

## Integration

- **nl-create-pr** — the "Deliver as PR" path; owns PR creation and delivery.
- **nl-research-plan-execute** — calls this skill as its verify stage; supplies `plan.md` for plan-aware verification.
- **nl-code-review** — heavier PR-time review lives there; this skill's Part 1 is the honesty gate, not a code review.
