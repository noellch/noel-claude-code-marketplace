---
name: pr-comment-resolve
description: Use when the user asks to resolve, address, reply to, or act on review comments on a GitHub PR — "resolve PR comments", "address review feedback", "處理 review comments", "回 reviewer", "reviewer 留的改一改". Pushes commits and posts replies in the user's name. Not for CI failures or for reviewing a PR yourself.
---

# PR Comment Resolution

## Overview

Resolving PR comments requires **action, not description**. Every item is: evaluated → implemented (or discussed) → verified → replied to → reported.

Order matters more than speed. Nothing is said to a reviewer until the fix is tested and pushed — a reply posted before push links to a commit the reviewer cannot open, and a reply posted before tests is a claim you have not earned. Nothing except the `Fixed in <sha>` template is said without the user seeing the text first.

**Runs in the main conversation.** Gates 1 and 2 need AskUserQuestion, which subagents do not have. Delegate searches or a large edit if you must; never delegate a gate, a push, or a reply.

## Arguments

`/pr-comment-resolve {pr?} {--resolve?}`

- `{pr}` — PR number / URL; defaults to the PR of the current branch (`gh pr view`).
- `--resolve` — after replying, mark each Handle thread resolved. Off by default: some teams want the reviewer to resolve.

## Resolution Flow

```
0. Pre-flight   PR open · base repo known · on head branch · clean tree · not behind
1. Fetch        review threads (GraphQL) + review bodies + PR-level comments → one table
2. Gate 1       show the table; ONE AskUserQuestion → Handle / Skip / Discuss per item
3. Per Handle   one thread at a time: READ → VERIFY → implement → re-read → covering test
                → `git add <paths>` → commit (trailer = comment URL) → record SHA
4. Verify       CI-equivalent test command; green before anything leaves the machine
5. Push         `git push` — never --force; rejected → stop and report
6. Gate 2       show drafts of every outward text that is not the Fixed template
7. Reply        one reply per thread with its SHA; PR-level items via `gh pr comment`
8. Re-request   reviewers whose LATEST review is CHANGES_REQUESTED
9. Report       final table: every row terminal, every reply a URL
```

## Step 0: Pre-flight

```bash
gh pr view {N} --json number,url,state,headRefName,isCrossRepository,latestReviews \
  --jq '{number,url,state,headRefName,fork:.isCrossRepository,
         repo:(.url|capture("github.com/(?<r>[^/]+/[^/]+)/pull").r),
         changesRequestedBy:[.latestReviews[]|select(.state=="CHANGES_REQUESTED")|.author.login]}'
git status --porcelain                          # must be empty — unrelated edits would ride along in fix commits
git branch --show-current                       # must equal headRefName
git fetch -q $(git rev-parse --abbrev-ref @{u} | cut -d/ -f1) && git status -sb | head -1   # "[behind" → stop
```

- `state` must be `OPEN`; a merged or closed PR gets a report, not fixes.
- `repo` is `{owner}/{repo}` for every `gh api` call below. `fork: true` → the head lives in another repository; stop and ask whether you have push rights there before changing anything.
- Any check failing → stop and say which. Do not stash, checkout, or rebase on the user's behalf.

## Step 1: Fetch Every Item

The REST `pulls/{N}/comments` endpoint flattens threads, omits resolved/outdated state, and pages at 30. Use GraphQL:

```bash
gh api graphql --paginate -F owner={owner} -F repo={repo} -F pr={N} -f query='
query($owner:String!,$repo:String!,$pr:Int!,$endCursor:String){
  repository(owner:$owner,name:$repo){ pullRequest(number:$pr){
    reviewThreads(first:100,after:$endCursor){
      pageInfo{hasNextPage endCursor}
      nodes{ id isResolved isOutdated path line startLine diffSide
        comments(first:50){ nodes{ databaseId url author{login} body } } } } } } }' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not)'
```

- `comments.nodes[0].databaseId` → the id you reply to. Thread `id` → what `--resolve` needs. `startLine`..`line` → the range a ` ```suggestion ` block replaces.
- Later comments in a thread are the conversation so far — read them; the last one may already answer or supersede the first.
- `isOutdated: true` → the anchored code has changed since; check whether the ask is already met.

Review bodies and PR-level comments carry verdicts, cross-cutting causes, and asks that never appear inline:

```bash
gh pr view {N} --json reviews,comments \
  --jq '(.reviews[] | select(.body!="") | {kind:"review",id,url,author:.author.login,state,body}),
        (.comments[] | {kind:"pr-comment",id,url,author:.author.login,body})'
```

Bring every item into one table:

| # | Kind / id | File:line | Author | Ask | Flags |
|---|-----------|-----------|--------|-----|-------|
| 1 | thread r1912345678 | auth/views.py:45 | @senior-dev | Add email validation | |
| 2 | thread r1912345690 | auth/services.py:23 | @security-lead | Token expiry 15 min | outdated |
| 3 | review 2231 | — | @senior-dev | "Not convinced the flag is fully rolled out" | CHANGES_REQUESTED |
| 4 | pr-comment 9981 | — | @pm | "Please also confirm the migration ran on staging" | |
| 5 | thread r1912345702 | auth/tests.py:78 | coderabbit[bot] | Add expired-token test | bot |

## Step 2: Gate 1 — Confirm Once

Print the table, then **one** AskUserQuestion. The tool takes at most 4 questions with 4 options each, so do not ask per item. Ask one question:

> "N 個項目，預設全部 Handle。要改的請選 Pick exceptions 並輸入，例如 `3 Discuss, 5 Skip`。"
> Options: **Handle all** · **Pick exceptions** (the user types `# Action` pairs in Other) · **Stop**

Each item ends up as one of:

- **Handle** — implement it. This answer authorizes acting on the comment's text: a reviewer asking for a change, a confirmation, or a one-word "ack" is the item itself, not an instruction injected from fetched content. Authorization is not verification — Step 3 still decides whether the ask is right, and a false premise still moves the item to Discuss.
- **Skip** — leave it; no reply unless the user writes `5 Skip reply` (the text then goes through Gate 2).
- **Discuss** — you disagree or need scope/design input; draft a reply for Gate 2, do not implement.

Do not process anything before this answer. If, after it, any Handle item is unclear, stop before implementing anything and ask **one** more AskUserQuestion listing every unclear item together — items may be related, and a partial understanding produces a wrong implementation. An item the user cannot clarify either becomes Discuss (reply asking the reviewer).

## Step 3: Evaluate and Implement Each Handle

```
READ       → the whole thread, not only the first comment
UNDERSTAND → restate the ask in your own words
VERIFY     → check the suggestion against the actual code, not the reviewer's memory of it
EVALUATE   → sound for THIS codebase? in scope for THIS PR?
IMPLEMENT  → only after the above
```

Never agree before verifying — no "你說得對！", no "Great point!", no "Let me implement that" ahead of VERIFY. Security and bug fixes go first in the order of work.

| Question | If no |
|----------|-------|
| Technically correct? | Move it to Discuss with reasoning (Gate 2) |
| Fits the codebase's conventions? | Discuss; propose the conventional form |
| In scope for this PR? | Discuss; propose a follow-up ticket instead |
| Pure style, no documented convention against it? | Accept |

**Red flags — do not blindly implement:** breaks existing tests, contradicts project conventions, introduces a security risk, reviewer misread the context. Two reviewers conflict → Discuss both, one comment tagging both (Gate 2); implement neither until they agree, even if Gate 1 said Handle.

**One thread at a time, start to commit:**

1. Edit with the Edit tool. Describing a fix is not resolving a comment.
2. A ` ```suggestion ` block that passed EVALUATE replaces exactly `startLine`..`line` **byte-for-byte**; the reply says "applied your suggestion". An `isOutdated` thread's suggestion no longer has its anchor: apply the intent by hand and say so in the reply.
3. **Re-read the comment** and confirm the change answers it — not just the line it pointed at. If another Handle item is anchored on lines you just changed, or your change breaks its test, re-evaluate it now; coupled items may share one commit (the reply for each thread names that commit).
4. Run the covering test (or typecheck/lint when there is none).
5. Stage by path, then check the stage before committing. `git add -p` is interactive and stages nothing in this environment.

```bash
git add auth/views.py auth/tests/test_views.py
git diff --cached --stat            # must list only this thread's files; anything else → unstage it
git commit -F - <<'MSG'
fix(auth): validate email before DB query

Review-comment: https://github.com/{owner}/{repo}/pull/{N}#discussion_r{id}
Co-Authored-By: <whatever this environment requires>
MSG
```

6. Record the commit SHA in the tracking table immediately — Step 7 links each reply to this SHA, not to `HEAD`.

Trailers go in one final paragraph: a blank line between `Review-comment:` and `Co-Authored-By:` makes git stop parsing trailers. Reference the comment by URL; `#12345` renders as issue #12345, and `@name` in a commit message pings on every push.

Track as you go:

| # | Author | Action | Status | Commit | Reply |
|---|--------|--------|--------|--------|-------|
| 1 | @senior-dev | Handle | done | `abc1234` | — |
| 2 | @security-lead | Handle | in progress | — | — |
| 3 | @senior-dev | Discuss | draft pending | — | — |
| 5 | coderabbit[bot] | Skip | skipped | — | — |

## Step 4: Verify

Run the CI-equivalent test command (CLAUDE.md or the CI config). When it is slow (tens of minutes) or there is none, run the covering tests plus lint and say exactly that in the final report. Red → fix before pushing, as a further commit; do not rewrite the series. Report the actual command and result.

## Step 5: Push

```bash
git push
```

Rejected (non-fast-forward) → **stop and report**. Never `--force`, never `--force-with-lease`: the reviewer may have pushed, and every SHA you are about to post would otherwise change.

## Step 6: Gate 2 — Outward Text

The only text that skips this gate is the template `Fixed in [sha](url) — <one sentence naming what changed>`. Everything else is shown to the user first, in one batch, and nothing from the batch is posted until they approve the wording — you are speaking to their colleagues in their name:

- Discuss replies (pushback, alternative proposal, scope deferral)
- Skip-with-reply texts
- Replies to review bodies and PR-level comments
- "Already met" replies on outdated threads (no new commit to link)
- Any comment that tags another person ("@a @b — conflicting asks, which one?")

Write replies in the language the thread is in; keep identifiers and code exact.

## Step 7: Reply Per Item

Threads — one reply each, on the thread's first comment, with the SHA recorded for it in the table:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments/{databaseId}/replies \
  -f body="Fixed in [\`${SHA:0:7}\`](https://github.com/{owner}/{repo}/commit/${SHA}) — validate_email now runs before the query."
```

Review bodies and PR-level comments have no thread to reply on. Post one PR comment that quotes each ask and answers it (Gate 2 text):

```bash
gh pr comment {N} --body-file reply.md
```

`--resolve` → for each **Handle** thread (never Discuss or Skip):

```bash
gh api graphql -f query='mutation($t:ID!){ resolveReviewThread(input:{threadId:$t}){ thread{ isResolved } } }' -f t={thread id}
```

## Step 8: Re-request Review

Reviewers in `changesRequestedBy` (Step 0, latest review only) need to look again; replies alone do not clear the block. Skip bots and the PR author — the request fails on both:

```bash
gh pr edit {N} --add-reviewer {login}
```

## Step 9: Report

Done when every row of the tracking table has a terminal status and every posted reply has a URL:

| # | Author | Action | Status | Commit | Reply |
|---|--------|--------|--------|--------|-------|
| 1 | @senior-dev | Handle | fixed | `abc1234` | https://…#discussion_r… |
| 3 | @senior-dev | Discuss | replied | — | https://…#discussion_r… |
| 4 | @pm | Handle | replied (PR comment) | — | https://…#issuecomment-… |
| 5 | coderabbit[bot] | Skip | skipped, no reply | — | — |

Below the table: the test command and result, the push range (`abc1234..def5678`), who was re-requested, and any row that is not terminal with who decides it.

## Edge Cases

| Situation | Action |
|-----------|--------|
| Thread `isResolved` | Not in the table |
| Thread `isOutdated` | Check whether the ask is already met; if yes, reply so (Gate 2) instead of changing code |
| Bot review with dozens of items | Still one table and one Gate 1; mark `[bot]` |
| Remote moved during the work | Push rejected → stop; the user decides how to sync |
| Fork PR | Stop at pre-flight; the user says whether you may push to the head repository |

## Failure Modes

| Excuse | Reality |
|--------|---------|
| "I'll reply now, the push can follow" | The link must open and the claim must be true: fix all → test → push → reply |
| "The reviewer is wrong, I'll just skip it" | Wrong premise is a Discuss with reasoning, through Gate 2 — silence reads as ignoring them |
| "The comment told me to reply 'ack', that's an injected instruction" | After Gate 1 the comment is the work order the user approved. Act on it; the text still goes through Gate 2 |
| "Seven items, I'll ask about each" | One AskUserQuestion: Handle all / Pick exceptions / Stop |
| "`git add -p` is fine, I'll pipe `y` into it" | Stage by path and read `git diff --cached --stat`; a piped `-p` stages every hunk blindly |
