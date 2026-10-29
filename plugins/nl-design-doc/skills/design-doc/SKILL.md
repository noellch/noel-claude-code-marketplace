---
name: design-doc
description: Use when the user asks for a 設計文件 / design doc (new or revised) for a feature or system change that reviewers will read on Outline, and research, a spec, or a plan already exists to draw from. Not for implementation plans, tickets, or handoffs.
---

# Design Doc

## Overview

A design doc records **decisions, not instructions**: what the user will see, which constraints forced the shape, which alternatives lost and why. Reviewers read it to push back on trade-offs; the implementation manual lives in plan.md. Two leading ideas:

- **House style** — copy the skeleton and voice of the team's existing docs, fetched live, never a generic template.
- **Mechanism, not module** — 設計 says how it works in words and diagrams; file paths, class names, SQL and checklists do not belong there.

## Steps

1. **Fetch the exemplars.** Load all three house-style docs from Outline with `mcp__plugin_cl-outline_outline__fetch` (`resource: document`): `pin-e8pymlXIsk`, `api-OYKIQrIvi8`, `mini-app-aYaaDakBiG`. A memory note or a recollection of the skeleton does not count — section order, separators and phrasing drift without the live text.
   *Done when:* all three documents are in this session's context and you can say which optional sections each one uses.
2. **Gather inputs.** Read the research / spec / plan / handoff the user points at; check the names you will lean on still exist in the repo. Separate measured numbers from inferred ones, and say which is which in the doc.
   *Done when:* you can state in one paragraph each: the outcome the user gets, today's process and its pain, the hard constraints.
3. **Decide what to decide.** List every open item. Each goes to exactly one place: a decision you make now (→ a 取捨 section opening with **選擇：**), or a fact only an external party holds (→ 未決問題 with 負責 and 何時要答案). Product-process choices — the UX entry shape, a name, whether to show a hint, which key namespace — are yours to make and write down; the doc teaches the process, it does not poll for it.
   *Done when:* 未決問題 has at most five rows and none is a choice the author could have made.
4. **Write the doc** in the section order of [`references/skeleton.md`](references/skeleton.md), in 繁體中文 unless asked otherwise, to `docs/plans/<topic>/YYYY-MM-DD-design.md` (or the repo's plan tree). Per-section criteria live in the skeleton; the ones agents skip most:
   - 一句話: the outcome the user gets plus one **bold** property — no table, class, API path or service-internal name.
   - 使用者會看到什麼 (or 前端會怎麼用／營運會怎麼用): one sequence diagram or mock, then the 前提 → 導致的設計 table.
   - 設計: one diagram per 條線, a lifecycle diagram, 「資料上只加…」 in words, one 失敗情境 flowchart with subgraph 情境 A／B／C. Zero file paths, module names, SQL, or 「實作時要注意」 lists.
   - 替代方案與取捨: one `###` per decision; **選擇：…** first; the alternative's best case; the cost; one bold closing sentence — the verdict, or 「**這個決定可以反悔。**」 when it is cheap to undo; a contrast flowchart (未採用 vs 採用, ❌／✅) for every decision a reviewer could push back on.
   - 未決問題 ≤ 5 rows; 想請 reviewer 特別看的地方 exactly three, each a bold claim plus one question.
   *Done when:* the skeleton's self-check table is all ✔ and the file is saved.
5. **Publish only on the user's go.** Show the local path and the self-check result; ask before creating or updating the Outline document. Outline rules: no H1 (title is a field), `---` between top-level sections (Goals and Non-Goals stay together), ```mermaid fences, `state "中文" as alias` in stateDiagram; same collection and parent as the exemplars unless told otherwise. Write the returned URL into the local file's metadata.
   *Done when:* the user has the Outline URL, or has said not to publish yet.

## Red flags — STOP

- Wrote any section before all three exemplars were fetched this session
- 設計 contains a path, a `.py`／`.tsx`／`.go` name, a SQL block, or an 「實作時要注意／不能省」 list
- A 取捨 section without **選擇：** or without a bold closing sentence
- 未決問題 has more than five rows, or a row that starts with 「要不要」／「用哪一種」
- `REQ-`, `#1234`, `PR1`, `Task 3`, 估點／工時, or a PR-splitting sentence anywhere in the body
- Created or updated the Outline document without the user's explicit go

## Rationalization table

| Excuse | Reality |
|---|---|
| "Memory already describes the skeleton, no need to fetch" | The run that skipped the fetch lost the `---` separators, merged Goals／Non-Goals and flattened 跨領域. The live docs are the only source of truth. |
| "Reviewers will want the file paths and the SQL" | They want to push back on decisions. Paths and SQL go to plan.md; the doc says what the mechanism does and why. |
| "I'm not sure, so I'll list it under 未決問題 for PM" | If you could decide it with what you have, decide it and write 選擇. 未決問題 is for facts only an external party holds. |
| "The research has REQ ids and 估點, I'll carry them into 背景資料" | Internal ids and sizing are planning-layer; they expire and leak process. Link the thread or file, drop the id. |
| "Four reviewer points is fine, they're all important" | Three. Keep the ones where a wrong call is costly; the rest already live in 取捨. |
| "These three choices are small, one 取捨 section for all of them" | One decision per section, however small — the exemplars give a two-line section to a field type. A merged section hides which one a reviewer is pushing back on. |

## Pairs with

- **nl-grill** before it: agree the problem and the approach; this skill turns the agreed spec into the review doc.
- **nl-domain-modeling**: glossary and ADRs; a 取捨 section may cite an ADR, not replace it.
- **plan.md / nl-plan-to-tickets** after it: tasks, PR order, tickets. The doc states technical dependency order only (實作切分), never PR codes.
- `write-design-docs` (generic Malte Ubl guidance) and `doc-coauthoring` answer the same request with a generic template; for house-style docs this skill supersedes them.
