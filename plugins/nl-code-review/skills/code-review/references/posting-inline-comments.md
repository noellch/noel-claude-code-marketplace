# Posting Inline Review Comments

Everything about `--post` lives here: what goes where, how a comment reads, and the `gh api` mechanics. Read it in full before the first `gh api` call — an anchor outside the diff fails loudly, an anchor on the wrong in-diff line succeeds quietly.

## Two surfaces, two jobs

A sentence that appears on both is a sentence the author reads twice.

| Surface | Carries |
|---------|---------|
| **Review body** | First line, when any Blocking exists: `⚠ N 個 Blocking，建議 Request Changes（由人按）`. Then a counted index per tier, a few words each (`**Blocking ×2**（見 inline）：lockfile integrity、檢視版本入口失效`). Then, written out in full: root causes that span several findings, Unverified Claims, PR-description claims that did not survive verification, what you ran and what you only read, the verdict. |
| **Inline comment** | One finding, anchored to the line that has to change. |

The printed Output Format's finding lists collapse into the body's index — keep the section headings so the tiers stay countable, drop the evidence, which now lives on the anchors.

## Comment shape

Lead with the tier — `Blocking`, `Should fix`, `Nit`, `Context（不用改這裡）` — because tier is what to do about it. `Nit` is the printed Suggestions tier; `Context` is something the author should know that changes nothing in this diff. For Blocking and Should fix, the `[SEVERITY]` tag from the printed review follows the tier.

**Blocking / Should fix — sectioned:**

```
**[{tier}] [{SEVERITY}] {headline: what breaks, one sentence — not what the code does}**

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

**Language:** prose in the language the repo's existing review comments use; default Traditional Chinese prose with English identifiers. Code and identifiers exact.

- **Lead with the consequence.** The headline says what breaks; evidence comes after. A comment that opens with "這個 effect 在 X 時 early return" makes the reader assemble the consequence themselves.
- **A `suggestion` block is code you are shipping.** Emit one by default, but only after applying it in the Step 0 worktree and running the cheapest check that would catch a wrong fix: typecheck / lint on that file, the covering test if one exists (mechanics below). PERF fixes that reshape queries (join, prefetch, batching) need the covering test, not just a typecheck. If you cannot run anything, post a plain fenced block and say so in one line (`未實跑，依 {file}:{line} 推斷`). Not being sure of the surrounding idiom is a reason to go read the file, not a reason to describe the fix in prose. When the fix can't be a suggestion block (non-contiguous edit, anchored line isn't the line to change, displaced anchor), show the fixed code in a plain fenced block — never prose alone.
- **Say how you know only where the reader could get it wrong.** A review comment is assumed to come from reading the code; a marker identical on every anchor carries no information. Mark two cases: a claim about runtime behaviour you did not observe, and a comment written as a reproduction ("upload file A, swap in file B, the row now reads…"). Better than any label is the command that settles it — put that command in the comment. Never label a claim inferred when a cited file:line proves it.
- **The review event is the human's call.** Always `COMMENT`. `REQUEST_CHANGES` blocks the merge and has to be dismissed by a human; `APPROVE` is a human signature. State the verdict in the body and let them press it.

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

Head SHA is the `head` from Step 0 (`gh pr view {N} --json headRefOid -q .headRefOid`). Omitting `event` creates a PENDING review nobody sees.

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
| Submit `REQUEST_CHANGES` or `APPROVE` because the findings point that way | Both are the human's call. Post `COMMENT`, state the verdict, let them press it |
| Anchor to the line the finding is about, without checking the diff | Only lines inside a diff hunk are anchorable; the wrong in-diff line succeeds silently |
| Post a `suggestion` block you never ran | Apply it in the worktree and typecheck / test it. Cannot run → fenced block plus one line saying so |
| "Not sure how the surrounding code is written, so I'll describe the fix" | Go read those lines, then emit a `suggestion` block. Uncertainty is a lookup, not a downgrade |
