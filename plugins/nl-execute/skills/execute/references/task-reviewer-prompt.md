# Task reviewer subagent — dispatch template

Fill and send as the reviewer's prompt. Two verdicts, both required. Do not pre-judge.

```
Review ONE task's implementation. Report two independent verdicts.

Inputs (all as files — read them):
- Brief (the requirements): <path/to/task-N-brief.md>
- Implementer report: <path/to/task-N-report.md>
- Diff (commit list + stat + full diff): <path/to/review-task-N.diff>

Global constraints (the binding requirements — your attention lens):
<copied verbatim from the plan: exact values, formats, stated relationships>

Report EXACTLY this:

## Spec compliance: ✅ / ❌
- Missing: requirements in the brief not implemented (quote the brief line)
- Extra: behaviour not asked for (scope creep)
- Wrong: implemented but doesn't match the brief

## Code quality: Approved / Changes needed
Findings by severity — Critical / Important / Minor. For each: file:line, the
problem, why it matters. Judge against the global constraints and general quality
(correctness, error handling, tests, clarity). Skip anything a linter/formatter/CI
already enforces.

## ⚠️ Cannot verify from diff
Requirements that live in unchanged code or span tasks — list them; do not guess.

Rules:
- Do not re-run tests the report already shows on this same code.
- Report what you find; do not soften or omit a finding because it seems minor to you.
```
```
