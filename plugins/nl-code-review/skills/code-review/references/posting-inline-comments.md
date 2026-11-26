# Posting Inline Review Comments

Everything about `--post` lives here: what goes where, how a comment reads, and the `gh api` mechanics. Read it in full before the first `gh api` call — an anchor outside the diff fails loudly, an anchor on the wrong in-diff line succeeds quietly.

## Two surfaces, two jobs

A sentence that appears on both is a sentence the author reads twice.

| Surface | Carries |
|---------|---------|
| **Review body** | The outcome line (below), then a counted index per tier, each led by its tier emoji, a few words each (`🛑 **Blocking ×2**（見 inline）：lockfile integrity、檢視版本入口失效`). Then `**合併前置**` when it applies (below). Then, written out in full: root causes that span several findings, Unverified Claims, PR-description claims that did not survive verification, what you ran and what you only read, the verdict. |
| **Inline comment** | One finding, anchored to the line that has to change. |

The printed Output Format's finding lists collapse into the body's index — keep the section headings so the tiers stay countable, drop the evidence, which now lives on the anchors.

**Outcome line** — the body's first line is exactly one of these three, picked by the counts, never a sentence of your own:

| Counts | First line | Event |
|---|---|---|
| ≥1 Blocking | `🛑 N 個 Blocking，建議 Request Changes（由人按）` | `COMMENT` |
| 0 Blocking, ≥1 Should fix | `🔧 N 個 Should fix，修完可 approve` | `COMMENT` |
| 0 Blocking, 0 Should fix | `✅ 沒有 Blocking / Should fix` | `APPROVE` |

**合併前置** (a body section, heading written as `**合併前置**`) — what must be true before this PR merges that the diff itself cannot fix: a PR it depends on is not merged yet, its migration number collides with a migration already on the base branch (re-list the base's migration directory at review time — another PR may have landed since CI ran), a deploy or rollout order. List only conditions that are **unmet** now, each with what breaks if it is ignored; a condition already satisfied is not listed. Omit the section when nothing is unmet. An unmet condition that would break a reachable path if the PR merged today (a missing parameter, two migration leaves, a deploy-time migrate failure) is also a finding at its tier — that is what keeps a dependent PR from being approved early. It stops counting once the PR is stacked on the dependency's branch or is a draft.

## Comment shape

Lead with the tier, prefixed by its emoji — `🛑 Blocking`, `🔧 Should fix`, `🧹 Nit`, `📝 Context（不用改這裡）` — because tier is what to do about it, and the emoji makes it scannable in the Files changed view. An inline comment carries only its tier emoji, once, at the start. `Nit` is the printed Suggestions tier; `Context` is something the author should know that changes nothing in this diff. For Blocking and Should fix, the severity from the printed review follows the tier.

**Blocking / Should fix — sectioned:**

```
**{tier emoji} {tier} · {SEVERITY} — {headline: what breaks, one sentence — not what the code does}**

**問題**

{mechanism, compressed. Evidence as a bullet list: the file:line chain the reader can
check themselves. End with the consequence if the headline alone doesn't carry it.}

**建議修法（範例）**

{a ```suggestion block when the edit is a contiguous replacement of the anchored lines;
otherwise a fenced code block showing the fixed code}

**測試**

{only when missing coverage is part of the finding: name the specific test that would pin it}
```

e.g. `**🔧 Should fix · BUG — backfill task 不在 watchdog 清單，20 分鐘就被 revoke 重送**`

**When the fix is a choice the author (or PM) must make**, `**建議修法（範例）**` becomes `**需要決定**`, and the headline ends as a question about that choice. Under it, one bullet per option: what the option does and what it costs. Options are prose bullets, never comments inside a code fence. Add a code block only for the option you would pick, and say that you would pick it. The tier stays what the defect warrants; the author answering with a reasoned choice resolves the finding.

```
**🔧 Should fix · BUG — 同網址＋同 UTM 的兩個區塊都顯示合計 clicks，要怎麼呈現？**

**問題**
{…}

**需要決定**

- clicks 也只算第一列：與 GA 口徑一致；第二個區塊顯示 0，看起來像沒人點
- 同 link_key 的區塊合併成一列：數字不重複；`area_index` 要改成 list，前端要配合
- 維持逐區塊一列、標「共用連結」：不動資料形狀；使用者要自己理解為何兩列相同
```

**Nit — one line, no headings:** `🧹 nit：{observation}` plus an optional example block. Section structure on a nit reads heavier than the finding warrants.

**Language:** prose in the language the repo's existing review comments use; default Traditional Chinese prose with English identifiers. Code and identifiers exact.

- **Lead with the consequence.** The headline says what breaks; evidence comes after. A comment that opens with "這個 effect 在 X 時 early return" makes the reader assemble the consequence themselves.
- **A `suggestion` block is code you are shipping.** Emit one by default, but only after applying it in the Step 0 worktree and running the cheapest check that would catch a wrong fix: typecheck / lint on that file, the covering test if one exists (mechanics below). PERF fixes that reshape queries (join, prefetch, batching) need the covering test, not just a typecheck. If you cannot run anything, post a plain fenced block and say so in one line (`未實跑，依 {file}:{line} 推斷`). Not being sure of the surrounding idiom is a reason to go read the file, not a reason to describe the fix in prose. When the fix can't be a suggestion block (non-contiguous edit, anchored line isn't the line to change, displaced anchor), show the fixed code in a plain fenced block — never prose alone.
- **Say how you know only where the reader could get it wrong.** A review comment is assumed to come from reading the code; a marker identical on every anchor carries no information. Mark two cases: a claim about runtime behaviour you did not observe, and a comment written as a reproduction ("upload file A, swap in file B, the row now reads…"). Better than any label is the command that settles it — put that command in the comment. Never label a claim inferred when a cited file:line proves it.
- **The review event follows the outcome line's table**, counting only findings that survived verification. Never `REQUEST_CHANGES`: it blocks the merge and has to be dismissed by a human. GitHub rejects approving your own PR (`422 Can not approve your own pull request`) — fall back to `COMMENT` and say so.

## One review, not N comments

Post every finding in a single review so the author gets one notification, and capture the review id for the verification step:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews --input review.json --jq .id
```

`gh api` fills `{owner}` and `{repo}` from the current repo — keep them literal. `--raw-field 'comments[0][path]=...'` does NOT work — the API receives an object, not an array. Always write a JSON file and pass it with `--input`.

```json
{
  "event": "COMMENT",
  "commit_id": "<head sha>",
  "body": "review body markdown",
  "comments": [
    { "path": "src/a.ts", "line": 42, "side": "RIGHT", "body": "..." },
    { "path": "src/b.ts", "start_line": 10, "start_side": "RIGHT", "line": 14, "side": "RIGHT", "body": "..." },
    { "path": "src/c.ts", "line": 7, "side": "LEFT", "body": "finding about a deleted line: old-side line number" }
  ]
}
```

Head SHA is the `head` from Step 0 (`gh pr view {N} --json headRefOid -q .headRefOid`). Omitting `event` creates a PENDING review nobody sees. `event` is `"APPROVE"` instead of `"COMMENT"` when no Blocking or Should fix survived (see the outcome line in Two surfaces); an approve may carry zero `comments`.

## The anchor must be inside a diff hunk

A `line` outside the diff fails with `Pull request review thread line must be part of the diff`. Worse, an in-diff line that is not the line you meant succeeds silently and points the author at the wrong code.

List the new-side ranges before choosing anchors:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate \
  --jq '.[] | select(.filename=="<path>") | .patch' | grep '^@@'
# @@ -115,7 +155,73 @@   →  new-side lines 155..227 are anchorable
```

`.patch` is absent for large or binary files; such a finding gets no inline anchor — put it in the body with its `file:line`.

New files are fully anchorable. Modified files usually are not — the line you want to talk about is often unchanged context. When that happens, anchor to the nearest changed line **inside the same construct** and name the real line in the text ("見 134-139 行"). Do not silently move the finding.

A displaced anchor never carries a ` ```suggestion ` block — the block would replace the anchor line, not the line you are talking about. Fenced block plus "見 N 行" instead.

## Suggestion blocks must match the target byte-for-byte

A ` ```suggestion ` block replaces exactly the commented line range. Wrong indentation produces a diff the author cannot apply. Read the real bytes first:

```bash
git show <head-sha>:<path> | sed -n '402,404p' | cat -A
```

Multi-line suggestion → the comment must carry `start_line` + `line` covering every line the block replaces.

Skip the suggestion when the fix spans non-contiguous ranges, needs a decision only the author can make, or drags in a change outside the anchor (a new hook dependency, a companion i18n key). Say which of those it was — "沒做成 suggestion 是因為…" — so the omission reads as a judgment, not an oversight.

## Run the suggestions before posting

A suggestion is applied with one click and no CI in between. Apply them yourself first, in the Step 0 worktree (`$W`, at `head`, already fetched):

```bash
# dependencies: symlink the main checkout's, or install once
ln -s "$(git rev-parse --show-toplevel)/node_modules" "$W/node_modules"
# baseline first, so pre-existing failures are not blamed on your edits
npx tsc --noEmit -p "$W"                            # or: ruff check <file> / go vet ./...
# apply every non-overlapping suggestion, then run the check once
pytest "$W/<test_file>::<case>"                     # the covering test, if one exists
```

One worktree, all suggestions, one run. If the run fails, revert suggestions one at a time to find the culprit. Several suggestions in one file: check that their line ranges do not overlap and that none depends on another being applied first. If they do, merge them into one comment spanning both ranges, or demote one to a fenced block.

## Verify after posting

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate \
  --jq '.[] | select(.pull_request_review_id==<id>) | "\(.path):\(.start_line // .line)-\(.line) \(if (.body|test("```suggestion")) then "[suggestion]" else "" end)"'
```

`<id>` is the value captured when posting. Anchors that silently drifted show up here and nowhere else. A `[suggestion]` on a range you did not intend is the worst case — delete that comment before the author sees it.

## Re-review: the author answered your last review

A follow-up round answers what changed since your review, nothing else. The reading scope is SKILL.md Step 0's Re-review row (`base` = your last review's `commit_id`). Then take each of your previous threads to exactly one disposition:

| Author's response | Check | GitHub action |
|---|---|---|
| Says fixed | Read the fix in the `base..head` diff and run the covering test if one was added | None. A verified fix needs no thread reply |
| Says fixed, but the fix is wrong or incomplete | Cite the line that is still wrong | Reply in that thread; the finding stays open |
| Declines with a reason you accept | The reason holds against the code or a recorded decision | One-line reply in that thread: `接受：{why}`. The finding is closed |
| Declines with a reason you do not accept | — | Reply in that thread with why; the finding stays open |
| No response | — | The finding stays open; no new comment |

Code the fixes added is reviewed like any new code, and its findings are new inline comments. Then post one new review whose outcome line counts **open** findings only — still-open old ones plus new ones. The body carries:

- The outcome line and, when anything is open, its index.
- One line for what closed: `前一輪 N 條：M 條已修、K 條接受作者說明`. Do not restate them one by one.
- `**合併前置**`, re-checked now, not copied from the last round.
- Unverified Claims only if one changed since the last round.
- What you ran this round.

When nothing is open, this is a short `APPROVE`.

## Reworking a review you already submitted

A submitted review cannot be deleted. Its parts can:

```bash
gh api -X DELETE repos/{owner}/{repo}/pulls/comments/{comment_id}            # per comment
gh api -X PUT repos/{owner}/{repo}/pulls/{N}/reviews/{review_id} -f body='…'  # shrink the body
gh api repos/{owner}/{repo}/pulls/{N}/comments/{comment_id}/replies -f body='…'  # reply in a thread
```

Delete only comments with no replies; a comment the author has already answered keeps its thread — reply "已由新 review 取代，見 {link}" and resolve it. Resolving is GraphQL only:

```bash
gh api graphql -f query='mutation { resolveReviewThread(input:{threadId:"<thread node id>"}) { thread { isResolved } } }'
# thread node ids: gh api graphql -f query='{ repository(owner:"O",name:"R"){ pullRequest(number:N){ reviewThreads(first:100){ nodes{ id isResolved comments(first:1){ nodes{ databaseId path } } } } } } }'
```

Shrink the old body to a one-line pointer, then post the replacement as a new review. Leaving both live doubles what the author has to read.

## Traps

| Symptom | Cause / Fix |
|---|---|
| `422 user_id can only have one pending review` | Your own unsubmitted review exists. Find it with `gh api repos/{owner}/{repo}/pulls/{N}/reviews --jq '.[] | select(.state=="PENDING") | .id'`, then `gh api -X DELETE .../pulls/{N}/reviews/{id}`, then post again. |
| `commit_sha is not part of the pull request` | Stale SHA — refetch `head`. |
| zsh: URL contains literal `\n` | `for id in $ids` does not word-split in zsh. Use an array: `ids=(1 2 3)`. |

## Posting failure modes

| Failure / Excuse | Reality / What to Do |
|------------------|----------------------|
| Restate each inline finding in the review body too | Body carries the index, verdict and cross-cutting causes only; duplication makes the author read it twice |
| One global "I didn't run the app" note in the body | Files changed shows one anchor at a time. Put it on the anchors whose claims need it |
| Close every comment with the same "didn't run it" tag | A marker that never varies carries no information. Mark only what a reader could mistake for something you observed |
| Tag a finding "inferred" when a cited file:line already proves it | That understates your evidence. Cite the line and drop the tag |
| Submit `REQUEST_CHANGES` because the findings point that way | That is the human's call. Post `COMMENT`, state the verdict, let them press it |
| `APPROVE` while a Blocking or Should fix is still open, or before re-reading the cited lines | Approve only on zero Blocking and zero Should fix that survived verification; otherwise `COMMENT` |
| "The dependency is written in the body, so the code is approvable" | An unmet 合併前置 that breaks if merged today is a finding at its tier until the PR is stacked or draft — a note in the body does not stop someone pressing merge |
| Re-review body walks through every previous finding again ("the old threads are resolved, so I'll explain here") | One closed-count line. The author lived through those threads; only what is still open or new gets words |
| Anchor to the line the finding is about, without checking the diff | Only lines inside a diff hunk are anchorable; the wrong in-diff line succeeds silently |
| Post a `suggestion` block you never ran | Apply it in the worktree and typecheck / test it. Cannot run → fenced block plus one line saying so |
| "Not sure how the surrounding code is written, so I'll describe the fix" | Go read those lines, then emit a `suggestion` block. Uncertainty is a lookup, not a downgrade |
