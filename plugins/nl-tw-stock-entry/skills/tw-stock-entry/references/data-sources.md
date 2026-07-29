# TWSE / market data sources — endpoint map and gotchas

All requests need a browser `User-Agent` header. TWSE `Date` fields use ROC years: `1150729` = 2026-07-29. Convert with year + 1911.

## Same-day full market (the primary source after close)

```
https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=YYYYMMDD&type=ALLBUT0999&response=json
```

Available after ~15:00 TW time on trading days. Check `stat == "OK"`. Structure:

- `tables[0]` — index closes (row `發行量加權股價指數`: [name, close, sign-html, delta, pct])
- `tables[7]` — breadth: 漲/跌/持平 counts; each row like `上漲(漲停) 2,092(15) 243(6)` where the first pair includes warrants, the second pair is stocks only
- `tables[8]` — all securities (~1,373 rows), fields: 證券代號, 證券名稱, 成交股數, 成交筆數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌(+/-), 漲跌價差, …, 本益比
  - row[9] (漲跌 sign) is an **HTML string** (`<p style=...>-</p>`) — detect direction by whether it contains `-`
  - row[10] is the absolute delta; compute pct against `close − delta`
  - numbers are comma-formatted strings; prices can be `--` for untraded

Filter to common stocks: 4-digit numeric code. This drops ETFs (00xx / 5-digit), warrants, preferred (letter suffix).

## OpenAPI bulk files — LAG ONE TRADING DAY

`https://openapi.twse.com.tw/v1/...` — convenient but the files reflect the **previous** trading day until refreshed. Always check the `Date` field against today before trusting them.

| Endpoint | Content | Notes |
|---|---|---|
| `/exchangeReport/STOCK_DAY_ALL` | all-stock daily OHLCV | lags one day; ~1,373 rows (stocks + ETFs) |
| `/exchangeReport/STOCK_DAY_AVG_ALL` | close + monthly average price | **one row per security, single date**, ~26,800 rows because it includes warrants — the row count makes it look like month-history per stock; it is NOT. Verify distinct `Date` values before treating any bulk file as history. `MonthlyAveragePrice` ≈ MA20 proxy |
| `/exchangeReport/BWIBBU_ALL` | PE / PB / dividend yield | lags one day; usable if you print its date |
| `/announcement/punish` | 處置股 list | includes warrants — match by code |
| `/announcement/notice` | 注意股 list | same |

Price history is only available per stock (STOCK_DAY below) or from Yahoo — plan request counts accordingly (fine for ~15 survivors, not for the full market).

## Same-day valuation

`/rwd/zh/afterTrading/BWIBBU_d?date=YYYYMMDD&selectType=ALL&response=json` publishes late in the evening; before that it returns a polite "很抱歉，沒有符合條件的資料" message. Fallback: BWIBBU_ALL (prior day) and state the date.

## Institutional flows (三大法人, T86)

The openapi variant 302-redirects to HTML — don't use it. Use:

```
https://www.twse.com.tw/rwd/zh/fund/T86?date=YYYYMMDD&selectType=ALLBUT0999&response=json
```

- Same-day file publishes around 16:30 TW time; before that it returns 「沒有符合條件的資料」 — wait and retry, don't conclude it's missing
- Totals include dealer hedging (權證對沖) which inflates apparent conviction; the foreign-investor column excludes dealers — weight conclusions on it
- Pull the crash-window days separately and sum per stock

## Per-stock cross-check

```
https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?stockNo=XXXX&date=YYYYMM01&response=json
```

Monthly per-stock daily table — this is also the source for the Layer 1 month-trend condition (first vs latest close). Cross-check at least one screened name against the pipeline output before publishing numbers. Untraded days show `--` prices; filter them.

## History and indicators

```
https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?range=1y&interval=1d
```

Needs a browser UA. Compute indicators yourself: MA (simple), RSI-14 (Wilder smoothing), KD (9,3,3 — K = ⅔K′+⅓RSV), MACD (12/26 EMA, 9 signal). Nulls appear in the arrays on halted days — filter before computing.

## Reporting conventions

- Taiwan color convention: **red = up, green = down** — invert Western defaults in any visual output and note the convention in the legend/subtitle
- TPEx (上櫃) is not covered by any endpoint above; say so when reporting "full market" screens
