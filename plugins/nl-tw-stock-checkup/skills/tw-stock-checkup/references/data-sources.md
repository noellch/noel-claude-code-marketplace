# Per-stock data sources — fundamentals, margin, dividend calendar

Complements the tw-stock-entry references (market-wide endpoints, one-day-lag rules, ROC-year format `1150729` = 2026-07-29). All requests need a browser `User-Agent`. OpenAPI bulk files lag one trading day unless noted.

## Fundamentals (TWSE OpenAPI, listed companies)

| Endpoint | Content | Key fields |
|---|---|---|
| `/opendata/t187ap05_L` | monthly revenue, all companies | `資料年月` (ROC), `營業收入-當月營收`, `-上月營收`, `-去年當月營收` — compute YoY/MoM yourself |
| `/opendata/t187ap14_L` | quarterly EPS, all companies | `年度`, `季別`, `基本每股盈餘(元)` — quick EPS lookup |
| `/opendata/t187ap06_L_ci` | quarterly income statement (一般業) | revenue, gross profit, operating income, net income — margin trajectory; financial-industry companies live in sibling files (`_bd`, `_ins`, `_fh`) |
| `/opendata/t187ap03_L` | company profile | capital, chairman, industry — float/capital size context |

Only the latest published period is in each file — for revenue history beyond the current month, query month by month is NOT possible via these files; use the trend fields (上月/去年當月) plus news for older context, and say which months are actually measured.

## Margin balances (融資融券)

```
https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN
```

Per-stock rows, Chinese field names: `融資今日餘額`, `融資前日餘額`, `融券今日餘額`, `融資限額`. Lags one day; the same-day RWD variant (`/rwd/zh/marginTrading/MI_MARGN?date=...`) publishes in the evening — before that it returns 「沒有符合條件的資料」. Prior-day balances are sufficient for the trend panel; state the data date. Rising margin balance into a downtrend = forced-selling fuel; quantify it before advising staged exits.

## Known data gaps (state them, don't silently skip)

- **Major-holder % / 股權分散**: no TDCC endpoint in this scope — mark "not findable via endpoints"; a web-sourced figure must be labeled unverified.
- **Company-specific report dates**: no endpoint for 法說/公告 calendars. Use statutory deadlines (monthly revenue by the 10th; quarterly filings per regulatory schedule) labeled 推論的. Never quote a news headline for a date — either an endpoint confirms it or it is an inference.

## Ex-dividend calendar (除權息預告)

```
https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL
```

**Forward-looking** — rows are upcoming ex-dates. `Date` (ROC) = ex-date, `Exdividend` = 息/權, `CashDividend` = amount. This is the endpoint that answers "is the ex-dividend imminent" — never quote a news headline for a date this file contains.

## Valuation

`BWIBBU_d` (same-day, publishes evening, polite-refusal message before that) with `BWIBBU_ALL` (prior-day) as fallback — details in tw-stock-entry references.

Compare PER/PBR against the stock's **own** range, not a hand-picked peer. Preferred method: sample the official per-stock monthly file across the past year —

```
https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU?stockNo=XXXX&date=YYYYMM01&response=json
```

— it carries the actual official PER of each day (trailing EPS as it was then). The approximation "price history × today's trailing EPS" is a fallback only; it systematically understates past PER when earnings grew, so label its bias inline.

To check a "cheaper than peers" claim: join `t187ap03_L` 產業別 with today's `BWIBBU_d`, take the industry median, and state the stock's rank — verify the basis or reject it explicitly, never accept the claim untested.

## History

Yahoo chart API (`query1.finance.yahoo.com/v8/finance/chart/{code}.TW?range=1y&interval=1d`, browser UA, nulls on halted days) — same usage and indicator formulas as tw-stock-entry. Cross-check the latest close against a TWSE source before publishing any number built on this history.
