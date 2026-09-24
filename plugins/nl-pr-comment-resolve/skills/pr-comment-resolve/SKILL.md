---
name: pr-comment-resolve
description: Use when the user asks to resolve, address, or fix PR review comments. Triggers on "resolve PR comments", "address review feedback", "fix PR issues"
---

# PR Comment Resolution

## Overview

Resolving PR comments requires **action, not description**. Every thread must be: evaluated → implemented (or discussed) → verified → replied to → tracked.

Order matters more than speed. Nothing is said to a reviewer until the fix is tested and pushed; nothing except "Fixed in <sha>" is said without the user seeing the text first.

## Arguments

`/pr-comment-resolve {pr?} {--resolve?}`

- `{pr}` — PR number / URL; defaults to the PR of the current branch (`gh pr view`).
- `--resolve` — after replying, mark each handled thread resolved. Off by default: some teams want the reviewer to resolve.

## Resolution Flow

```
0. Pre-flight   clean tree · on PR head branch · fetched, not behind
1. Fetch        review threads (GraphQL) + review bodies + issue comments → one table
2. Gate 1       AskUserQuestion ONCE — per item: Handle / Skip / Discuss
3. Per Handle   READ → UNDERSTAND → VERIFY → EVALUATE → implement → re-read the comment
                → run the covering test → commit locally (trailer = comment URL)
4. Verify       full test command; must be green before anything leaves the machine
5. Push         `git push` — never --force; rejected → stop and report
6. Gate 2       show drafts of every outward text that is not "Fixed in <sha>"
7. Reply        one reply per thread with clickable SHA(s); `--resolve` if asked
8. Re-request   reviewers whose last review was CHANGES_REQUESTED
```

**Key principle:** batch-confirm all threads first, fix and test everything, push once, then reply. A reply posted before push links to a commit the reviewer cannot open; a reply posted before tests is a claim you have not earned.

## Step 0: Pre-flight

```bash
gh pr view {N} --json number,url,headRefName,headRepositoryOwner,reviews \
  --jq '{number,url,headRefName,owner:.headRepositoryOwner.login,
         changesRequestedBy:[.reviews[]|select(.state=="CHANGES_REQUESTED")|.author.login]|unique}'
git status --porcelain                          # must be empty — unrelated edits would ride along in fix commits
git branch --show-current                       # must equal headRefName
git fetch origin && git status -sb | head -1    # "behind" → stop; ask the user how to sync
```

Any of the three failing → stop and say which. Do not stash, checkout, or rebase on the user's behalf.

## Step 1: Fetch Every Thread

The REST `pulls/{N}/comments` endpoint flattens threads, omits resolved/outdated state, and pages at 30. Use GraphQL:

```bash
gh api graphql --paginate -F owner={owner} -F repo={repo} -F pr={N} -f query='
query($owner:String!,$repo:String!,$pr:Int!,$endCursor:String){
  repository(owner:$owner,name:$repo){ pullRequest(number:$pr){
    reviewThreads(first:100,after:$endCursor){
      pageInfo{hasNextPage endCursor}
      nodes{ id isResolved isOutdated path line originalLine
        comments(first:50){ nodes{ databaseId url author{login} body } } } } } } }' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not)'
```

- `comments.nodes[0].databaseId` → the id you reply to. Thread `id` → what `--resolve` needs.
- Later comments in a thread are the conversation so far — read them; the last one may already answer or supersede the first.
- `isOutdated: true` → the anchored code has changed since; check whether the ask is already met.

Review bodies and PR-level comments carry verdicts, cross-cutting causes, and unverified claims that never appear inline:

```bash
gh pr view {N} --json reviews,comments \
  --jq '(.reviews[] | select(.body!="") | {kind:"review",author:.author.login,state,body}),
        (.comments[] | {kind:"issue",author:.author.login,body})'
```

Bring every item into one table:

| # | Thread / id | File:line | Author | Ask | Flags |
|---|-------------|-----------|--------|-----|-------|
| 1 | r1912345678 | auth/views.py:45 | @senior-dev | Add email validation | |
| 2 | r1912345690 | auth/services.py:23 | @security-lead | Token expiry 15 min | outdated |
| 3 | review body | — | @senior-dev | "Not convinced the flag is fully rolled out" | CHANGES_REQUESTED |
| 4 | r1912345702 | auth/tests.py:78 | coderabbit[bot] | Add expired-token test | bot |

## Step 2: Gate 1 — Confirm Once

Use AskUserQuestion **once** for the whole table. Each item gets one of:

- **Handle** — implement it.
- **Skip** — leave it; no reply unless the user adds "reply" (then the text goes through Gate 2).
- **Discuss** — you disagree or need scope/design input; draft a reply for Gate 2, do not implement.

Do not process anything before this answer. Do not ask again per item.

## Step 3: Evaluate and Implement Each Handle

Use `superpowers:receiving-code-review` discipline:

```
READ       → the whole thread, not only the first comment
UNDERSTAND → restate the ask in your own words
VERIFY     → check the suggestion against the actual code, not the reviewer's memory of it
EVALUATE   → sound for THIS codebase? in scope for THIS PR?
IMPLEMENT  → only after the above
```

**Forbidden responses:** "You're absolutely right!", "Great point!", "Let me implement that now" (before verification).

**If any Handle item is unclear: stop before implementing anything.** Items may be related; a partial understanding produces a wrong implementation. Say which items you understand and which need clarification.

| Question | If no |
|----------|-------|
| Technically correct? | Move it to Discuss with reasoning |
| Fits the codebase's conventions? | Discuss; propose the conventional form |
| In scope for this PR? | Discuss; propose a follow-up ticket instead |
| Security / bug fix? | Handle first |
| Pure style? | Accept unless it contradicts a documented convention |

**Red flags — do not blindly implement:** breaks existing tests, contradicts project conventions, introduces a security risk, reviewer misread the context.

**Implementing:**

- Use the Edit tool. Describing a fix is not resolving a comment.
- A comment containing a ` ```suggestion ` block that passed EVALUATE is applied **byte-for-byte**; the reply says "applied your suggestion". Do not retype it.
- After the edit, **re-read the comment** and confirm the change answers it — not just the line it pointed at. Check whether any other Handle item was anchored on lines you just changed; if so, re-evaluate it before continuing.
- Run the covering test (or typecheck/lint when there is none) **before committing**. Every commit in the series must be green on its own.

**Commit — one per resolved thread by default:**

```bash
git add -p auth/views.py          # stage only the fix, not incidental edits
git commit -F - <<'MSG'
fix(auth): validate email before DB query

Review-comment: https://github.com/{owner}/{repo}/pull/{N}#discussion_r{id}
MSG
```

- Reference the comment by URL in a trailer. `#12345` renders as issue #12345, not a comment; `@name` in a commit message pings on every push.
- Merge two threads into one commit when they touch the same construct or one ask spans several files; the reply for each thread names the commit. Never split so that an intermediate commit fails tests.

Track as you go:

| # | Author | Action | Status | Commit |
|---|--------|--------|--------|--------|
| 1 | @senior-dev | Handle | ✅ done | `abc1234` |
| 2 | @security-lead | Handle | 🔄 in progress | — |
| 3 | @senior-dev | Discuss | draft pending | — |
| 4 | coderabbit[bot] | Skip | ⏭️ | — |

## Step 4: Verify

Run the repo's full test command (from CLAUDE.md / CI config). Red → fix before pushing; if a fix commit caused it, add the correction **now**, before any SHA is public. Report the actual command and result.

## Step 5: Push

```bash
git push
```

Rejected (non-fast-forward) → **stop and report**. Never `--force`, never `--force-with-lease`: the reviewer may have pushed, and every SHA you are about to post would otherwise change.

## Step 6: Gate 2 — Outward Text

Everything you are about to post that is not a bare "Fixed in <sha>" is shown to the user first, in one batch:

- Discuss replies (pushback, alternative proposal, scope deferral)
- Skip-with-reply texts
- Any comment that tags another person ("@a @b — conflicting asks, which one?")

Post nothing from this list until the user approves the wording. You are speaking to their colleagues in their name.

## Step 7: Reply Per Thread

```bash
FULL_SHA=$(git rev-parse HEAD)   # or the specific commit for that thread
gh api repos/{owner}/{repo}/pulls/{N}/comments/{databaseId}/replies \
  -f body="Fixed in [\`${FULL_SHA:0:7}\`](https://github.com/{owner}/{repo}/commit/${FULL_SHA}) — validate_email now runs before the query."
```

One reply per thread, on the thread's first comment. One sentence of what changed; the link carries the diff.

`--resolve` → for each handled thread:

```bash
gh api graphql -f query='mutation($t:ID!){ resolveReviewThread(input:{threadId:$t}){ thread{ isResolved } } }' -f t={thread id}
```

## Step 8: Re-request Review

Reviewers whose last review was `CHANGES_REQUESTED` (from Step 0) need to look again; replies alone do not clear the block:

```bash
gh api -X POST repos/{owner}/{repo}/pulls/{N}/requested_reviewers -f 'reviewers[]={login}'
```

## Edge Cases

| Situation | Action |
|-----------|--------|
| Two reviewers conflict | Discuss — draft one comment tagging both (Gate 2), implement neither until they agree |
| Thread `isResolved` | Not in the table |
| Thread `isOutdated` | Check whether the ask is already met; if yes, reply so (Gate 2 text) instead of changing code |
| Vague comment | Ask the user first; if they cannot tell either, Discuss → reply asking the reviewer |
| Bot review with dozens of items | Still one table; mark `[bot]`; the user decides in Gate 1 |
| Remote moved during the work | Push rejected → stop; the user decides how to sync |

## Common Mistakes

| Mistake | Correct approach |
|---------|------------------|
| Reply "Fixed" before tests pass or before push | Fix all → test → push → reply. The link must open, the claim must be true |
| Fetch with REST `pulls/{N}/comments` | Flattens threads, no resolved state, 30-item page. Use GraphQL `reviewThreads` |
| Ignore review bodies / PR-level comments | They carry the verdict and cross-cutting asks; fetch them |
| Post pushback or tag reviewers without the user reading it | Gate 2 — every non-"Fixed" text is approved first |
| `#12345` / `@reviewer` in commit messages | Comment URL trailer; no mentions |
| `git add <file>` sweeping unrelated edits | Pre-flight requires a clean tree; stage with `-p` |
| Force-push to get past a rejected push | Never. Stop and report |
| Retype a reviewer's ` ```suggestion ` | Apply byte-for-byte |
| Ask per comment | One AskUserQuestion for the whole table |
| Describe the fix instead of editing | Edit tool, then re-read the comment |
