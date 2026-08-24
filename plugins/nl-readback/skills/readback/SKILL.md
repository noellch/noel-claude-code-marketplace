---
name: readback
description: Use when a human needs to confirm that implemented code actually does what they expect and cannot personally read the whole diff — before PRing large agent-written changes, when the user says they can't confirm the mechanism matches expectations (無法確認機制是不是預期的、反向導讀), or when implementation, tests, and prior verification all came from the same agent lineage. Not for code quality review (code-review) or completion gating (verify).
---

# Clean-Room Readback

Confirm a mechanism matches human expectations by having **information-isolated readers narrate what the code actually does**, then letting the human compare the narrative against what they expected. Like an aviation readback: the system repeats back what it will do; the mismatch surfaces at the human, who is the only party that truly knows the intent.

**Why isolation is the whole trick:** a verifier who reads the spec first sees what the spec promises. Measured baseline: a spec-first verifier declared all six rows of a failure-mode table conformant when one row was divergent (spec said "retry + alert"; code had neither), blessed an unconfirmed UX decision because a spec row existed to anchor it, and missed a real bug (a validated field silently dropped before the task boundary) — while citing test names as coverage evidence. Clean-room readers with no spec caught the bug the same day.

## Iron Rules

1. **Readers never see the spec.** No plan, no handoff, no design docs, no *.md of any kind. Code and diff only. The orchestrator (you) HAS read the spec — that is exactly why you cannot be the reader.
2. **Comments, docstrings, commit messages, and test names are not evidence.** They encode the author's intent — the thing under audit. Only control flow counts.
3. **Every claim carries file:line** from the current tree.
4. **The human is the judge.** The deliverable is a comparable behavior narrative, never "conforms / safe to PR". If your summary contains a verdict where a narrative should be, delete the verdict.

## Process

1. **Slice the diff into event paths.** An event path is a user-visible trigger narrated end-to-end: "when a user saves X…", "when the periodic task runs…", "when step N fails…". Failure paths are paths. Group 1–3 related paths per reader by file locality.
   *Done when:* every hunk of the diff belongs to at least one path.
2. **Dispatch one fresh reader per group** using the reader prompt contract below. Readers run in parallel.
   *Done when:* every path has a numbered, file:line-anchored narrative plus the reader's own 疑點 (suspicions) section.
3. **Spot-check before presenting.** Personally read the cited lines for the highest-impact claims (minimum: every claim you will highlight in your summary). Subagent output is a lead, not a fact.
   *Done when:* every claim in your summary is marked ✅ (you read the lines) or ⚠ (reader-only).
4. **Comparison layer — only now open the spec.** Sort findings into four buckets: matches expectations / diverges from spec (quote BOTH the spec sentence and the code behavior with file:line) / new findings the spec never covered / known trade-offs confirmed. Present the buckets and the raw narratives; let the human read the narrative against their own expectations.
   *Done when:* the human can locate, for any bucket entry, the narrative step it came from.

## Reader prompt contract

Every reader prompt MUST contain all of:

- **Scope jail**: exact worktree/repo directory; read-only; no searching outside it.
- **Ground truth**: base commit + a scoped `git diff <base>..HEAD -- <files>` command so the reader can separate pre-existing behavior from this change — and must label steps 既有 vs 本次新增. If the working tree differs from HEAD, the reader states which one each claim describes (a live run surfaced uncommitted fixes stacked on the commits under audit).
- **Ban list**: no *.md / docs / plans; do not trust comments, docstrings, commit messages, or test names — verify against control flow.
- **Boundary tracing**: at every hand-off boundary (task kwargs, queue payload, serializer→service, outbound API call), enumerate what goes IN versus what was available — dropped values are where validated-but-unused bugs live.
- **Output contract**: numbered steps in execution order, file:line per step, written in the human's language, ending with a 疑點 section ("what strikes you as odd from code alone" — the reader has no spec, so suspicions, not violations).

## What this does NOT replace

Readback answers one question: *does the mechanism match the human's intent?* It does not prove reachability or robustness. Pair it with:
- **forward sweeps** — changed constructor/function signatures need an all-callsites check (a baseline forward pass caught a `scripts/` callsite the readers never opened);
- **running the tests** (verify / CI);
- **staging or end-to-end checks** for behavior that only the real platform exhibits.

## Rationalizations

| Excuse | Reality |
|---|---|
| "The spec IS the acceptance baseline — reading it first is efficient" | A spec-first verifier marked a divergent failure-mode row as conformant. Efficiency toward the wrong answer. |
| "Tests are green and test names cover the acceptance criteria" | Tests share the implementation's misunderstanding; a test name is a claim of intent, not evidence of behavior. |
| "I'll just give the user a pass/fail to save their time" | The user asked for confirmability, not a verdict. A verdict from the same lineage that wrote the code is the thing they don't trust. |
| "The diff is small, I'll read it myself — no need for isolated readers" | You read the spec; you are contaminated. Isolation is for the reader, and you are not one. |
| "The reader's narrative looks thorough, ship the summary" | Reader output is a lead. Spot-check the lines you highlight, or mark them ⚠ unverified. |
