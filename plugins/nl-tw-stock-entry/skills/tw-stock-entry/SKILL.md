---
name: tw-stock-entry
description: Use when the user asks whether today is a day to enter the Taiwan stock market, which TWSE stocks look buyable, or requests a daily entry screen/assessment — triggers on "進場", "可以買哪些股票", "台股篩選", "進場評估", "今天買什麼", "entry screen"
---

# TW Stock Entry Assessment

## Overview

Deterministic daily entry assessment for TWSE-listed stocks: a hard market gate plus pinned screen criteria decide the verdict. Your job is execution and reporting, not inventing criteria per run.

**The baseline failure mode**: the agent concludes "today is not a good entry day" and then delivers a 10-name buy list anyway, hedged with "small positions, staged entry". The gate rule below exists to kill exactly that.

## The Gate Rule (non-negotiable)

```
GATE FAILS → NO ENTRY LIST. A watchlist is not a buy list.
```

Gate fails when ANY of:
- TAIEX single-day change ≤ −2%
- limit-down count ≥ 30 (the stocks-only column of the breadth table, not the warrants-inclusive total)
- Layer 1 momentum screen passes 0 stocks

When the gate fails, the output is exactly: verdict 觀望 + relative-strength watchlist (every table labeled 「非買進訊號」) + the stabilization checklist. No exceptions for "small position", "staged entry", or "defensive names only".

## Execution Flow (MANDATORY order)

1. **Market context** — TAIEX close, breadth (up/down/limit-down counts), turnover. First determine the **signal day**: same-day close data publishes ~15:00 TW time via the RWD endpoint; before that, every source (RWD and OpenAPI bulk) carries the previous trading day. Signal day = the latest complete trading day whose data is actually available — print it, never present it as today's if it isn't. **Entry window = the trading day after signal day.** A run during trading hours (signal day ≠ today) makes step 4 mandatory.
2. **Screen** — run the pinned two-layer screen below on the full market, on signal-day data. Do not tune thresholds or lookback windows per run.
3. **Verdict** — apply the gate on signal-day data. Pass → continue to step 4/5. Fail → watchlist + stabilization checklist, skip to step 6. Either path: cross-check every published table against the 處置/注意 lists and exclude or flag matches.
4. **Intraday confirmation (veto-only)** — only when signal day ≠ today and the gate passed; see the section below. May downgrade the verdict to 觀望 or drop candidates; never upgrades.
5. **Deep check (entry candidates only)** — per stock: 1y daily history, MA alignment (MA5>MA20>MA60), RSI/KD/MACD, volume expansion; flag imminent ex-dividend dates.
6. **Report** — conclusion first; criteria, signal day, entry window, and every data date stated; TW color convention (紅漲綠跌) in any visual output; ends with a non-advice disclaimer. Produce an HTML artifact only when the user asks — then invoke the dataviz skill before writing chart code.

## Pinned screen criteria

Universe: TWSE common stocks only — 4-digit numeric code (excludes ETF/warrants/preferred). TPEx is not covered; say so in the report.

**Layer 1 — momentum (feeds the gate):**
- trade value > 1 億 TWD
- close > monthly average price (MA20 proxy)
- day change between +1% and +7.5%
- close ≥ day high × 0.985, and close > open
- month trend up, pinned definition: today's close > the month's first trading-day close. Apply this condition LAST, on the survivors of the other four — it needs one per-stock STOCK_DAY request each; no bulk file carries price history.

**Layer 2 — crash-day relative strength (feeds the watchlist):**
- trade value > 0.5 億, day change > 0
- close > monthly average price
- close ≥ day high × 0.97

Watchlist fallback when Layer 2 also passes 0: green close + value > 0.5 億. Any watchlist table (Layer 2 output or fallback) is sorted by trade value, top 10–15, each row annotated with vs-monthly-average % and close position within the day's range.

**Stabilization checklist (always shown when the gate fails):**
1. Index stops making new lows, reclaims the 5-day MA, limit-down count shrinks to single digits
2. US semiconductors (SOX) stabilize overnight
3. A reversal candle on expanded volume appears — then watch which watchlist names make short-term highs first

## Intraday confirmation (veto-only)

Closes the blind spot of a during-hours run: the gate was judged on yesterday's close while today's tape may already contradict it. Data: MIS snapshot API, ~5s delayed (see references).

- **Direction is one-way.** Live data can only downgrade — veto a passing gate or drop a candidate. A gate that failed on signal-day data stays failed no matter how strong today's rebound looks; it needs a full trading day's data to pass.
- **Index veto**: fetch live TAIEX (`tse_t00.tw`). Intraday change vs reference price ≤ −2% → verdict becomes 觀望, entry list dropped, watchlist rules apply.
- **Candidate re-check** (gate still passing): fetch live quotes for every entry candidate. Drop names now below monthly average price. Flag names up more than +7.5% intraday as chase risk — flagged means not recommended for today's window.
- **Print the confirmation timestamp** next to the verdict. If MIS is unreachable, no same-day entry list: label all candidates 適用於下一交易日 instead.

## Optional enrichment

Institutional flows (三大法人 T86) for candidates or watchlist names — a strong secondary signal on crash days (who is absorbing the selling). Endpoint and its pitfalls are in the references file.

## Completion criteria

Done only when ALL hold:
- Verdict is exactly one of 進場條件成立 / 觀望, backed by the pass-count as evidence
- Every table of stock names carries its label: 進場候選 or 觀察名單（非買進訊號）
- Signal day and entry window are stated; every data source's date is printed
- If run during trading hours with a passing gate: the intraday confirmation timestamp is printed, or its unavailability plus the next-day-only downgrade is stated
- Output ends with a non-advice disclaimer (非投資建議)

## Rationalizations

| Excuse | Reality |
|---|---|
| "Small position / staged entry makes a list OK on a gate-fail day" | Publishing a list IS the recommendation. Gate failed → watchlist only. |
| "A different lookback window seems more reasonable today" | Criteria are pinned for repeatability. Change the skill, not the run. |
| "Valuation file is one day old, close enough" | Usable — but print its data date in the output. |
| "News quotes an analyst calling this a buying point" | Forecasts are context, not signals. The gate decides. |
| "These are defensive names, different from chasing rebounds" | Defensive or not, a named list on a gate-fail day is still a buy list. |
| "The market is bouncing hard today, yesterday's gate fail is stale" | Intraday data is veto-only: it can cancel an entry, never create one. |

## Data sources

All endpoints, one-day-lag gotchas, ROC-year date format, and field layouts: [references/data-sources.md](references/data-sources.md) — read it before the first curl, not after the first failed request.
