---
name: stack-pr
description: Use when pull requests depend on each other — one PR's base is another PR's branch — and the user wants to add to, update, collapse, or abandon the stack: "stacked PRs", "PR stack", "疊 PR", "下層 PR merge 了", "更新下游 PR", "rebase stack". Rewrites branch history and force-pushes (with lease). A single PR → nl-create-pr.
---

# Stack PR

One rule carries every flow here: **a stacked branch is moved with `git rebase --onto <new base> <old base>`, where `<old base>` is the commit the branch was actually built on.** Plain `git rebase <new base>` has to guess the old base from patch-ids, and after a squash merge or an amended parent nothing matches — it replays the parent's commits and conflicts.

## Step 0: Pre-flight and Picture (always first)

```bash
git status --porcelain                  # must be empty; a rebase on a dirty tree stops half-way
BASE=$(gh pr view <bottom PR> --json baseRefName -q .baseRefName)   # the stack's base is PR1's base — never assume develop
gh pr list --author @me --state open --json number,headRefName,baseRefName,headRefOid,author \
  --template '{{range .}}#{{.number}} {{.headRefName}} → {{.baseRefName}} @{{slice .headRefOid 0 7}}{{"\n"}}{{end}}'
```

Draw the chain before touching anything:

```
$BASE
  └── feat/a   PR1
        └── feat/b   PR2
              └── feat/c   PR3
```

**Capture every old tip before the first fetch** — `git fetch` moves `origin/*`, and `--prune` deletes the refs you still need:

```bash
for b in feat/a feat/b feat/c; do echo "$b $(git rev-parse -q --verify origin/$b)"; done   # keep this table
git fetch origin                        # without --prune
```

A branch whose PR author is not you → confirm with the user before force-pushing it. No `gh` access → the PR facts come from the user; say which ones you could not verify.

## Collapse After the Bottom PR Merges

PR1 (`feat/a`) merged into `$BASE`. GitHub retargets PR2 to `$BASE` by itself when the head branch is deleted — check, do not assume, and either way PR2's diff still shows PR1's commits until you rebase.

```bash
gh pr view <PR2> --json baseRefName -q .baseRefName     # feat/a → needs `gh pr edit` later; $BASE → already retargeted
```

Old base for `feat/b` = the merge-base of `feat/b` and PR1's line. PR1's tip may no longer exist in your clone; take it from the captured `origin/feat/a` (stale is fine — the merge-base is the same), or from the PR ref GitHub keeps after the branch is deleted:

```bash
PARENT_TIP=$(git rev-parse -q --verify origin/feat/a || (git fetch -q origin refs/pull/<PR1>/head && git rev-parse FETCH_HEAD))
OLD=$(git merge-base feat/b "$PARENT_TIP")
OLD_B=$(git rev-parse origin/feat/b)          # PR2's own old tip, for the lease and the check below
git checkout feat/b
git rebase --onto origin/$BASE "$OLD"
```

- Conflict → resolve and `git rebase --continue`, or `git rebase --abort` and report. **Never push while `git status` shows a rebase in progress.**
- Verify before pushing: `git log --oneline origin/$BASE..feat/b` lists exactly PR2's own commits (same count and subjects as `git log --oneline $OLD..$OLD_B`); `git range-diff $OLD..$OLD_B origin/$BASE..feat/b` shows no content change you did not make; run the tests the repo names.

```bash
git push --force-with-lease=feat/b:$OLD_B origin feat/b
gh pr view <PR2> --json baseRefName -q .baseRefName     # still feat/a → gh pr edit <PR2> --base $BASE
```

Then PR3, with `feat/b` as the parent: `OLD` is the captured old `origin/feat/b` tip, new base is the rewritten `feat/b`:

```bash
OLD_C=$(git rev-parse origin/feat/c)
git checkout feat/c && git rebase --onto feat/b "$OLD_B" && git push --force-with-lease=feat/c:$OLD_C origin feat/c
```

PR3's base (`feat/b`) does not change. **Bottom to top, never skip a level.**

## Parent Got New Commits (not merged yet)

Same move. PR1 gained review fixes — or was amended and force-pushed, which plain rebase cannot tell apart from new work:

```bash
# OLD_A = captured origin/feat/a tip from Step 0; origin/feat/a is now the new tip
git checkout feat/b && git rebase --onto origin/feat/a "$OLD_A" && git push --force-with-lease=feat/b:$OLD_B origin feat/b
```

Continue upward with the same pattern; the verification and conflict rules above apply at every level.

## Adding a PR on Top

Branch from the parent's current tip, commit, then hand the PR to **nl-create-pr with the parent branch as base** — it owns the scope gate, the repo's PR template, the `Tests:` line and `gh pr create`:

```bash
git fetch origin && git checkout -b feat/c origin/feat/b
# ... commit ...
```

Work that already sits on another branch is moved, not re-created: `git rebase --onto origin/feat/b <old base>` first. Put `Depends on #<parent PR>` in the body so reviewers read the chain in order.

## When to Abandon the Stack

Abandon into one PR when any of these holds: three or more rounds of rebase conflicts across the chain, reviewers can no longer follow the diffs, the original dependency is gone. Say so to the user first, then:

```bash
git checkout -b feat/combined origin/$BASE
git merge --squash feat/c                     # the top of the stack carries everything below it
git commit -m "<type>(<scope>): <summary>"
# nl-create-pr with base $BASE, then close the old PRs:
gh pr close <n> --comment "Superseded by #<new>"   # for each PR in the stack
```

## Done When

- Every branch in the stack holds exactly its own commits above its parent (`git log origin/<parent>..<branch>` matches the pre-rebase list).
- Every PR's base is the branch below it, or `$BASE` for the bottom one (`gh pr view --json baseRefName` per PR).
- `git status` clean, no rebase in progress, tests green at the top of the stack.
- The user is told which steps needed `gh` and could not run, if any.

## Failure Modes

| Excuse | Reality |
|--------|---------|
| "Parent is deleted, so plain `git rebase origin/$BASE` — git detects merged commits" | Only for merge commits. A squash commit matches no patch-id; the parent's commits replay and conflict. Always `--onto` with the merge-base |
| "`origin/feat/a` is still there, use it as the old base" | It is a stale ref after auto-delete; fine for the merge-base, wrong as "the parent still exists". Check `git ls-remote --heads origin feat/a` |
| "Conflict — I'll push what I have and sort it out after" | Never push mid-rebase; `--continue` or `--abort` |
| "GitHub doesn't retarget the base" | It does when the head branch is deleted. `gh pr view` first, `gh pr edit` only if still pointing at the parent |
| "The base is `develop`" | The stack's base is PR1's `baseRefName`; other repos use `main` |
| "I'll `gh pr create` from here" | nl-create-pr owns PR creation; this skill moves branches |
