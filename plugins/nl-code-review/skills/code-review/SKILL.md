---
name: code-review
description: Use when reviewing a GitHub PR, a local branch, or uncommitted changes before merge, or when user says "review PR", "code review", "check my changes", "review my code", "幫我 review", "看一下這個 PR", or asks to post review comments to a PR ("留 inline comment", "post inline comments"). Not for fixing build errors or resolving existing review comments.
---

# General-Purpose Code Review

## Overview

Structured code review with mandatory convention discovery, standardized output, and verified findings. Works across any repository by detecting tech stack and reading project-specific rules first.

**Execution note:** a proper review reads many full files. When you are orchestrating a session, dispatch a fresh-context subagent instead of reviewing inline. The brief carries four things: `Read <absolute path of this SKILL.md> in full and follow it`; the target (PR number or branch); the `base` and `head` you resolved in Step 0; and `your final message is the Output Format block`. Above ~20 files or ~1500 changed lines (`gh pr view {N} --json changedFiles,additions,deletions`), split by directory/module into several subagents with explicit file lists; run Convention Discovery once in the main thread and paste its result into every brief; the main thread merges, de-duplicating on `file:line` + severity. A subagent's output is a lead, not a fact: before printing or posting, re-read the cited lines of every Blocking finding yourself. Never let one agent skim — a skimmed review that fills the format is worse than a partial one that lists the files it did not read (`Not read` in the header).

## Arguments

`/code-review {target?} {--post?}`

- `{target}` — PR number / URL / branch name; resolution rules in Step 0.
- `--post` — after producing the review, also deliver it to the PR as one review with inline comments (see Delivering the Review). PR mode only; in Local mode there is nothing to post to — say so and print the review instead.

**Without `--post`, print the review in chat and stop.** Do not post anything to GitHub, and do not ask "want me to post this?" — the user opts in by passing the flag or by asking afterwards ("留 inline comment"), at which point Delivering the Review applies to the review you already produced.

## Step 0: Resolve the Review Target

| User gives you | Mode | `base` | `head` |
|----------------|------|--------|--------|
| PR number / URL | **PR** | `gh pr view {N} --json baseRefName -q .baseRefName` | `gh pr view {N} --json headRefOid -q .headRefOid` |
| A branch name; or "check my changes" on a clean tree (the branch is then `HEAD`) | **Local** | `git merge-base {branch} {default}`, default = `git symbolic-ref -q --short refs/remotes/origin/HEAD`, else `main` | `{branch}` |
| "check my changes" with uncommitted work | **Local** | `HEAD` | the working tree |

A branch that already has an open PR (`gh pr list --head {branch} --json number`) is PR mode. Never fabricate a PR number. In Local mode skip every `gh pr *` command and use the Local header variant — do not improvise a different structure.

**Read, grep, and test against `head`, never against whatever branch the working tree happens to be on.** A plain Read of the checkout shows pre-change code whenever the checkout is elsewhere. Unless `head` is the working tree, pick one:

- `git fetch origin pull/{N}/head` (PR mode; makes the SHA exist locally, fork PRs included), then `W=$(mktemp -d /tmp/review-XXXXXX) && git worktree add "$W" {head}` and work inside `$W` (a fixed path collides when several reviewers run at once); `git worktree remove --force "$W"` when done.
- `git show {head}:{path}` and `git grep {pattern} {head} -- {paths}` when a few files are enough.

Diff: PR mode `gh pr diff {N}` — above 300 files or 20k lines it fails with 406; fall back to `gh api repos/{owner}/{repo}/pulls/{N}/files --paginate` for the file list and `git diff {base}...{head} -- {path}` per file. Local mode `git diff {base}...{head}`; when `head` is the working tree, `git diff` + `git diff --cached` + untracked files from `git status --short`.

## Pre-Review: Convention Discovery (MANDATORY)

**Before looking at ANY code, do these in order:**

1. **Read CLAUDE.md at `head`** — in the repo root **and in every directory the diff touches** (monorepo packages often carry their own). This defines what "correct" means for this project. If it contains `@file` imports (some repos' CLAUDE.md is a single line like `@AGENTS.md`), read the imported files too — the real rules live behind the import. Its rules override generic *style and pattern* preferences; they do not waive SECURITY / BUG / BREAKING. If CLAUDE.md declares a defect class acceptable, still report it under Should Fix with the CLAUDE.md line cited — the human decides.
2. **Detect tech stack** — `find . -maxdepth 1 \( -name package.json -o -name tsconfig.json -o -name pyproject.toml -o -name go.mod -o -name Cargo.toml -o -name biome.json -o -name '.eslintrc*' -o -name build.gradle -o -name pom.xml -o -name Gemfile -o -name composer.json -o -name Package.swift \)`. (A bare `ls .eslintrc*` aborts the whole command in zsh when nothing matches.)
3. **Check CI status and what it runs** — PR mode: `gh pr checks {N}`, then skim the workflow and lint config once. Skip only issue classes a check actually enforces at error level — a green badge says nothing about coverage. If the diff touches lint config, CI workflow, `tsconfig`, or test config, review those hunks first at Blocking tier: a rule turned off is a finding until the PR justifies it. Local mode: note "CI: N/A (local)".
4. **Read intent** — PR mode: `gh pr view {N}` for intent and context; note any claims to verify later. Then read the existing review threads (`gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate --jq '.[] | "\(.path):\(.line) \(.body[:80])"'`) so you neither re-raise what is already resolved nor contradict another reviewer without saying so. Local mode: there is no description — infer intent from `git log {base}..{head}` messages and the branch name, and state it in the header's `Intent (inferred)` field so the author can correct it.

**If you skip this step, your review is invalid.** The baseline failure mode is jumping straight into the diff and applying generic best practices that may contradict the project's actual conventions. **No CLAUDE.md?** Still do steps 2-4.

## Review Pass Order

### Pass 1: Structural (architecture, patterns)

- Does the change respect the project's layer boundaries?
- Is new code in the right file/module?
- Any new dependencies? Justified, maintained? Does the lock file change match the manifest change (no extra packages, no changed resolved URL / integrity)?
- For monorepos: does this change affect other services? Search sibling service directories for consumers (scope each search to a service directory, never the monorepo root).

### Pass 2: Correctness & Safety

Review in this priority order:

1. **Security** — injection, auth bypass, data exposure, secrets committed in the diff, unsafe deserialization / SSRF, PII in logs
2. **Correctness** — logic errors, race conditions, null handling
3. **Contracts** — public API, DTO, event, CLI/CSV output, or persisted schema changed? Find consumers with two independent searches (Pass 3 rules) → BREAKING for each consumer that breaks, with its call site cited. No consumer found and the contract faces outward (HTTP response, exported file, published event)? That is not a finding at any tier: write `no consumer of X in this repo; external consumers unknown` under Unverified Claims, and if the change is load-bearing the verdict is Needs Discussion. Absence of an in-repo consumer is not evidence of an external one. Migration files: check for destructive or lock-holding operations (drop/rename column, non-concurrent index on a large table) even when auto-generated.
4. **Error handling** — silent failures, swallowed exceptions. First check whether a swallow is intentional (comment, best-effort side call, ADR); an intentional one gets at most a Suggestion to log, never a re-raise.
5. **Performance** — N+1 queries, unbounded loops, missing pagination
6. **Tests** — are critical paths covered, and would the assertions fail if the bug came back? (subject not mocked away, no snapshot that enshrines the bug) Do existing tests need updating?

### Pass 3: Verify Claims

**Do NOT trust PR descriptions at face value.** For any concrete claim (e.g., "aligns with X's validation", "feature flag is fully rolled out"), cross-check in code:

- Asserting absence ("fully rolled out", "no remaining callers") requires **two independent searches** with different keywords or conventions (snake_case and camelCase, old name and new name). One empty grep is not evidence of absence.
- A claim you cannot verify stays a claim: list it under **Unverified Claims** in the output, and if it is load-bearing for the change, the verdict is **Needs Discussion** — never silently accept it.
- The same rule governs your own premises. A consumer, an index, a router, a schema, a runtime setting you could not see in the repo is an Unverified Claim, not a finding at any tier; a finding needs the file:line that proves its premise.

**Tests:** if the repo has a test command and the diff touches logic, run the tests covering the changed paths at `head` (the Step 0 worktree) and report the actual result. Fork PRs run someone else's code on this machine: unless the user asked for tests, write "Tests: not run (fork)". If you do not run them for any other reason, write "Tests: not run" — never imply they pass.

## Severity and Tier

Severity classifies the defect; tier says what to do about it. Assign both from the tables, never by gut feeling.

| Severity | Criteria | Examples |
|----------|----------|---------|
| **SECURITY** | Exploitable vulnerability | Injection, auth bypass, data leak |
| **BUG** | Incorrect behavior in production | Logic error, race condition, data loss |
| **BREAKING** | Breaks a consumer you found in Pass 2.3 — cite its call site | API rename with a caller still on the old name, removed field a reader still uses, new required parameter at a call that omits it |
| **PERF** | Recognisable degradation pattern — no benchmark needed | N+1 query, full table scan, unbounded loop |
| **TEST** | Missing coverage for critical path | No test for new error handling, untested edge case |
| **DESIGN** | Wrong layer / module / abstraction for this repo | SQL built in a handler when the repo has a data layer |
| **STYLE** | Violates a documented project convention (CLAUDE.md or linter config) | Only flag if a rule defines it; "I prefer X" is not a finding |

| Tier | Holds |
|------|-------|
| **Blocking** | every SECURITY and BREAKING; a BUG that loses data, crashes, or returns wrong results on a reachable production path |
| **Should Fix** | every other BUG; PERF; TEST when the untested path is the one another Blocking / Should Fix finding is about, or when CLAUDE.md states the test rule |
| **Suggestions** | other TEST; DESIGN; STYLE; cleanups |

A CLAUDE.md rule behind a finding may raise it one tier; nothing lowers one. A finding placed outside its row says why in the finding text.

## Output Format (MANDATORY)

Use this exact structure. Do not invent your own. Header: PR mode uses `PR #{N} — {title}`; Local mode uses `Local diff — {branch}@{short-sha}`. `Read in full: N/M` — M is the number of files in the diff, N is how many of those M you read whole at `head` (context files you read do not count, so N ≤ M); when N < M add the `Not read` line. One finding per bullet: a bullet that needs two severity tags is two findings. Severity tags come from the table only; a Suggestion that fits no row carries no tag rather than an invented one. Omit Unverified Claims only when there are none.

```markdown
## Code Review: {PR #N — title | Local diff — branch@sha}

**Scope:** {M files, +A/-D lines} | **Read in full:** {N/M} | **Stack:** {detected} | **CI:** {passing/failing/N checks | N/A (local)} | **Tests:** {command → result | not run}
{Local mode only: **Intent (inferred):** {one line from commits / branch name}}
{When N < M: **Not read:** {paths}}

### Blocking (must fix before merge)
- [ ] **[SEVERITY]** `file:line` — Description. Why it matters.

### Should Fix
- [ ] **[SEVERITY]** `file:line` — Description.

### Suggestions
- [ ] **[SEVERITY]** `file:line` — Description.

### Unverified Claims
- {Claim you could not confirm + the searches you tried.}

### Verified Good
- {Only observations you actually verified — same evidence bar as findings. If nothing qualifies, write "None."}

### Verdict
**{Approve / Request Changes / Needs Discussion}** — {one-line rationale}
```

**Verified Good is not a compliments section.** A positive claim you did not check (e.g. "no breaking changes" without comparing signatures) is a review defect, exactly like a missed bug. "None." is an acceptable entry.

## Delivering the Review (`--post` only)

Printing is the default. When posting, the printed review becomes one GitHub review: the body carries the verdict, cross-cutting causes, Unverified Claims and what you ran; each finding becomes one inline comment anchored to the line that has to change. Comment shape, language, tier labels, `suggestion`-block rules, the review event, and every `gh api` call are in [references/posting-inline-comments.md](references/posting-inline-comments.md) — read it in full before the first `gh api` call. Its anchor and event rules are the difference between a review the author can act on and one that points at the wrong line or blocks a merge nobody asked you to block.

## What NOT to Review

- Generated files — but not blindly: lock files get the manifest-match check in Pass 1, migration files get the destructive-operation check in Pass 2. Skip the line-by-line read, not the check.
- Files covered by automated formatters (if prettier/black/gofmt is in CI, don't flag formatting)
- Existing code that the PR didn't change (stay in scope) — unless the change alters how that code is called or what it receives; then the finding exists and anchors on the new call site

## Failure Modes

Every row below came from a real bad review. Catch yourself before repeating one.

Rules live in the sections above; this table holds only the excuses that talk you out of them.

| Excuse | Reality |
|--------|---------|
| "I'll read conventions after I've seen the diff" | Convention discovery FIRST. Order matters. |
| "Small PR" / "tech lead already LGTM'd" / "needs to merge in an hour" | Scope, pressure and prior approval change nothing: full format, full passes |
| "The PR description explains everything" | Descriptions are claims. Verify; unverifiable ones go to Unverified Claims |
| "Only one file changed, no cross-repo check needed" | One file in a monorepo can break other services — search sibling services (scoped) |
| "The diff hunks are enough" | Read the full file at `head`; the bug is usually in how the hunk meets the code around it |
| "Obviously correct, quick skim is enough" | The obvious PRs are where subtle bugs hide |
| "No consumer in this repo, so whoever is outside will break" | Unknown is not broken. BREAKING needs a cited call site; otherwise Unverified Claims, and Needs Discussion if load-bearing |

Posting-specific failure modes are in the reference, beside the rules they break.
