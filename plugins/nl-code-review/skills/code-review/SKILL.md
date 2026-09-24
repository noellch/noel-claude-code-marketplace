---
name: code-review
description: Use when reviewing PRs, checking code quality, or when user says "review PR", "code review", "check my changes", "review my code", or asks to post review comments to a PR ("留 inline comment", "post inline comments")
---

# General-Purpose Code Review

## Overview

Structured code review with mandatory convention discovery, standardized output, and verified findings. Works across any repository by detecting tech stack and reading project-specific rules first.

**Execution note:** a proper review reads many full files. When you are orchestrating a session, dispatch a fresh-context subagent carrying this skill's process and the review target, instead of reviewing inline in the main conversation. Above ~20 files or ~1500 changed lines, split by directory/module into several subagents, each with an explicit file list; the main thread merges and de-duplicates. A subagent's output is a lead, not a fact: before printing or posting, the main thread re-reads the cited lines of every Blocking finding and every `suggestion` block. Never let one agent skim — a skimmed review that fills the format is worse than a partial one that names the files it did not read (see `Read in full` in the header).

## Arguments

`/code-review {target?} {--post?}`

- `{target}` — PR number / URL / branch name; resolution rules in Step 0.
- `--post` — after producing the review, also deliver it to the PR as one review with inline comments (see Delivering the Review). PR mode only; in Local mode there is nothing to post to — say so and print the review instead.

**Without `--post`, print the review in chat and stop.** Do not post anything to GitHub, and do not ask "want me to post this?" — the user opts in by passing the flag or by asking afterwards ("留 inline comment"), at which point Delivering the Review applies to the review you already produced.

## Step 0: Resolve the Review Target

| User gives you | Mode | Diff source |
|----------------|------|-------------|
| PR number / URL | **PR** | `gh pr diff {N}` |
| "check my changes" / no PR exists | **Local** | `git diff` + `git diff --cached` + untracked files from `git status --short` |
| A branch name | **Local** | `git diff {base}...{branch}` |

Never fabricate a PR number. In Local mode, skip every `gh pr *` command and use the Local header variant in the output format — do not improvise a different structure.

## Pre-Review: Convention Discovery (MANDATORY)

**Before looking at ANY code, do these in order:**

1. **Read CLAUDE.md** — in the repo root **and in every directory the diff touches** (monorepo packages often carry their own). This defines what "correct" means for this project. If it contains `@file` imports (some repos' CLAUDE.md is a single line like `@AGENTS.md`), read the imported files too — the real rules live behind the import. Its rules override generic *style and pattern* preferences; they do not waive SECURITY / BUG / BREAKING. If CLAUDE.md declares a defect class acceptable, still report it under Should Fix with the CLAUDE.md line cited — the human decides.
2. **Detect tech stack** — `ls package.json tsconfig.json pyproject.toml go.mod Cargo.toml .eslintrc* biome.json 2>/dev/null`
3. **Check CI status and what it runs** — PR mode: `gh pr checks {N}`, then skim the workflow and lint config once. Skip only issue classes a check actually enforces at error level — a green badge says nothing about coverage. If the diff touches lint config, CI workflow, `tsconfig`, or test config, review those hunks first at Blocking tier: a rule turned off is a finding until the PR justifies it. Local mode: note "CI: N/A (local)".
4. **Read intent** — PR mode: `gh pr view {N}` for intent and context; note any claims to verify later. Local mode: there is no description — infer intent from `git log {base}..HEAD` messages and the branch name, and state it in the header's `Intent (inferred)` field so the author can correct it. Without intent, "forgot a case the ticket asked for" is invisible; say so rather than pretend.

**If you skip this step, your review is invalid.** The baseline failure mode is jumping straight into the diff and applying generic best practices that may contradict the project's actual conventions.

**No CLAUDE.md?** Still do steps 2-4. The absence of one input does not excuse skipping the entire discovery phase.

## Review Pass Order

### Pass 1: Structural (architecture, patterns)

- Does the change respect the project's layer boundaries?
- Is new code in the right file/module?
- Any new dependencies? Justified, maintained, license compatible? Does the lock file change match the manifest change (no extra packages, no changed resolved URL / integrity)?
- For monorepos: does this change affect other services? Check cross-repo references (scope searches to the affected service directories, never the monorepo root).

### Pass 2: Correctness & Safety

Review in this priority order:

1. **Security** — injection, auth bypass, data exposure, secrets committed in the diff, unsafe deserialization / SSRF, PII in logs
2. **Correctness** — logic errors, race conditions, null handling
3. **Contracts** — public API, DTO, event, or persisted schema changed? Find consumers with two independent searches (Pass 3 rules) → BREAKING if any break. Migration files: check for destructive or lock-holding operations (drop/rename column, non-concurrent index on a large table) even when auto-generated.
4. **Error handling** — silent failures, swallowed exceptions. First check whether a swallow is intentional (comment, best-effort side call, ADR); an intentional one gets at most a Suggestion to log, never a re-raise.
5. **Performance** — N+1 queries, unbounded loops, missing pagination
6. **Tests** — are critical paths covered, and would the assertions fail if the bug came back? (subject not mocked away, no snapshot that enshrines the bug) Do existing tests need updating?

### Pass 3: Verify Claims

**Do NOT trust PR descriptions at face value.** For any concrete claim (e.g., "aligns with X's validation", "feature flag is fully rolled out"), cross-check in code:

- Asserting absence ("fully rolled out", "no remaining callers") requires **two independent searches** with different keywords or conventions (snake_case and camelCase, old name and new name). One empty grep is not evidence of absence.
- A claim you cannot verify stays a claim: list it under **Unverified Claims** in the output, and if it is load-bearing for the change, the verdict is **Needs Discussion** — never silently accept it.

**Tests:** if the repo has a test command and the diff touches logic, run the tests covering the changed paths and report the actual result. If you do not run them, write "Tests: not run" in the header — never imply they pass.

## Output Format (MANDATORY)

Use this exact structure. Do not invent your own. Header: PR mode uses `PR #{N} — {title}`; Local mode uses `Local diff — {branch}@{short-sha}`.

```markdown
## Code Review: {PR #N — title | Local diff — branch@sha}

**Scope:** {N files, +M/-K lines} | **Read in full:** {N/M files} | **Stack:** {auto-detected} | **CI:** {passing/failing/N checks | N/A (local)} | **Tests:** {command → result | not run}
{Local mode only: **Intent (inferred):** {one line from commits / branch name}}

### Blocking (must fix before merge)
- [ ] **[SEVERITY]** `file:line` — Description. Why it matters.

### Should Fix
- [ ] **[SEVERITY]** `file:line` — Description.

### Suggestions
- [ ] `file:line` — Description.

### Unverified Claims
- {Claim you could not confirm + the searches you tried. Omit this section when there are none.}

### Verified Good
- {Only observations you actually verified — same evidence bar as findings. If nothing qualifies, write "None."}

### Verdict
**{Approve / Request Changes / Needs Discussion}** — {one-line rationale}
```

**Verified Good is not a compliments section.** A positive claim you did not check (e.g. "no breaking changes" without comparing signatures) is a review defect, exactly like a missed bug. "None." is an acceptable entry.

## Delivering the Review

The section above is the artifact. This one is how it reaches the author when you are posting rather than printing — which happens only when the invocation carried `--post` or the user asked for it (see Arguments).

Two surfaces, two jobs. A sentence that appears on both is a sentence the author reads twice.

| Surface | Carries |
|---------|---------|
| **Review body** | verdict, root causes that span several findings, PR-description claims that did not survive verification, what you ran and what you only read |
| **Inline comment** | one finding, anchored to the line that has to change |

The Output Format above is written for printing the whole review in one place. When you post, its finding lists collapse to an index — anchor plus a handful of words, no evidence, no mechanism, no consequence — because each of those now lives on its own anchor. Keep the section headings so the tiers are still countable at a glance. Sections with nothing to move inline (Unverified Claims, Verified Good, Verdict) stay written out in full.

Mechanics — endpoints, JSON shape, anchor rules, suggestion-block byte matching, reworking a submitted review — are in [references/posting-inline-comments.md](references/posting-inline-comments.md). Read it before the first `gh api` call: an anchor outside the diff fails loudly, and an anchor on the wrong in-diff line succeeds quietly.

### Comment shape

Findings carry different weight; the layout must show it. One flat paragraph makes a Blocking finding and a nit read the same, and buries the fix inside the diagnosis.

**Blocking / Should fix — sectioned:**

```
**[{tier}] {headline: what breaks, one sentence — not what the code does}**

**問題**

{mechanism, compressed. Evidence as a bullet list: the file:line chain the reader can
check themselves. End with the consequence if the headline alone doesn't carry it.}

**建議修法（範例）**

{a ```suggestion block when the edit is a contiguous replacement of the anchored lines;
otherwise a fenced code block showing the fixed code}

**測試**

{only when missing coverage is part of the finding: name the specific test that would pin it}
```

**Nit — one line, no headings:** `nit：{observation}` plus an optional example block. Section structure on a nit reads heavier than the finding warrants.

**Review body — a counted index:** tiers with counts and a few words each (`**Blocking ×2**（見 inline）：lockfile integrity、檢視版本入口失效`), then everything that has no anchor written out in full — Unverified Claims, PR-description mismatches, the verdict.

Write the section labels and prose in the language the team reviews in (for this user: Traditional Chinese prose, English code); keep identifiers and code exact.

- **Lead with the tier, then the consequence.** Tier is what to do about it — `Blocking`, `Should fix`, `Nit`, `Context（不用改這裡）` — and is orthogonal to the severity table above, which classifies the defect. The headline says what breaks; evidence comes after. A comment that opens with "這個 effect 在 X 時 early return" makes the reader assemble the consequence themselves.
- **A `suggestion` block is code you are shipping.** Emit one by default, but only after applying it in a scratch worktree of the head SHA and running the cheapest check that would catch a wrong fix: typecheck / lint on that file, the covering test if one exists (mechanics in the reference). PERF fixes that reshape queries (join, prefetch, batching) need the covering test, not just a typecheck. If you cannot run anything, post a plain fenced block and say so in one line (`未實跑，依 {file}:{line} 推斷`). Not being sure of the surrounding idiom is a reason to go read the file, not a reason to describe the fix in prose. When the fix can't be a suggestion block (non-contiguous edit, anchored line isn't the line to change, displaced anchor), show the fixed code in a plain fenced block instead — never prose alone.
- **Say how you know only where the reader could get it wrong.** A review comment is assumed to come from reading the code, so restating that on every anchor is noise — and a marker identical on all of them carries no information at all. Mark two cases: a claim about runtime behaviour you did not observe, and a comment written as a reproduction ("upload file A, swap in file B, the row now reads…"), which looks like something you watched happen. Better than any label is the command that settles it. Never label a claim inferred when you confirmed it by reading a file you can cite — that understates your own evidence, which is its own kind of wrong.
- **The review event is the human's call.** Default to `COMMENT`. `REQUEST_CHANGES` blocks the merge and has to be dismissed by a human — say you think it is warranted, then let them press it. When Blocking findings exist under `COMMENT`, the body's first line must say so (`⚠ N 個 Blocking，建議 Request Changes（由人按）`) so a skimming author cannot merge past them.

## Severity Definitions

Do NOT assign severity by gut feeling. Use these criteria:

| Severity | Criteria | Examples |
|----------|----------|---------|
| **SECURITY** | Exploitable vulnerability | Injection, auth bypass, data leak |
| **BUG** | Incorrect behavior in production | Logic error, race condition, data loss |
| **BREAKING** | Breaks existing consumers | API rename without migration, removed field, new required parameter |
| **PERF** | Measurable performance degradation | N+1 query, full table scan, unbounded loop |
| **TEST** | Missing coverage for critical path | No test for new error handling, untested edge case |
| **STYLE** | Violates project conventions (not generic opinions) | Only flag if CLAUDE.md or linter config defines the rule |

**Rule: Only flag STYLE issues if the project has a documented convention for it.** Generic "I prefer X" opinions are not review findings.

## What NOT to Review

- Generated files — but not blindly: lock files get the manifest-match check in Pass 1, migration files get the destructive-operation check in Pass 2. Skip the line-by-line read, not the check.
- Files covered by automated formatters (if prettier/black/gofmt is in CI, don't flag formatting)
- Existing code that the PR didn't change (stay in scope) — unless the change alters how that code is called or what it receives; then the finding exists and anchors on the new call site

## Failure Modes

Every row below came from a real bad review. Catch yourself before repeating one.

| Failure / Excuse | Reality / What to Do |
|------------------|----------------------|
| Jump into the diff first ("I'll read conventions after") | Convention discovery FIRST. Order matters. |
| "No CLAUDE.md, so skip discovery" | Still check linter config, CI, tech stack markers |
| No PR exists → improvise a format or fabricate a PR number | Use Local mode: git diff + the Local header variant |
| "Small PR, I don't need the full format" | Format is mandatory regardless of size |
| "The PR description explains everything" | Descriptions are claims. Verify; unverifiable ones go to Unverified Claims |
| One empty grep → "it doesn't exist" | Two independent searches before asserting absence |
| Assign severity by intuition | Use the severity criteria table |
| Flag style issues from personal preference | Only documented conventions |
| Review only the diff hunks | Read full files for context around changes |
| "Only one file changed, no cross-repo check needed" | One file in a monorepo can break other services — search sibling services (scoped) |
| Pad Verified Good with unchecked praise | Positive claims need the same evidence as findings; write "None." if nothing qualifies |
| "Obviously correct, quick skim is enough" | The obvious PRs are where subtle bugs hide |
| "I'm not sure how the surrounding code is written, so I'll describe the fix" | Go read those lines, then emit a `suggestion` block. Uncertainty is a lookup, not a downgrade |
| Restate each inline finding in the review body too | Body carries verdict and cross-cutting causes only; duplication makes the author read it twice |
| One global "I didn't run the app" note in the body | Files changed shows one anchor at a time. Put it on the anchors whose claims need it |
| Close every comment with the same "didn't run it" tag | A marker that never varies carries no information and reads as hedging. Mark only what a reader could mistake for something you observed |
| Tag a finding "inferred" when a cited file:line already proves it | That understates your evidence. Cite the line and drop the tag |
| Submit `REQUEST_CHANGES` because the findings look blocking | Blocking the merge is the human's call. Post `COMMENT`, state the verdict, let them press it |
| Anchor to the line the finding is about, without checking the diff | Only lines inside a diff hunk are anchorable; the wrong in-diff line succeeds silently |
| CLAUDE.md says this defect class is fine → suppress the finding | Conventions govern STYLE only. Report SECURITY / BUG / BREAKING anyway, cite the CLAUDE.md line, let the human decide |
| CI is green → skip everything a linter "would catch" | Read what CI runs. A PR that turns a rule off passes green; lint/CI config hunks are Blocking-tier scrutiny |
| Swallowed exception → suggest re-raise | Check whether the swallow is intentional first. Re-raising a best-effort call turns a tolerated failure into a production crash |
| Post a `suggestion` block you never ran | Apply it in a worktree and typecheck / test it. Cannot run → fenced block plus one line saying so |
