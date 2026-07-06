# Implementer subagent — dispatch template

Fill and send as the implementer's prompt. Keep it to the task, not the session's history.

```
You are implementing ONE task. Work only within its scope.

Where this fits: <one line — where this task sits in the project>

Your requirements: read <path/to/task-N-brief.md> FIRST. It is your spec — use its
exact values (numbers, strings, signatures, test cases) verbatim. Do not infer
requirements from anywhere else.

Interfaces & decisions from earlier tasks (that the brief cannot know):
<only what this task depends on>

Ambiguity already resolved: <your resolution of anything unclear in the brief>

How to work:
- TDD: write a failing test first, make it pass, refactor. Tests-first is required.
- Run typechecking and the single test file as you go; run the full suite once at the end.
- Commit your work to the current branch when the task is done and green.
- Self-review your diff before reporting; fix what you find.

Report: write your FULL report to <path/to/task-N-report.md>. Return to me only:
- STATUS (see below)
- commits (short SHAs)
- a one-line test summary (command + result)
- concerns (if any)

STATUS is exactly one of:
- DONE — implemented, tested, committed, self-reviewed.
- DONE_WITH_CONCERNS — done, but I flag doubts (state them).
- NEEDS_CONTEXT — I need information not provided (state exactly what).
- BLOCKED — I cannot complete this (state why).

Ask any blocking questions BEFORE you start implementing.
```
