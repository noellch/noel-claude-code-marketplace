---
name: create-pr
description: Use when ready to deliver work as a pull request — triggers on "create PR", "open PR", "發 PR", "push and PR", "submit for review", or after finishing a feature, fix, or refactor
---

# Create PR

Delivers completed work as a focused PR following FoD (Feature on Demand) principles. FoD scope check is a **hard gate** — skip it and you will create PRs that are too large to review.

## Phase 1: FoD Scope Check (Hard Gate — Do This First)

Before touching any git command, check the actual state:

```bash
git status
git diff --stat HEAD
```

Also check which branch you're on and whether commits already exist:

```bash
git branch --show-current
git log --oneline develop..HEAD
```

Ask: does this changeset contain **exactly one primary task**?

**If yes** → proceed to Phase 2.

**If no** → stop and propose the split to the user before doing anything else:
> "This has [X] independent concerns. Recommend: PR1 (…), PR2 (…). Which do you want to start with?"

**Splitting rules** (from project policy):

| Situation | Action |
|-----------|--------|
| Pure refactor mixed with feature | Separate PRs |
| Schema/model change + feature code | Separate PRs (schema first) |
| Multiple new UI surfaces | One PR per surface |
| Feature flag + code that uses it | Same PR is OK |
| Import updates from a refactor | Same PR as the refactor |

**Red flag:** If you find yourself saying "I'll include the refactor since I was already in that file" — that's scope creep. Split it.

## Phase 2: Branch Setup

Always start from `develop`. Do not branch off the current working branch.

```bash
git fetch origin
git checkout develop
git pull origin develop
git checkout -b <type>/<short-description>
```

**Branch naming:**

| Type | Pattern | Example |
|------|---------|---------|
| New feature | `feat/<topic>` | `feat/user-export-csv` |
| Bug fix | `fix/<topic>` | `fix/login-redirect-loop` |
| Refactor | `refactor/<topic>` | `refactor/extract-auth-middleware` |
| Chore/tooling | `chore/<topic>` | `chore/upgrade-eslint` |

Lowercase, hyphens only, ≤ 40 chars.

## Phase 3: Commit

Stage specific files. Never `git add -A` without reviewing what's included.

```bash
git add <specific-files>
git commit -m "<type>(<scope>): <short summary>"
```

**Commit types:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

Commit messages must be in English. If the summary needs "and", split the commit.

## Phase 4: Create PR

```bash
git push -u origin <branch-name>

gh pr create \
  --title "<type>(<scope>): <short description>" \
  --base develop \
  --body "$(cat <<'EOF'
## What

[One sentence: what this PR does]

## Why

[Why this change is needed]

## How to Test

- [ ] [Step 1]
- [ ] [Step 2]

## Notes

[Trade-offs, follow-up PRs, caveats — omit if none]
EOF
)"
```

PR title < 70 chars. English. `--base develop` is mandatory — do not omit.

If this PR depends on another open PR (stacked), use **`nl-stack-pr`** instead.

## Common Mistakes

| Mistake | Correct Approach |
|---------|----------------|
| Skipping scope check, going straight to git | FoD check is Phase 1 — non-negotiable |
| Not checking current branch before branching | `git log --oneline develop..HEAD` first |
| Branching off current feature branch | Always `git checkout develop` first |
| `git add -A` | Stage specific files; check for secrets, generated files |
| Missing `--base develop` | Always explicit — default may point to wrong branch |
| "I'll include the refactor since I was already there" | That's scope creep. Separate PR. |
