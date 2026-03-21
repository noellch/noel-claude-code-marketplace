---
name: code-review
description: Use when reviewing PRs, checking code quality, or when user says "review PR", "code review", "check my changes", "review my code"
---

# General-Purpose Code Review

## Overview

Structured code review with mandatory convention discovery, standardized output, and verified findings. Works across any repository by detecting tech stack and reading project-specific rules first.

## Pre-Review: Convention Discovery (MANDATORY)

**Before looking at ANY code, do these in order:**

1. **Read CLAUDE.md** — `cat CLAUDE.md` in the repo root. This defines what "correct" means for this project. Its rules override generic best practices.
2. **Detect tech stack** — `ls package.json tsconfig.json pyproject.toml go.mod Cargo.toml .eslintrc* biome.json 2>/dev/null`
3. **Check CI status** — `gh pr checks {N}` to see what automated checks already cover. Do NOT flag issues that linters/CI already enforce.
4. **Read PR description** — `gh pr view {N}` for intent and context. Note any claims to verify later.

**If you skip this step, your review is invalid.** The baseline failure mode is jumping straight into the diff and applying generic best practices that may contradict the project's actual conventions.

**No CLAUDE.md?** Still do steps 2-4. No CI? Note "CI: not configured" in the output header. No PR description? Note it and review the diff only. The absence of one input does not excuse skipping the entire discovery phase.

## Review Pass Order

### Pass 1: Structural (architecture, patterns)

- Does the change respect the project's layer boundaries?
- Is new code in the right file/module?
- Any new dependencies? Justified?
- For monorepos: does this change affect other services? Check cross-repo references.

### Pass 2: Correctness & Safety

Review in this priority order:

1. **Security** — injection, auth bypass, data exposure
2. **Correctness** — logic errors, race conditions, null handling
3. **Error handling** — silent failures, swallowed exceptions
4. **Performance** — N+1 queries, unbounded loops, missing pagination
5. **Tests** — are critical paths covered? do existing tests need updating?

### Pass 3: Verify Claims

**Do NOT trust PR descriptions at face value.** For any concrete claim (e.g., "aligns with Rubato's validation", "feature flag is fully rolled out"), cross-check:

```bash
# Search for what PR claims to match
grep -r "PATTERN" /path/to/other/repo

# Verify feature flag status if claimed "fully rolled out"
# Check the flag dashboard or search for remaining usages
grep -r "flag_name" . --include="*.py" --include="*.ts"
```

## Output Format (MANDATORY)

Use this exact structure. Do not invent your own.

```markdown
## Code Review: PR #{N} — {title}

**Scope:** {N files, +M/-K lines} | **Stack:** {auto-detected} | **CI:** {passing/failing/N checks}

### Blocking (must fix before merge)
- [ ] **[SEVERITY]** `file:line` — Description. Why it matters.

### Should Fix
- [ ] **[SEVERITY]** `file:line` — Description.

### Suggestions
- [ ] `file:line` — Description.

### Verified Good
- {Specific positive observations — at least one required}

### Verdict
**{Approve / Request Changes / Needs Discussion}** — {one-line rationale}
```

## Severity Definitions

Do NOT assign severity by gut feeling. Use these criteria:

| Severity | Criteria | Examples |
|----------|----------|---------|
| **SECURITY** | Exploitable vulnerability | Injection, auth bypass, data leak |
| **BUG** | Incorrect behavior in production | Logic error, race condition, data loss |
| **BREAKING** | Breaks existing consumers | API rename without migration, removed field |
| **PERF** | Measurable performance degradation | N+1 query, full table scan, unbounded loop |
| **TEST** | Missing coverage for critical path | No test for new error handling, untested edge case |
| **STYLE** | Violates project conventions (not generic opinions) | Only flag if CLAUDE.md or linter config defines the rule |

**Rule: Only flag STYLE issues if the project has a documented convention for it.** Generic "I prefer X" opinions are not review findings.

## What NOT to Review

- Generated files (lock files, migration files unless migration logic is the point)
- Files covered by automated formatters (if prettier/black/gofmt is in CI, don't flag formatting)
- Existing code that the PR didn't change (stay in scope)

## Rationalizations That Lead to Bad Reviews

| Excuse | Reality |
|--------|---------|
| "No CLAUDE.md, so I'll skip convention discovery" | Still check linter config, CI, tech stack markers |
| "Small PR, I don't need the full format" | Format is mandatory regardless of PR size |
| "Only one file changed, no need for cross-repo check" | One file in a monorepo can break other services |
| "I'll read conventions after scanning the diff" | Convention discovery FIRST. Order matters. |
| "The PR description explains everything" | Descriptions are claims. Verify them. |
| "This is obviously correct, no need for deep review" | The obvious PRs are where subtle bugs hide |

## Gotchas

| Baseline Failure | What to Do Instead |
|---------|------------------|
| Jump straight into diff without reading conventions | ALWAYS read CLAUDE.md and check CI first |
| Trust PR description claims without verification | Cross-check concrete claims with grep/code search |
| Invent your own output format each time | Use the mandatory format above exactly |
| Assign severity by intuition | Use the severity criteria table |
| Flag style issues based on personal preference | Only flag if project has a documented convention |
| Review only the diff hunks | Read full files for context around changes |
| Skip checking cross-repo impact in monorepos | Search other services for shared interfaces/constants |
| Produce review without running tests | At minimum, check if existing tests still pass conceptually |
