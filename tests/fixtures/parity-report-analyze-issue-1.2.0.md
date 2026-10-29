## Root Cause
`repo.fetch_orders` was changed to `ORDER BY created_at DESC` (newest first) in commit 2e69aa5 ("feat: newest orders first in customer view"), but `reports.first_order_date` still takes `orders[0]` assuming oldest first, so for any customer with more than one order it now returns their newest order date (`app/repo.py:11`, `app/reports.py:6-9`). It is a regression from the order-pagination branch, not a report config problem.

Hypothesis tested: IF a customer has several orders THEN the first order date is the earliest `created_at` (as in the Oct 20 export), BUT it shows the latest (c-1042: 2026-10-25 instead of 2024-03-02), THEREFORE the sort direction of the shared `fetch_orders` changed under a caller that relied on the order.

## Evidence
- `app/repo.py:9-11` - `fetch_orders` docstring "Newest first." and `ORDER BY created_at DESC`.
- `git show 2e69aa5` - the only change to that line: `ORDER BY id` -> `ORDER BY created_at DESC`. Before that (4130a1d, bcf9b97) the order was `ORDER BY id`, so `orders[0]` was the earliest order.
- `app/reports.py:6-9` - `first_order_date` calls `repo.fetch_orders(conn, customer_id)` and returns `orders[0]["created_at"][:10]`. It has no sort of its own and was not touched by the branch.
- Repro (read-only, in-memory sqlite, nothing written; customer with orders 2024-03-02, 2025-06-01, 2026-10-25; a second customer with one order 2026-01-01): `first_order_date` returned `2026-10-25` for the multi-order customer and `2026-01-01` for the single-order one. This matches Lanchi's note that only multi-order customers are affected.
- `python3 -m unittest discover -s tests` - 7 tests, OK. The suite is green because the only report test (`tests/test_reports.py:21-22`) uses customer 2, who has one order. No test covers `first_order_date` with 2+ orders, so the regression was not caught. `tests/test_api.py:34,40` were updated to expect newest first, i.e. the new order is asserted but the report's dependence on the old order is not.
- Not verified: the real c-1042 data and the Oct 20 / Oct 27 exports (binary attachments, no DB access here). That 2026-10-25 is c-1042's latest order is inferred from the pattern, not checked. The "released last week" date is from the ticket; the repo commit timestamps are fixture timestamps and don't confirm it.

## Impact
- Scope: every org using the cohort/customer report's first-order-date column, for every customer with more than one order. Org 5338 reported it; other orgs are likely affected but not confirmed. Single-order customers are correct.
- Severity: wrong data in a weekly export, no data loss (stored orders are untouched). Any cohort or retention analysis the customer built from the Oct 27 export is skewed. No workaround other than the Oct 20 export for the first-order-date column.
- Urgency: Priority High; the customer exports weekly, so the next wrong export is around Nov 3.
- Blast radius: `fetch_orders` has three callers. `app/reports.py:6` (broken, this ticket); `app/api.py:18` (customer orders API, newest first was intended); `scripts/export.py:12` (the CSV export now also lists newest first, and 8eac160 added a header row and a `created_at` column, so anything parsing the weekly CSV by position or expecting oldest-first rows may also have changed; not part of this ticket's report but worth checking). Related, same commit: sorting on `created_at` alone with LIMIT/OFFSET (`app/repo.py:11,14`) has no tiebreaker, so orders with identical timestamps can repeat or vanish across pages (not tested here).

## Action Items
- [ ] Fix `first_order_date` so it does not depend on caller-visible ordering (e.g. add a repo function that selects `MIN(created_at)`, or an explicit ascending sort; SQL stays in `app/repo.py` per CLAUDE.md) - you (assignee) - the report must not rely on the default order of a function another feature changes
- [ ] Add a test for `first_order_date` with a multi-order customer (customer 1 in the fixture: expect `2026-01-05`) - you - the current test uses a single-order customer, which is why the suite stayed green
- [ ] Regenerate the Oct 27 export for org 5338 after the fix and confirm c-1042 shows 2024-03-02 - you, then send to Lanchi - confirms the fix against real data, which I could not check
- [ ] Reply to Dash/Lanchi confirming the cause is the order-pagination release (commit 2e69aa5) - you - Dash raised the question and it needs an answer for the customer
- [ ] Check whether other orgs' exports since the release show wrong first-order dates, and whether the weekly CSV consumers (`scripts/export.py`: row order, new header, new column) were told about the change - you with Lanchi (CS) - to decide whether proactive customer communication is needed
- [ ] Add `id` as a tiebreaker to the `ORDER BY` used with pagination - you - pagination correctness, can be a separate small PR

## Decision Needed
- [ ] Is "newest first" in `fetch_orders` intended to stay for the customer view? (It looks intentional per the commit message; the proposed fix keeps it and changes only the report.)
- [ ] Should the header row / `created_at` column added to the export CSV (8eac160) stay as-is for customers who parse the weekly file, or be announced?
- [ ] Fix and re-export only for org 5338, or proactively notify all orgs that use the report?
