---
name: release-watch
description: Use when a PR has just merged or a release/deploy completed and the session is about to conclude — confirms the release is actually healthy before signing off. Triggers on "merged", "deployed", "上線了", "release 完成", "merge 了就收工", "post-merge check", or when babysit-pr reports a merge finished.
---

# Release Watch

Post-merge triage is a **15-minute time-boxed checklist ending in a written verdict** — not an open-ended investigation, and not a "CI is green, bye" reflex. Root rule: **silence is not health**. A monitor showing zero errors proves nothing until the monitor itself proves alive.

## The contract

You are done ONLY when the verdict block (template below) is written and every line carries evidence (command output, URL, observed behaviour) or the explicit marker `CANNOT VERIFY`. Running out of time does not skip the verdict — it makes the verdict `UNVERIFIED` with a handoff note. Leaving silently is the only forbidden move.

## Steps — fixed order, each time-boxed

1. **Locate the blast radius (≤3 min).** Which branch did the change land on, and has it reached production yet? Trace the repo's real pipeline from `.github/workflows/` and verify with `gh pr view` / `gh run list` — do not assume "merged = staging only". (Example: Grazioso auto-deploys `develop`→staging and opens a release PR `develop`→`master`; if that release PR already merged, you are watching production, not staging.)
2. **CI + deploy runs (≤2 min).** `gh pr view <n> --json statusCheckRollup`, `gh run list --branch <deploy-branch>`. Green CI answers "the code passes its tests", never "the feature works in the real environment" — CI mocks the backend.
3. **Heartbeat before signal (≤3 min).** Before reading any error count: confirm the error monitor is receiving events at all — any project, org-wide, last 24h. A dead Sentry shows zero errors for broken code too. Monitor dead → open/flag a ticket for it, and cap your best possible verdict at `CI-GREEN-ONLY`.
4. **Release-scoped error scan (≤3 min).** Only now read new issues: `firstSeen` within 24h, filtered to the project (and release tag if available). A new issue matching the change → verdict `BROKEN`, escalate immediately, skip step 5.
5. **Exercise the change once, yourself (≤5 min).** Drive the real feature in the deployed environment — browser tool for UI, `curl` for a new endpoint. Recommending that someone else click through is not verification; you have the tools. Only after a failed attempt may you write `CANNOT VERIFY` with the reason.
6. **Verdict + handoff.** Fill the template. Anything `UNVERIFIED`, `CI-GREEN-ONLY`, or `BROKEN` makes the handoff line mandatory: name who must know what before you stop.

## Verdict template

```
Release: <PR/release id> → <environment it actually reached>
CI/deploy: <evidence>
Monitor heartbeat: ALIVE | DEAD — <evidence>
New errors: <evidence or CANNOT VERIFY>
Feature exercised: <what you did + observed result, or CANNOT VERIFY + attempt made>
Verdict: HEALTHY | CI-GREEN-ONLY | UNVERIFIED | BROKEN
Handoff: <who needs to know what — or "none needed (HEALTHY)">
```

## Rationalization table

| Excuse | Reality |
|---|---|
| "CI is green, so the release is fine" | CI proves the code, not the deployed behaviour. Steps 3–5 cover the gap CI cannot. |
| "No new Sentry errors — healthy" | A dead monitor also reports zero. Heartbeat first; zero only counts when the monitor is alive. |
| "PM said wrap up / this pipeline is always stable" | Fine — then the checklist takes 15 minutes and ends in HEALTHY with evidence. Authority and history are not evidence about *this* release. |
| "No time, I'll check next week" | Timebox exhausted = verdict UNVERIFIED + handoff note. That takes 2 minutes. Silence hands the pager to nobody. |
| "I'll suggest the user click through the flow" | Recommending is not exercising. Attempt it with your own tools; only a failed attempt earns CANNOT VERIFY. |

## Boundaries

- Watching CI **before** merge, retries, auto-merge → `babysit-pr`.
- A confirmed break needing diagnosis → `nl-debug` (build the reproduction loop there).
- Deploy mechanics, rollbacks, infra changes → out of scope; follow team runbooks and escalate to the owning team.
