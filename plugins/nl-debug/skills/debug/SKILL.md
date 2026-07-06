---
name: debug
description: Use for a hard bug — intermittent or flaky, a performance regression, or one where you already tried a fix and it didn't hold — and whenever you're tempted to patch a symptom under time pressure.
---

# Debug

Extends `superpowers:systematic-debugging` — its rules still apply (root-cause before fix, one change at a time, question the architecture after 3 failed fixes, use its `root-cause-tracing` for deep stacks). This skill sharpens the one thing hard bugs live or die on: **the feedback loop.**

## The one law

```
NO HYPOTHESIS UNTIL A RED-CAPABLE LOOP EXISTS
```

The feedback loop **is** the skill. With a tight signal that goes red on *this* bug, you'll find the cause — bisection, hypotheses, instrumentation all just consume it. Theorising about causes before that loop exists is the exact failure this prevents. (Naming a suspect "while we set up a repro" counts as theorising.)

## Phase 1 — Build the loop (spend disproportionate effort here)

Construct a signal that catches THIS bug. Roughly in order: failing test → curl/HTTP script → CLI + fixture diff → headless-browser script → replay a captured trace → throwaway harness → property/fuzz loop → bisection → differential run → HITL script (last resort).

- **Intermittent?** Don't chase a clean repro — *raise the reproduction rate*: loop 100×, parallelise, add stress, inject sleeps, throttle the network. 50% is debuggable; 1% isn't.
- **Multi-component?** Log data in + out at each boundary once, to find WHICH layer breaks before you suspect one.

*Done when* you can name ONE command you have **already run** that is: **red-capable** (asserts the user's exact symptom, not "didn't crash"), **deterministic**, **fast** (seconds), **agent-runnable**. Paste the command and its red output.

## Phase 2 — Reproduce + minimise

Run it red. Confirm it's the *user's* symptom, not a nearby one. Then shrink to the smallest scenario still red — cut inputs, config, steps one at a time. The minimal repro shrinks the suspect space **and** becomes the regression test.

## Phase 3 — Hypothesise (3–5, ranked, falsifiable)

Generate 3–5 ranked hypotheses **before testing any** — a single hypothesis anchors on the first plausible idea. Each states a prediction: "if X is the cause, changing Y makes it disappear." Show the list to the user (they often re-rank instantly). Then test **one at a time, one variable per probe**. Tag debug logs `[DEBUG-xxxx]` so cleanup is one grep.

## Phase 4 — Fix + regression test

Write the failing test **before** the fix — *if* a correct seam exists (one that exercises the real bug pattern at the call site). If no correct seam exists, **that is the finding**: the architecture is preventing lock-down — note it. Otherwise: fail → fix → pass → re-run the original (un-minimised) loop.

## Phase 5 — Close out

- Original repro no longer reproduces (re-run the loop)
- Regression test passes (or the absent seam is documented)
- All `[DEBUG-...]` logs removed (grep), throwaway harnesses deleted
- The hypothesis that was correct goes in the commit/PR message
- Ask "what would have prevented this?" — if the answer is architectural, hand off to a refactor pass (make the call *after* the fix, not before)

## Under pressure — the trap

A demo band-aid (optimistic UI insert, a retry, a sleep) is **not** the fix. If a deadline forces you to ship one, label it a stopgap — the loop still owes you a root cause. "30 minutes" is exactly when guessing feels right and costs the most.

## Red flags — STOP

- Naming a suspect cause before a red-capable loop exists
- "I reproduced it by hand" — manual ≠ an automated red-capable loop
- Shipping a stopgap and calling the bug fixed
- One hypothesis, tested by changing several things at once
- Fixing without leaving a regression test (when a seam exists)

## Rationalization table

| Excuse | Reality |
|---|---|
| "It's intermittent, I can't get a clean repro" | You don't need clean — raise the rate (loop, stress, throttle) until it's debuggable. |
| "I'll reproduce by hand with throttling for now" | Manual repro doesn't gate hypotheses or become a regression test. Automate the loop. |
| "30 min to demo — just make the symptom go away" | A stopgap is not a fix. Ship it labelled, but the root cause is still owed. |
| "I can see it's probably the cache/race" | Seeing a symptom pattern ≠ evidence. No red loop, no hypothesis. |
