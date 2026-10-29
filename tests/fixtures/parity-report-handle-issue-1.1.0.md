## Problem statement

Beauty Corp (org 5338) reports that the "first order date" column in the customer report shows recent dates for long-time customers (c-1042: first order 2024-03-02, report shows 2026-10-25). The Oct 20 export was correct, the Oct 27 export is wrong, and only customers with more than one order are affected. The service is orders-svc (`app/reports.py` plus `app/repo.py`), and the affected users are every customer with 2+ orders in any report or export that uses the first-order-date value. The ticket is in MAAC Issues, not the Support project, so I fetched it as a plain Asana task (exported file) and did not use `cl-support:triage`.

This looks like a **MEDIUM** issue (single service, cause unknown at intake, no new API/page/migration), so I'm using the Investigate & Fix workflow (Flow B).

Nothing has been changed or committed. The repo is still on `feature/order-pagination`, clean.

## Investigation Report

**Root Cause:** Commit `2e69aa5` ("feat: newest orders first in customer view") changed `repo.fetch_orders` from `ORDER BY id` to `ORDER BY created_at DESC`. `reports.first_order_date` takes `orders[0]` and treats it as the earliest order, so it now returns the newest order's date. The pagination change itself (`bcf9b97`) is not the cause; the sort flip that shipped in the same release is.

**Why chain:**
1. The report shows a recent date because `first_order_date` returns the newest order's `created_at`.
2. It does so because `orders[0]` is now the newest order.
3. That is because `fetch_orders` now sorts `created_at DESC` (`app/repo.py:11`).
4. It was changed for the customer-orders view, and `fetch_orders` is a shared function with two other callers.
5. `first_order_date` relies on an implicit "oldest first" ordering that was never part of `fetch_orders`' contract, so nothing flagged the change. The contract is now documented as "Newest first." (`app/repo.py:10`).

**Measured:**
- `app/reports.py:6-9`: `orders = repo.fetch_orders(conn, customer_id)` then `return orders[0]["created_at"][:10]`.
- `app/repo.py:11`: `ORDER BY created_at DESC`. `git diff bcf9b97 2e69aa5` shows the line was `ORDER BY id` before.
- Red-capable loop (throwaway script outside the repo, `/tmp/loop_first_order.py`; customer 1042 with orders on 2024-03-02 and 2026-10-25, which are the ticket's example dates):
  - HEAD (`feature/order-pagination`): `got 2026-10-25 expected 2024-03-02`, exit 1.
  - Same script against `git archive` copies of earlier commits: `4130a1d` (init) gives 2024-03-02, exit 0; `bcf9b97` (pagination) gives 2024-03-02, exit 0; `2e69aa5` (newest-first) gives 2026-10-25, exit 1. The regression starts at `2e69aa5` exactly.
- `python3 -m unittest discover -s tests`: 7 tests, OK. The suite is green despite the bug.
- `tests/test_reports.py:21-22` only checks customer 2, who has a single order (`tests/test_reports.py:12`), so ordering cannot matter there. That matches Lanchi's observation that single-order customers are fine.
- `grep` for `fetch_orders` / `first_order_date` / `orders[0]` across `*.py`: only `reports.py:6`, `api.py:18`, `scripts/export.py:5,12`, plus the definition. `reports.py:9` is the only `orders[0]` use.

**Inferred:**
- Org 5338's weekly export reads the report through `first_order_date` (the ticket says the config is unchanged, and the report code path is the only consumer in this repo). I did not see the exports or the report-config layer, so I am inferring the export-to-function link.
- The values are computed at read time, not stored, so no data is corrupt and no backfill is needed. Once the code is fixed the next export is correct. This follows from the code (no writes anywhere in `reports.py`); I did not check the production DB.
- The release timing fits: the Oct 20 export was before last week's release, the Oct 27 export after.
- Dash's guess ("order pagination release") is right about the release but not the commit: pagination alone (`bcf9b97`) is fine. The ordering change is what breaks it.

**Ruled out:**
- Pagination (`bcf9b97`): the loop is green at that commit. Also `first_order_date` calls `fetch_orders` without `limit`, so LIMIT/OFFSET is not applied.
- Report config change: Dash states nothing changed on that side, and no config exists in this repo.
- Bad data or timezone: `created_at[:10]` slicing is unchanged since init, and the script reproduces with clean data.
- `export.py` as the source of the wrong report date: it does not call `first_order_date`.

**Confidence:** High for the code-level cause (measured: red loop plus bisection to the exact commit). Medium for "this is exactly what produced the customer's file", because the customer's exports and production data were not inspected.

**Affected files:**
- `app/reports.py:6-9` (breaks; needs the earliest order explicitly, not `orders[0]` of a newest-first list)
- `app/repo.py:9-16` (owns the ordering; per `CLAUDE.md` all SQL lives here, so any fix that needs a different order or a "earliest order" query goes here)
- `tests/test_reports.py:21-25` (add a multi-order customer; the current fixture cannot catch this)

**Other findings (not the cause, flagged so you can decide):**
- `scripts/export.py:12` also uses `fetch_orders`, so its CSV rows are now newest-first instead of oldest-first. The same release (`8eac160`) also added a header row and a `created_at` column to that export. If anyone consumes that weekly CSV by position or by "first row is oldest", it changed too. This is not what the ticket reports, and I did not check who consumes it.
- Customers using `api.customer_orders` now get newest-first by design (the intent of `2e69aa5`), so I would not change that behaviour.

**Scope check:** the root cause points at one known location with a small change (roughly `reports.py` plus possibly one repo query or parameter, plus a test), with no new API, page or migration. That is below the MEDIUM bar, so under the Re-scope rule: scope changed, moving to SMALL (Quick Fix: report, fix, verify, deliver only when asked).

## Stopping here for your confirmation

Please confirm this diagnosis before I touch any code. Two points to decide when you do:
1. Whether the earliest-order lookup should live in `repo.py` (a dedicated query or an explicit sort argument, in line with the "all SQL in repo.py" rule) rather than re-sorting in `reports.py`.
2. Whether to look into the `export.py` ordering/format change separately (not part of this ticket).

No commit or PR will be made unless you ask.
