---
name: create-pr
description: Use when the user asks to open, push, or submit a pull request for finished work — "create PR", "open PR", "發 PR", "開 PR", "提 PR", "push and PR", "submit for review". Pushes a branch and opens a PR in the user's name, so it never fires on its own when a task ends. Stacked PRs (base is another PR) → nl-stack-pr.
---

# Create PR

Delivers completed work as one focused PR. **FoD** (Feature on Demand) means one primary task per PR, sized for a single review sitting; the scope check is a hard gate because a PR that fails it is too large to review well.

## Phase 0: Read the Repo's Rules

Before any git command, learn how *this* repo delivers. Repo policy overrides every default in this skill.

```bash
git fetch origin
cat CLAUDE.md 2>/dev/null                                                       # read it whole: base, naming, language, test command, PR rules
gh repo view --json defaultBranchRef -q .defaultBranchRef.name                  # falls back below when gh has no access
git symbolic-ref -q --short refs/remotes/origin/HEAD | cut -d/ -f2-
git show HEAD:.github/pull_request_template.md 2>/dev/null \
  || git show HEAD:.github/PULL_REQUEST_TEMPLATE.md 2>/dev/null \
  || git show HEAD:PULL_REQUEST_TEMPLATE.md 2>/dev/null
```

- `BASE` = the branch CLAUDE.md names → else the default branch from `gh` → else `origin/HEAD` → else ask. Never assume `develop`; Rubato uses it, other repos use `main`.
- A PR template that exists is the body's shape (Phase 4). `gh pr create --body` replaces the template silently, so the text you pass must already be the filled template.
- Note the repo's test command and PR language (CLAUDE.md, or the language of the last few merged PRs: `gh pr list --state merged --limit 5 --json title,body`).

## Phase 1: FoD Scope Check (Hard Gate)

```bash
git branch --show-current                       # empty → detached HEAD → stop
git status --short                              # uncommitted and untracked work
git log --oneline origin/$BASE..HEAD            # commits already on this branch
git diff --stat origin/$BASE...HEAD             # what those commits touch
```

Ask: does this changeset contain **exactly one primary task**?

**If yes** → Phase 2. **If no** → stop and propose the split before doing anything else:
> "This has [X] independent concerns. Recommend: PR1 (…), PR2 (…). Which do you want to start with?"

Portable splitting defaults, used only when the repo documents nothing:

| Situation | Action |
|-----------|--------|
| Pure refactor mixed with feature | Separate PRs |
| Schema/model change + feature code | Separate PRs (schema first) |
| Multiple new UI surfaces | One PR per surface |
| Feature flag + code that uses it | Same PR is OK |
| Import updates from a refactor | Same PR as the refactor |

**Red flag:** "I'll include the refactor since I was already in that file" — that is scope creep. Split it.

## Phase 2: Branch — Decide, Never Reset

The work usually already sits on a branch. Pick the row that matches; do not `git checkout $BASE` while holding uncommitted or unpushed work — that is how commits get left behind.

| State (from Phase 1) | Action |
|----------------------|--------|
| On a feature branch, commits ahead of `origin/$BASE`, name fits the pattern | Keep it. This is the PR branch |
| On a feature branch, name does not fit | `git branch -m <type>/<topic>` if never pushed; otherwise keep the name and move on |
| On `$BASE` with uncommitted work | `git checkout -b <type>/<topic>` right here — the changes come along |
| On `$BASE` with nothing uncommitted and nothing ahead | Nothing to deliver; say so |
| Feature branch is behind `origin/$BASE` | Say so with the count; rebase vs merge is the user's call unless CLAUDE.md decides |
| Detached HEAD | Stop; ask which branch the work belongs to |

**Branch naming** (unless the repo prescribes ticket prefixes or another scheme):

| Type | Pattern | Example |
|------|---------|---------|
| New feature | `feat/<topic>` | `feat/user-export-csv` |
| Bug fix | `fix/<topic>` | `fix/login-redirect-loop` |
| Refactor | `refactor/<topic>` | `refactor/extract-auth-middleware` |
| Chore/tooling | `chore/<topic>` | `chore/upgrade-eslint` |

Lowercase, hyphens only, ≤ 40 chars.

## Phase 3: Commit and Verify

Only when Phase 1 showed uncommitted work. Stage by path, then read the stage before committing:

```bash
git add <specific-files>
git diff --cached --name-only        # no .env*, keys, credentials, dumps, or generated/lock files this PR did not mean to change
git commit -m "<type>(<scope>): <short summary>"
```

Match the repo's commit style (`git log --format=%s -15 origin/$BASE` shows it); the default is conventional commits in English with types `feat`, `fix`, `refactor`, `test`, `chore`, `docs`. A summary that needs "and" is two commits.

**Verify before anything leaves the machine.** Run the repo's test command (CLAUDE.md, CI config, or nl-verify's evidence if that skill already ran). The result goes into the PR body as a line the reviewer can trust: `Tests: <command> → <result>`, or `Tests: not run (<reason>)`. A docs-only change still carries the line. Right under it, one `Not verified: <behaviour> (<why>)` line per behaviour the diff adds that nothing you ran exercised (nl-verify's lines go in verbatim when it ran). A checkbox is a to-do for someone; it does not tell the reviewer what you did not exercise.

## Phase 4: Push and Open

```bash
gh pr list --head "$(git branch --show-current)" --json number,url --jq '.[0].url'   # non-empty → PR exists
```

A PR already exists → `git push`, update its body with `gh pr edit {N} --body-file body.md` only if the user asked, print the URL, stop.

```bash
git push -u origin "$(git branch --show-current)"      # rejected → stop and report; never --force
gh pr create --base "$BASE" --title "<type>(<scope>): <short description>" --body-file body.md [--draft]
```

- Title < 70 chars, English unless the repo says otherwise.
- `body.md` is the repo's PR template filled in, in the repo's PR language; with no template, use the default below. No `[placeholder]` or `<!-- -->` hint may survive into the posted body; an unknown section (an Asana link you do not have) is written as "待補：…" rather than left as the template's comment.
- `--draft` when the repo has a test command and you did not run it, or the user called it WIP. A repo with no test command gets a normal PR; the `Tests:` line already says so.
- Print the PR URL. Then hand off: CI watching → `babysit-pr`; attach to the Asana task → `cl-asana-pr`.

Default body when the repo has no template:

```markdown
## What
[One sentence: what this PR does]

## Why
[Why this change is needed]

## How to Test
Tests: <command> → <result>
Not verified: <behaviour> (<why>) — omit when nothing is unverified
- [ ] [Manual step, if any]

## Notes
[Trade-offs, follow-up PRs, caveats — omit if none]
```

## Failure Modes

| Excuse | Reality |
|--------|---------|
| "I'll include the refactor since I was already there" | Scope creep. Separate PR |
| "The base is `develop`, it always is" | Phase 0 resolves it per repo; `develop..HEAD` on a `main` repo fails before any work starts |
| "Checkout the base and cut a fresh branch, that's cleaner" | The commits stay on the old branch and the PR is empty. Phase 2 keeps the branch that holds the work |
| "The built-in body template is fine" | `--body` silently discards the repo's template; fill theirs when it exists |
| "Docs-only, no need to mention tests" | The `Tests:` line is how the reviewer knows what was and was not run |
