---
name: stack-pr
description: Use when managing dependent pull requests where one PR is based on another — triggers on "stacked PRs", "PR stack", "PR1 merged what now", "update downstream PR", "rebase stack", or when a PR's base is another PR's branch
---

# Stack PR

Manages the lifecycle of a stacked PR chain: visualizing the stack, adding to it, updating when upstream changes, and collapsing when PRs merge.

**Prerequisite:** Use `nl-create-pr` for single PRs. Use this skill when PRs have dependencies.

## Step 0: Visualize the Stack (Always First)

Before any operation, establish the full picture:

```bash
git fetch origin

# All open PRs with base branches
gh pr list --state open --json number,title,headRefName,baseRefName \
  --template '{{range .}}#{{.number}} {{.headRefName}} → {{.baseRefName}}: {{.title}}{{"\n"}}{{end}}'

# Commit graph
git log --oneline --graph develop..HEAD
```

Build a mental model before touching anything:
```
develop
  └── feat/base-schema          ← PR1 (open)
        └── feat/feature        ← PR2 (open)
              └── feat/ui       ← PR3 (open)
```

## Adding a PR to the Stack

Branch off from the **immediate parent branch** (not develop):

```bash
git checkout feat/feature          # parent branch
git pull origin feat/feature       # ensure it's up to date
git checkout -b feat/new-work
# ... make changes, commit ...
git push -u origin feat/new-work
gh pr create --base feat/feature --title "feat: new work"
```

## After a PR Merges — Collapse the Stack

When PR1 (`feat/base-schema`) merges into `develop`, update PR2's base.

**Use `rebase --onto` for precision** — it replays only PR2's own commits, explicitly discarding the old parent:

```bash
git fetch origin

git checkout feat/feature
git rebase --onto origin/develop origin/feat/base-schema
# ↑ rebase --onto <new-base> <old-base> <branch (current)>

git push origin feat/feature --force-with-lease

# Update PR base in GitHub
gh pr edit <PR2-number> --base develop
```

**Choose the right rebase form based on whether the parent branch still exists:**

```
Parent branch still exists on remote? (origin/feat/base-schema)
  ├─ YES → git rebase --onto origin/develop origin/feat/base-schema
  │         (explicit: "replay only commits between old-base and HEAD")
  └─ NO  → git rebase origin/develop
            (parent already deleted; Git correctly detects merged commits)
```

Default to `--onto` — it fails loudly if you get the branch name wrong.

Then repeat for PR3:

```bash
git checkout feat/ui
git rebase origin/feat/feature     # parent is now updated
git push origin feat/ui --force-with-lease
# PR3's base (feat/feature) stays the same — no gh pr edit needed
```

**Rule: rebase top-to-bottom (PR2 → PR3). Never skip a level.**

## Updating When a Parent Gets New Commits

When PR1 gets review feedback and its branch changes:

```bash
git fetch origin

# Update PR2
git checkout feat/feature
git rebase origin/feat/base-schema
git push origin feat/feature --force-with-lease

# Update PR3
git checkout feat/ui
git rebase origin/feat/feature
git push origin feat/ui --force-with-lease
```

Always use `origin/<branch>` (remote ref after `git fetch`), not the local branch name — ensures you rebase onto the latest remote state.

## Verify After Each Collapse

```bash
# Confirm PR2 now targets develop
gh pr view <PR2-number> --json baseRefName -q '.baseRefName'
# Expected: develop
```

## When to Abandon the Stack

Abandon and merge into a single PR when:
- 3+ rounds of rebase conflicts across branches
- PRs have diverged so much reviewers can't follow the chain
- The original dependency no longer exists

Tell the user:
> "The stack has become difficult to maintain. I recommend squashing into a single branch targeting develop and creating one combined PR."

```bash
git checkout develop
git checkout -b feat/combined
git merge --squash feat/ui          # squash entire stack into one commit
git commit -m "feat: combined PR description"
gh pr create --base develop --title "feat: ..."
```

## Common Mistakes

| Mistake | Correct Approach |
|---------|----------------|
| `git rebase develop` (local branch) | `git rebase origin/develop` (fetch first, use remote ref) |
| `git rebase origin/develop` when parent still exists on remote | Use `--onto origin/develop origin/feat/parent` |
| `--onto origin/develop origin/feat/parent` when parent was deleted | Parent gone → plain `git rebase origin/develop` |
| Rebase PR3 before PR2 | Always top-to-bottom: PR2 first, then PR3 |
| `git push --force` | Always `--force-with-lease` |
| Forget `gh pr edit --base develop` | GitHub doesn't auto-update base after parent merges |
| Skip `git fetch origin` before rebase | Remote may have changed; always fetch first |
