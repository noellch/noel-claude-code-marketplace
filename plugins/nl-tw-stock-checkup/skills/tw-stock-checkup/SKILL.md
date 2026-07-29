---
name: tw-stock-checkup
description: Use when the user asks about a specific named Taiwan stock — whether it is worth buying, how healthy it is (體質), or what to do with a position they hold — triggers on "這檔可以買嗎", "值得進場嗎", "體質分析", "我持有…成本…", "停利", "停損", "加碼", "攤平". For whole-market "what can I enter today" questions, use tw-stock-entry instead.
---

# TW Stock Checkup

## Overview

Single-stock health check and position decisions for TWSE stocks. Two branches share one checkup card; only the final question differs.

**Baseline failure modes this skill kills**: fabricating portfolio context the user never stated, deciding hold/sell without ever asking why the user holds the stock, punting verifiable facts back to the user（「請自行確認」）, and burying "not backtested" caveats in an appendix away from the price levels they qualify.

## Non-negotiables

- **Sunk cost**: the user's cost basis sets P&L, never the verdict. The only decision question is: knowing what you know today, would you hold/buy this stock at today's price?
- **Thesis first (Branch B)**: before any hold/sell verdict, establish why they hold it and the intended timeframe. Not stated → ask. Cannot ask → give conditional verdicts per thesis（「若為題材短線…／若為基本面長線…」）, never one unconditional answer.
- **BUY is gated**: any verdict that means new buying — fresh entry or 加碼 — is capped by the tw-stock-entry market gate. Run that skill's market-context gate check first; on gate fail the ceiling is 觀望 (Branch A) or 續抱 (Branch B), regardless of how good the stock looks. The gate is OR-logic: once any condition triggers, it has failed — skip the remaining conditions (the full-market Layer 1 screen is expensive and cannot un-fail a triggered gate).
- **No fabricated context**: portfolio-level statements (concentration, sizing, "your real risk is…") only from facts the user stated. Unknowns go in the output as questions, not as assumptions dressed up as insights.
- **Verify or say you couldn't**: dividend dates, punish/notice status, financials all have endpoints (references).「請自行確認」is allowed only after your own attempt failed — and then state what you tried.

## Execution Flow (MANDATORY order)

1. **Classify** — Branch A (not holding → entry question) or Branch B (holding with cost/size → manage question). Branch B: establish thesis + timeframe per the non-negotiable before proceeding.
2. **Checkup card** — all four panels, in this order; a panel with no obtainable data says so explicitly instead of silently shrinking:
   - **基本面**: monthly revenue trend (YoY and MoM, last 3 months), latest quarterly EPS, margin trajectory
   - **估值**: today's official PER/PBR/yield vs the stock's own history — not a hand-picked peer average. If the user cites a peer comparison, verify its basis or reject it explicitly.
   - **籌碼**: institutional flows (T86, ≥5 days summed), margin-balance trend (MI_MARGN), float structure (capital size, major-holder %) where findable
   - **技術面**: 1y daily history, MA alignment, RSI/KD/MACD, volume pattern, distance from 52w high/low
3. **Event risk** — ex-dividend proximity (TWT48U calendar), next monthly-revenue and earnings dates, punish/注意 status. Verified via endpoints, never quoted from news headlines.
4. **Verdict** — fixed vocabulary, each tied to the card and (Branch B) the thesis, with an explicit invalidation condition ("what would change this call"):
   - Branch A: 進場條件成立 / 觀望
   - Branch B per position: 續抱 / 部分停利 / 全部停利 / 停損出場 / 加碼 (gate-pass only)
5. **Report** — conclusion first. Label every number: 量過的 (fetched/computed this run, date stated) vs 推論的 (inferred or quoted). Price levels (stops, targets) carry their basis inline where they appear（e.g.「60 日線位置，技術參考位，非回測參數」）— not in an appendix. End with a non-advice disclaimer (非投資建議).

## Completion criteria

Done only when ALL hold:
- Branch identified; Branch B has a stated thesis or conditional verdicts per thesis
- All four card panels present, or explicit N/A with the reason
- Event-risk section verified via endpoints
- Verdict uses the fixed vocabulary and names its invalidation condition
- Measured-vs-inferred labeling throughout; disclaimer at the end

## Rationalizations

| Excuse | Reality |
|---|---|
| "These two stocks are probably their whole portfolio" | You don't know. Concentration advice from invented context is fabrication — ask or omit. |
| "News says the ex-dividend is coming; the user can confirm the date" | TWT48U is one curl away. Verify it, or state that your attempt failed. |
| "The stop level is obviously just the MA" | The reader executes these numbers. The basis belongs inline, next to the number. |
| "They're down 50%, staged-exit advice is the gentle version" | Gentleness ≠ vagueness. Name the sunk-cost fallacy and keep the verdict framework-driven. |
| "The holding thesis is obvious from context" | If they never said why they hold it, you're guessing. Conditional verdicts per thesis. |

## Data sources

Market gate and market-wide endpoints (MI_INDEX, T86, punish/notice, one-day-lag gotchas): the **tw-stock-entry** skill and its references. Per-stock fundamentals, margin balances, and the dividend calendar: [references/data-sources.md](references/data-sources.md) — read it before the first curl.
