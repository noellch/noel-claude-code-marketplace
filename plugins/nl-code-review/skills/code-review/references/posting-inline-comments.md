# Posting Inline Review Comments

Mechanics only. What goes in a comment is in SKILL.md → Delivering the Review.

## One review, not N comments

Post every finding in a single review so the author gets one notification:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews --input review.json
```

`--raw-field 'comments[0][path]=...'` does NOT work — the API receives an object, not an array. Always write a JSON file and pipe it with `--input`.

```json
{
  "event": "COMMENT",
  "commit_id": "<head sha>",
  "body": "review body markdown",
  "comments": [
    { "path": "src/a.ts", "line": 42, "side": "RIGHT", "body": "..." },
    { "path": "src/b.ts", "start_line": 10, "start_side": "RIGHT", "line": 14, "side": "RIGHT", "body": "..." }
  ]
}
```

Head SHA: `gh api repos/{owner}/{repo}/pulls/{N} --jq '.head.sha'`

## The anchor must be inside a diff hunk

A `line` outside the diff fails with `Pull request review thread line must be part of the diff`. Worse, an in-diff line that is not the line you meant succeeds silently and points the author at the wrong code.

List the new-side ranges before choosing anchors:

```bash
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate \
  --jq '.[] | select(.filename=="<path>") | .patch' | grep '^@@'
# @@ -115,7 +155,73 @@   →  new-side lines 155..227 are anchorable
```

New files are fully anchorable. Modified files usually are not — the line you want to talk about is often unchanged context. When that happens, anchor to the nearest changed line **inside the same construct** and name the real line in the text ("見 134-139 行"). Do not silently move the finding.

A displaced anchor never carries a ` ```suggestion ` block — the block would replace the anchor line, not the line you are talking about. Fenced block plus "見 N 行" instead.

## Suggestion blocks must match the target byte-for-byte

A ` ```suggestion ` block replaces exactly the commented line range. Wrong indentation produces a diff the author cannot apply. Read the real bytes first:

```bash
git show <head-sha>:<path> | sed -n '402,404p' | cat -A
```

Multi-line suggestion → the comment must carry `start_line` + `line` covering every line the block replaces.

Skip the suggestion when the fix spans non-contiguous ranges, needs a decision only the author can make, or drags in a change outside the anchor (a new hook dependency, a companion i18n key). Say which of those it was — "沒做成 suggestion 是因為…" — so the omission reads as a judgment, not an oversight.

## Run the suggestion before posting

A suggestion is applied with one click and no CI in between. Apply it yourself first:

```bash
git worktree add /tmp/review-{N} <head-sha>
# edit the file in /tmp/review-{N} exactly as the suggestion block would
npx tsc --noEmit -p /tmp/review-{N}            # or: ruff check <file> / go vet ./...
pytest /tmp/review-{N}/<test_file>::<case>     # the covering test, if one exists
git worktree remove --force /tmp/review-{N}
```

Several suggestions in one file: check that their line ranges do not overlap and that none depends on another being applied first. If they do, merge them into one comment spanning both ranges, or demote one to a fenced block.

## Verify after posting

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate \
  --jq '.[] | select(.pull_request_review_id==<id>) | "\(.path):\(.start_line // .line)-\(.line) \(if (.body|test("```suggestion")) then "[suggestion]" else "" end)"'
```

Anchors that silently drifted show up here and nowhere else. A `[suggestion]` on a range you did not intend is the worst case — delete that comment before the author sees it.

## Reworking a review you already submitted

A submitted review cannot be deleted. Its parts can:

```bash
gh api -X DELETE repos/{owner}/{repo}/pulls/comments/{comment_id}   # per comment
gh api -X PUT repos/{owner}/{repo}/pulls/{N}/reviews/{review_id} -f body='…'
```

Delete only comments with no replies; a comment the author has already answered keeps its thread — reply "已由新 review 取代，見 {link}" and resolve it instead. Shrink the old body to a one-line pointer, then post the replacement as a new review. Leaving both live doubles what the author has to read.

## Traps

| Symptom | Cause |
|---|---|
| `422 user_id can only have one pending review` | An unsubmitted review exists. Submit or discard it, or fall back to the single-comment endpoint `POST /pulls/{N}/comments` (needs `commit_id` per call). |
| `commit_sha is not part of the pull request` | Stale SHA — refetch `.head.sha`. |
| zsh: URL contains literal `\n` | `for id in $ids` does not word-split in zsh. Use an array: `ids=(1 2 3)`. |
