---
name: bye
description: Sweep the session for risks you would otherwise walk away from — four fixed lanes, evidence on every lane, ending in an explicit verdict. Type /nl-bye before closing a session.
disable-model-invocation: true
---

# Bye

`bye` is a **verdict, not a farewell**. Root rule: **"found nothing" and "didn't look" produce the same sentence** — only the four evidence lines tell them apart.

The sweep is fixed-length; the report is variable-length. A rushed session gets a *shorter report*, never *fewer lanes*.

## The contract

You are done ONLY when the verdict block is written with **all four lanes present**, each carrying either evidence or the explicit marker `NOT CHECKED — <reason>`. An empty lane line is not "clean"; it is an unfinished sweep.

**Evidence** means output you can point at: a command you ran just now, or one whose output appeared in this session and that you can quote. An assertion backed by neither is a lane 4 finding about yourself, not evidence.

A lane can be **mixed** — some sub-checks with evidence, others `NOT CHECKED`. Write both on the line. Verdict precedence, in order:

1. any finding anywhere → `RISKS FOUND` (still name the gaps)
2. no finding, but any `NOT CHECKED` → `UNVERIFIED`
3. all four `無`, nothing skipped → `CLEAR`

`CLEAR` is never available while a `NOT CHECKED` stands.

## Steps

1. **Collect before judging.** Run the checks; do not report checks you *would* run. Minimum, from the repo root:
   ```
   git status --short && git status -sb | head -1
   git stash list
   git branch -vv | grep '^\*'
   gh pr list --head "$(git branch --show-current)"
   git worktree list
   ```
   *Done when:* you have real output for each, or a stated reason one was unavailable.

2. **Lane 1 — Uncommitted / unpushed.** Working tree changes, stashes, commits ahead of upstream, a branch with no PR, stray worktrees. Unshipped is not safe: uncommitted work is the most losable thing on the machine.
   *Done when:* one line, naming the actual files/counts or `無`.

3. **Lane 2 — Outside footprint.** Every action this session that exists **outside this machine**: writes to prod/staging (DB, BigQuery, feature flags, secrets), deploys, tickets created or assigned, messages sent, emails, external API calls with side effects. Frame it as a footprint, not a correctness question — a ticket assigned on a guess means a real person got a real notification.
   *Done when:* one line listing each outward action with its target and whether it is reversible, or `無`.

4. **Lane 3 — Broken or half-done.** Failing or never-run tests, placeholder values behind a TODO, debug logging, commented-out code, type errors, a PR opened against the wrong base. Check the diff you actually produced, not the whole repo.
   *Done when:* one line per item, each pinned to the most specific locator you can actually produce — `file:line` if the file is reachable, otherwise the message or command in this session that shows it, marked as unpinned.

5. **Lane 4 — Unstated calls. Re-read the session, not the repo.** This lane has no grep. Scroll the conversation for: decisions you made on the user's behalf, claims you made without running anything ("CI should pass", "that looks right"), verifications you skipped, assumptions you never surfaced. If you asserted something this session and never ran the command behind it, either run it now or list it here.
   *Done when:* one line per unstated call, or `無` — and you have re-read the session to say so.

6. **Verdict.** Fill the template. Do not act on findings unless asked; this skill reports.

## Verdict template

```
Uncommitted / unpushed : <evidence or 無>
Outside footprint      : <evidence or 無>
Broken / half-done     : <evidence or 無>
Unstated calls         : <evidence or 無>

Verdict: CLEAR — 沒發現風險，可以安全離開
       | RISKS FOUND (<n>) — 每項一句「怎麼收」
       | UNVERIFIED — <哪條 lane 沒查成、為什麼>
```

A lane line may read `<evidence> + NOT CHECKED — <what and why>`.

## Rationalization table

| Excuse | Reality |
|---|---|
| 「很晚了，快速掃一下就好」 | A short sweep is a shorter report, never fewer lanes. All four run. |
| 「抓到一個高信心的根因型風險，次要的就不再深究」 | The first finding is not a stop signal. Lane 3 being loud says nothing about lane 2. |
| 「還沒 push、沒開 PR，就算有問題也不會擋到任何人」 | Unshipped ≠ safe. Uncommitted work dies with the machine; lane 1 exists for exactly this. |
| 「這些我會建議他去跑」 | A list of commands you would run is not a check. You have the tools. Run them. A check that is genuinely unavailable is `NOT CHECKED` with the reason — never a recommendation handed back to the user. |
| 「tech lead 早上說這個改動很單純」 | Someone else's confidence is not evidence. They did not watch this session. |
| 「CI 全綠了，應該沒事」 | Green reports on what ran. Check what *didn't* — a suite that never triggered reports green by being absent. |
| 「使用者說收工，不是要我重做一輪 code review」 | Correct — this is not code review. It is four lanes over facts you already have. That is why it is cheap. |
| 「沒發現什麼問題，應該可以走了」 | "Found nothing" and "didn't look" read identically. Show the four lines. |
| 「lane 4 我大概記得沒什麼」 | Memory of a session is the least reliable thing in it. Re-read it. |

## Red flags — STOP

- Reported commands you *would* run instead of their output
- Any lane line empty, missing, or merged into another
- Wrote `CLEAR` while a lane says `NOT CHECKED`
- Stopped sweeping after the first serious finding
- Answered lane 4 from memory instead of re-reading the session
- Skipped a lane because "this session was simple"

## Boundaries

- **You cannot close the session.** The output ends at 「可以安全離開」; exiting is the user's action.
- **Report only.** Do not commit, push, open PRs, or fix findings unless the user asks after seeing the verdict.
- Adjacent skills — point, don't duplicate: unfinished work that another agent must resume → `/nl-handoff`. A merge or deploy landed this session → `/nl-release-watch`. Claiming one task complete → that is verification-before-completion, a different moment.
