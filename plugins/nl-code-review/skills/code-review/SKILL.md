---
name: code-review
description: Use when reviewing PRs in any repo, when asked to check code quality, review changes, or when user says "review PR", "code review", "check my changes", "review my code"
---

# General-Purpose Code Review

## Overview

A repo-agnostic code review skill. Auto-detects the codebase's tech stack and conventions, then applies a structured multi-pass review. Works across any repository — no repo-specific configuration needed.

## When to Use

- User asks to review a PR or code changes
- User says "review", "check my code", "review PR #N"
- Before creating a PR (pre-flight check)
- After completing a feature (self-review)

## Review Flow

```
1. Detect Context    → Identify tech stack, conventions, CLAUDE.md rules
2. Gather Changes    → git diff, PR diff, or specified files
3. Structural Pass   → Architecture, patterns, layering violations
4. Detail Pass       → Bugs, security, edge cases, error handling
5. (Optional) Adversarial Pass → Devil's advocate challenge
6. Summary Report    → Categorized findings with severity
```

## Step 1: Detect Context

**Auto-detect the tech stack and project conventions before reviewing anything.**

```bash
# Check for project markers (run in parallel)
ls package.json tsconfig.json pyproject.toml setup.cfg go.mod Cargo.toml 2>/dev/null
cat CLAUDE.md 2>/dev/null | head -100
```

**Tech stack detection matrix:**

| Marker | Stack | Review Lens |
|--------|-------|-------------|
| `package.json` + `tsconfig.json` | TypeScript/React | Component patterns, type safety, hooks rules |
| `pyproject.toml` or `setup.cfg` | Python | PEP8, type hints, import order |
| `manage.py` + `settings.py` | Django/DRF | Layered architecture, N+1, migrations |
| `go.mod` | Go | Error handling, goroutine safety, interfaces |
| `Cargo.toml` | Rust | Ownership, lifetimes, unsafe blocks |

**Also check for:**
- `.eslintrc` / `biome.json` — linting rules already enforced
- `CLAUDE.md` — project-specific conventions (HIGHEST PRIORITY)
- `.github/CODEOWNERS` — ownership context

**IMPORTANT:** If a project CLAUDE.md exists, its rules override generic best practices. Read it first.

## Step 2: Gather Changes

**Determine what to review based on user intent:**

```bash
# Option A: Review unstaged changes
git diff

# Option B: Review staged changes
git diff --cached

# Option C: Review PR diff (against base branch)
git diff $(git merge-base HEAD main)...HEAD

# Option D: Review specific PR
gh pr diff {PR_NUMBER}

# Always: check which files changed
git diff --stat $(git merge-base HEAD main)...HEAD
```

**Scope the review:** If more than 20 files changed, ask the user which areas to focus on.

## Step 3: Structural Pass

**Review architecture and patterns FIRST, before line-level details.**

### Checklist

- [ ] **Layering violations** — Does the change respect the project's layer boundaries? (e.g., views calling repositories directly, components importing from wrong modules)
- [ ] **Responsibility** — Is new code in the right file/module? Would it be discoverable by another developer?
- [ ] **API surface** — Do new public interfaces (functions, types, endpoints) follow existing naming conventions?
- [ ] **Dependencies** — Any new dependencies? Are they justified? Check for existing alternatives in the codebase.
- [ ] **Test structure** — Are tests co-located or in the right test directory? Do they follow existing patterns?

### Red Flags

| Pattern | Why It's Bad |
|---------|-------------|
| Giant file (300+ new lines in one file) | Likely needs splitting |
| New utility/helper for one-time use | Premature abstraction |
| Circular imports | Architecture problem |
| Business logic in view/controller layer | Layering violation |
| Hard-coded values that vary by environment | Should be config |

## Step 4: Detail Pass

**Line-by-line review for correctness and safety.**

### Priority Order (review in this order)

1. **Security** — Injection, auth bypass, data exposure, OWASP top 10
2. **Correctness** — Logic errors, off-by-one, race conditions, null handling
3. **Error handling** — Silent failures, swallowed exceptions, missing rollbacks
4. **Performance** — N+1 queries, unbounded loops, missing pagination, large payloads
5. **Readability** — Naming, complexity, dead code, misleading comments

### Stack-Specific Checks

**TypeScript/React:**
- Unnecessary `any` types or type assertions
- Missing dependency arrays in hooks
- State mutations instead of immutable updates
- Missing error boundaries for async operations
- Barrel exports creating circular dependencies

**Django/DRF:**
- N+1 query patterns (missing `select_related`/`prefetch_related`)
- Missing database indexes for filtered/ordered fields
- Raw SQL without parameterization
- Missing permission classes on views
- Migrations that lock tables on large datasets

**Go:**
- Unchecked errors (`_` on error return)
- Goroutine leaks (missing context cancellation)
- Data races on shared state
- Deferred close on response bodies

## Step 5: Adversarial Pass (Optional)

**Activate when:** User asks for thorough review, or changes are high-risk (auth, payments, data migration, public API).

**How it works:** After the normal review, adopt a deliberately critical perspective:

1. **Assume the worst** — What if every external input is malicious?
2. **Challenge design decisions** — Is there a fundamentally simpler approach?
3. **Find the missing test** — What scenario would break this code that no test covers?
4. **Question necessity** — Does this change actually solve the stated problem? Could a smaller change work?

**Format adversarial findings separately:**

```
### Adversarial Review

> These are deliberately provocative challenges. Not all require action,
> but each deserves a moment of consideration.

- **Challenge:** [description]
  **Risk if ignored:** [concrete consequence]
  **Suggested action:** [specific recommendation]
```

## Step 6: Summary Report

**Present findings in a structured, actionable format.**

```markdown
## Code Review Summary

**Scope:** [N files, M lines changed]
**Tech Stack:** [auto-detected]
**Overall:** [Clean / Minor issues / Needs work / Blocking issues]

### Blocking (must fix before merge)
- [ ] **[SECURITY]** `path/file.py:42` — SQL injection via string interpolation
- [ ] **[BUG]** `path/file.ts:88` — Off-by-one in pagination logic

### Should Fix (strongly recommended)
- [ ] **[PERF]** `path/file.py:15` — N+1 query in loop, use select_related
- [ ] **[ERROR]** `path/file.ts:33` — Swallowed exception in catch block

### Suggestions (nice to have)
- [ ] **[STYLE]** `path/file.py:67` — Variable name `d` is unclear, consider `delivery_date`
- [ ] **[REFACTOR]** `path/file.ts:120-145` — Extract to a named function for readability

### What's Good
- [Positive observations — always include at least one]
```

**Severity definitions:**

| Level | Meaning | Action |
|-------|---------|--------|
| Blocking | Security vuln, data loss, crash, broken functionality | Must fix |
| Should Fix | Performance issue, poor error handling, maintainability debt | Fix before merge if possible |
| Suggestion | Style, naming, minor refactoring opportunities | Author's discretion |

## Gotchas

| Mistake | Correct Approach |
|---------|------------------|
| Reviewing without reading CLAUDE.md first | ALWAYS read project CLAUDE.md — it defines what "correct" means for this repo |
| Flagging style issues enforced by linter | Check if ESLint/Ruff/etc. already covers it — don't duplicate automated checks |
| Reviewing generated/vendored files | Skip `node_modules`, lock files, generated types, migration files (unless migration logic is the point) |
| Only pointing out problems | Always include "What's Good" section — positive feedback matters |
| Reviewing 50+ files without scoping | Ask user to prioritize — a focused review beats a shallow one |
| Applying React patterns to Django or vice versa | Let auto-detection guide your lens — don't cargo-cult across stacks |
| Suggesting refactors unrelated to the change | Stay in scope — review what changed, not the entire codebase |

## Quick Reference

| Action | Command |
|--------|---------|
| PR diff | `gh pr diff {N}` |
| Changed files list | `git diff --stat main...HEAD` |
| Specific file history | `git log --oneline -10 -- path/to/file` |
| Check CLAUDE.md | `cat CLAUDE.md` |
| Check project markers | `ls package.json tsconfig.json pyproject.toml go.mod 2>/dev/null` |
