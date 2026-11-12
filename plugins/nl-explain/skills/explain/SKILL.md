---
name: explain
description: Use when the user says they don't understand an agent's output or asks for it plainer — 簡單說, 簡單講, 看不懂, 還是看不懂, 白話, 講人話, 什麼意思, 說到我理解, explain simply, ELI5 — whether the output is your own earlier message, a subagent report, or a tool result.
---

# Explain

The text the user didn't understand was written under the **curse of knowledge**: every term felt shared because the writer had just used it. Shortening keeps the curse; padding buries it. Rebuild from the reader's side, then cut.

**Done = teach-back.** Without the original, the reader can (1) restate the conclusion, (2) say why — and how that differs from what they assumed, (3) tell measured from inferred, (4) say what they do or decide next.

**Reader.** Unless you know better: a frontend engineer — React, TanStack Query, git, PRs are home turf; backend / infra / databases / networking / crypto are not. Reply in the user's language **and script**: Traditional Chinese stays Traditional (繁體), never Simplified.

## Steps

1. **Find the question.** What did the user originally want to know or decide? Your first sentence answers it — no opener (「簡單說：」「換個講法」), no apology.
2. **Pick the shape.** Two kinds of message, two shapes. Status shape only when the reader already knows what the thing *is* (their own PRs, their own feature); if they don't — someone else's PR, an unfamiliar service — open with 1–2 sentences placing it (where it sits in the flow, what it's for) before the status, and use the mechanism ceiling.
   - **Status / decision** (where things stand, what to choose): a decision skeleton — what happened → where it stands now → cost of leaving it → the choice, each option with its consequence. **Ceiling: 200 characters** — about 6 short lines. Don't re-explain things the reader owns (their own PR stack, their own feature). The rewrite the user accepted for a 5-layer stacked-PR status:
     > rebase 我跑了，前四層成功，第五層卡住，我問你怎麼辦，你選「還原，只推修正」。所以現在沒有 rebase。
     > 代價：五支 PR 之間有舊的內容落差，merge 前得處理，不然可能洗掉修正。
     > 好處：reviewer 的 22 條意見還釘在原位，我能正常回覆。
     > 現在做也行，晚點做也行。要我做嗎？
   - **Mechanism / cause** (why a bug, incident or result happened): mental model → what happened as a numbered timeline or one concrete walk-through → why (1–2 causes, "not X but Y", "why only sometimes") → what to do. **Ceiling: 800 characters.** A ceiling, not a target — the accepted rewrites ran 320–780.
3. **Term inventory.** List every term, code, ID, flag, path, command and number you're about to use. For each:
   - **drop** — task codes (T10, R1, D1), PR numbers, SHAs, branch / file / worktree paths, channel IDs, counts — unless the reader needs it to act;
   - **translate** into everyday words;
   - **define once**, with a frontend analogy if one fits (see *Analogies*).

   Then inventory the words inside your definitions. Done when no term is left that the reader wasn't given.
4. **Model before finding** (mechanism shape). Before any finding, 1–2 sentences on what the things involved *are* and how they normally relate — e.g. "Django keeps two descriptions of each table: the model code, and migration scripts that actually change the database; the check asks whether they match." "They don't match" is noise until the reader knows the two sides.
5. **Certainty inline, once.** Tag each claim where it appears — 「（實測）」「（推測，未查）」 — instead of restating every fact in a separate certainty section. Never fold an inference into a confident sentence. Keep the original's confidence: don't upgrade 「候選」 to 「最可能」, don't add reassurance it never gave (「大多無害」「不管哪邊先上都不會壞」), and keep the one piece of evidence that makes the conclusion believable (the 21-second timeout, "all 869 ran"). Add nothing the original doesn't support; if you infer something to make it readable, tag it （推測）.
6. **Cut.** Each fact appears once. Prose or short lists; at most 2–3 bold lead-ins, no fixed section template. Drop a detail rather than paraphrase it loosely — compression must not change which items, counts or states the original reported. Drop side findings that don't bear on the user's question (an unrelated flaky worker, an auth hiccup in the tooling). **Never cut a state line the reader acts on** — where their pending item stands ("the PR is pushed; I'll mark it ready when CI is green"), what is still unowned ("nobody has picked up the backend part"). In past cases the user's very next reply acted on exactly that line. Detail stays in the original; offer it in one line.
7. **Teach-back check.** Answer the four questions from your draft alone; fix any you can't. If the subject isn't the reader's own, also answer "what is this thing for, and where does it sit?" — a 230-character rewrite that skipped it lost to an unstructured 670-character one. Scan for untranslated jargon and Simplified characters.
8. **Length gate.** You cannot count CJK characters by eye — drafts that felt short measured 1.6–3.8× the accepted length. Write the draft to a temp file and run `python3 <this skill's base directory>/scripts/count.py status|mechanism <file>`. `OVER` → cut and rerun; act on every `leftover` line. Send only a draft that printed `OK`, and send it exactly as gated.

## Second round: 「還是看不懂」

Your last explanation failed. Shortening it again (same terms, fewer words) fails again; so does a longer version of the same thing. **Change representation**: a mental model, a timeline, a concrete example (one real row, one real user), or an analogy you haven't used. If the user named the part, rebuild only that part. If not, send the new version, then ask in one line which part lost them.

## Analogies

Map structure, not surface: the relationship must hold (ordering, who calls whom, who owns the state). Prefer the reader's world — a `fetch` stuck at *Initial connection* in DevTools, a TanStack Query cache entry, a feature branch behind `develop`, `package.json` vs lockfile — over generic metaphors. If acting on the analogy would mislead, say in one clause where it breaks.

## Red flags

| Thought | Reality |
|---|---|
| "They read the original, so T10 / #1234 / R1 are known" | Those codes are why it failed. Drop or translate. |
| "Keep the terms, shorten the sentences" | Observed result: 「什麼啊？我還是看不懂」. |
| "Explain everything from the top so it's complete" | A 50-line from-the-top rewrite got 「簡單講」 again within seconds; the accepted one was 6 lines. |
| "Every reply gets conclusion / background / timeline / why / certainty / action" | That template is the report format that failed. Use the shape for this message; most accepted rewrites had ≤ 3 lead-ins. |
| "Everyone knows CI / migration / IPv6" — or "前端" means the Google edge | The reader decides. To a frontend engineer 「前端」 is the browser. |
| "Found a mismatch / drift / race" — between what? | Model first: name the two sides before the gap. |

Evidence behind these rules (for editing this skill, not for running it): [REFERENCE.md](REFERENCE.md).
