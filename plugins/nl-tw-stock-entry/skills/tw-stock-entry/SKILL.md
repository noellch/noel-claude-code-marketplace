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

1. **Market context** — today's TAIEX close, breadth (up/down/limit-down counts), turnover. The data date MUST equal today: OpenAPI bulk files lag one trading day; same-day data comes from the RWD endpoint (see references). If only stale data is available, state that explicitly in the output instead of presenting it as today's.
2. **Screen** — run the pinned two-layer screen below on the full market. Do not tune thresholds or lookback windows per run.
3. **Verdict** — apply the gate. Pass → entry candidates go to step 4. Fail → watchlist + stabilization checklist, skip to step 5. Either path: cross-check every published table against the 處置/注意 lists and exclude or flag matches.
4. **Deep check (entry candidates only)** — per stock: 1y daily history, MA alignment (MA5>MA20>MA60), RSI/KD/MACD, volume expansion; flag imminent ex-dividend dates.
5. **Report** — conclusion first; criteria and every data date stated; TW color convention (紅漲綠跌) in any visual output; ends with a non-advice disclaimer. Produce an HTML artifact only when the user asks — then invoke the dataviz skill before writing chart code.

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

## Optional enrichment

Institutional flows (三大法人 T86) for candidates or watchlist names — a strong secondary signal on crash days (who is absorbing the selling). Endpoint and its pitfalls are in the references file.

## Completion criteria

Done only when ALL hold:
- Verdict is exactly one of 進場條件成立 / 觀望, backed by the pass-count as evidence
- Every table of stock names carries its label: 進場候選 or 觀察名單（非買進訊號）
- Every data source's date is printed and equals today, or its staleness is stated
- Output ends with a non-advice disclaimer (非投資建議)

## Rationalizations

| Excuse | Reality |
|---|---|
| "Small position / staged entry makes a list OK on a gate-fail day" | Publishing a list IS the recommendation. Gate failed → watchlist only. |
| "A different lookback window seems more reasonable today" | Criteria are pinned for repeatability. Change the skill, not the run. |
| "Valuation file is one day old, close enough" | Usable — but print its data date in the output. |
| "News quotes an analyst calling this a buying point" | Forecasts are context, not signals. The gate decides. |
| "These are defensive names, different from chasing rebounds" | Defensive or not, a named list on a gate-fail day is still a buy list. |

## Data sources

All endpoints, one-day-lag gotchas, ROC-year date format, and field layouts: [references/data-sources.md](references/data-sources.md) — read it before the first curl, not after the first failed request.
