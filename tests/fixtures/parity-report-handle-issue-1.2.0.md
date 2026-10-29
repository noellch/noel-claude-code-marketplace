## 問題陳述（Phase 1）

Beauty Corp（org 5338）的 Customer report「first order date」欄位，對下過多張訂單的老客戶改顯示最近一張訂單的日期（c-1042：應為 2024-03-02，顯示 2026-10-25）。服務是 orders-svc；每週匯出的客戶受影響，10/20 匯出正常、10/27 開始錯誤。

來源：Asana「MAAC Issues」（非 Support project）task 匯出檔。Asana MCP 不可用，無法搜尋同 project 是否有同 Feature／同症狀的其他票，這一步未做。Lanchi 附的兩份匯出檔是 binary，沒看到，所以 c-1042 的 2026-10-25 是引用票內文字，未自己驗證。

## 分類（Phase 2）

這看起來是 MEDIUM issue，走 Flow B（Investigate & Fix）。依據：單一服務、原因未知需調查、沒有新 API／頁面／migration。

## Investigation Report

**Root Cause:** `app/repo.py:11` 的 `fetch_orders` 被 commit `2e69aa5`（"newest orders first in customer view"）從 `ORDER BY id` 改成 `ORDER BY created_at DESC`；`app/reports.py:9` 的 `first_order_date` 靠「第一筆 = 最早」的隱含假設取 `orders[0]`，於是對多訂單客戶回傳最新一筆的日期。

**Hypothesis tested:** IF `first_order_date` 取的是 `fetch_orders` 的第一列，且 `fetch_orders` 現在是新到舊 THEN 多訂單客戶會得到最早日期 BUT 實際得到最新日期（c-1042 → 2026-10-25）THEREFORE 排序方向改變就是原因。此假設在做程式碼確認前就寫定，並用最小重現驗證。

**Measured:**
- 重現指令（scratch，不在 repo 內）：`python3 -I /tmp/repro.yUvG/repro.py`，建兩筆 customer 1042 的訂單（2024-03-02、2026-10-25），呼叫 `reports.first_order_date`。輸出 `got 2026-10-25`、AssertionError（預期 2024-03-02），exit=1。症狀與票上完全一致。
- 同一支腳本對 init commit `4130a1d`（用 `git archive` 解到 `/tmp/orders-prev.syVC`）輸出 `got 2024-03-02`、exit=0。
- `git show bcf9b97:app/repo.py` 第 10 行仍是 `ORDER BY id`：分頁 commit（bcf9b97）本身沒有改排序；改排序的是 `2e69aa5`。`git log` 顯示這三個 commit 同在 `feature/order-pagination`，即上週出貨那批。
- `grep` 全 repo：`fetch_orders` 的呼叫者只有 `app/api.py:18`、`app/reports.py:6`、`scripts/export.py:12`（`first_order_date` 在 app 內只有 test 呼叫）。
- `python3 -m unittest discover -s tests`：7 tests OK。測試是綠的，因為 `tests/test_reports.py:22` 只測單訂單客戶（customer 2），與票上「只有多訂單客戶受影響、單訂單正常」吻合；`test_customer_orders_*` 在 `2e69aa5` 已同步改成新到舊。

**Inferred:**
- Dash 的猜測方向對，但精確地說不是「分頁」造成，而是同一次出貨裡的排序方向變更。
- 凡是多訂單客戶的 `first_order_date` 都會錯，不限 org 5338（程式碼無 org 判斷）；實際其他 org 是否有人注意到，未查。
- 票上說的「customer report」與 `reports.py` docstring 的「cohort report」是否為同一支，我沒有在 repo 內找到呼叫端，未證實；`first_order_date` 是 repo 內唯一產生「首單日期」的函式。

**Ruled out:**
- 分頁邏輯（`api.py:13-19`）：報表路徑呼叫 `fetch_orders` 時不帶 limit／offset，沒有經過分頁。
- 報表設定：Dash 回報沒動；程式內沒有 report config 可影響此函式。
- `bcf9b97`（分頁 commit）：排序仍是 `ORDER BY id`，不是原因。
- `8eac160`（export 加欄位）：只動 `scripts/export.py`，不影響 `first_order_date`。

**Confidence:** High（根因已用「重現在 HEAD 紅、在 init commit 綠」量過）。「其他 org 都受影響」與「customer report = 這支函式」屬推論，Medium。

**Impact:** scope 已知 1 個 org（5338），推論所有有多訂單客戶的 org 都會算錯 · severity 輸出錯誤資料（非資料遺失，DB 內 created_at 不受影響；匯出檔錯，不用 backfill，修好後重匯即可）· urgency 客戶每週匯出，下一次約 11/3，High priority · blast radius：修在 `fetch_orders` 排序會同時動到 `api.customer_orders`（新到舊是該 commit 刻意的產品行為，且有測試鎖定）與 `scripts/export.py`；修在 `first_order_date` 則只動報表。另外 `scripts/export.py` 因同一個 commit 現在也是新到舊輸出（`2e69aa5` 之前是 id 升冪），若下游有人依賴順序，這是同類問題，未驗證下游。

**Affected files:**
- `app/reports.py:6-9`（`first_order_date` 依賴列順序）
- `app/repo.py:11`（排序變更的源頭；`CLAUDE.md` 規定 SQL 只能放這裡，所以若要「最早一筆」的查詢，SQL 也要放 repo）
- `tests/test_reports.py:21-22`（需補多訂單客戶的 case，現有測試抓不到）
- 同源但是否要動待決定：`scripts/export.py:12`

**Action items:**
- [ ] 讓 `first_order_date` 不再依賴 `fetch_orders` 的排序（例如在 repo 加明確的「最早訂單」查詢 `ORDER BY created_at ASC LIMIT 1`，或 `fetch_orders` 加 order 參數）——我——保持 customer view 新到舊、報表回到最早
- [ ] 補測試：同一客戶兩筆以上訂單，斷言 `first_order_date` 為最早日期（先紅後綠）——我——現有測試全是單訂單
- [ ] 修好後請 Lanchi／Beauty Corp 重匯 10/27 的報表——Lanchi——客戶手上的檔案是錯的
- [ ] 確認 `scripts/export.py` 的輸出順序有沒有下游依賴——Noel／Dash——同一個 commit 改了它的順序
- [ ] 回覆 Dash 與 Lanchi 根因與時程——Noel——Dash 在票上問過

**Decision needed:**
1. 這是 bug（`2e69aa5` 改共用函式的排序破壞了報表）；沒有要保留「顯示最近日期」的意圖。請確認修法：保留 `fetch_orders` 新到舊（customer view 要求），改讓報表明確取最早；還是你傾向別的做法？
2. `scripts/export.py` 的列順序變成新到舊，要不要一起處理（我預設不動，只回報）？
3. 時序備註：`2e69aa5` 與分頁 commit 同在上週出貨的 `feature/order-pagination`。我沒有看 prod 資料，不知道其他 org 是否已被影響。

**Re-scope：** 調查結果是位置已知的小修（`reports.py` 一處，加上 repo 一個查詢與一個測試，少於 5 個檔案，沒有跨服務、沒有新 API／migration），所以 Scope changed — moving to SMALL（Flow A）。不過因為上面 Decision needed 還有待你拍板，我在這裡停下，沒有改任何程式碼、沒有 commit。

**環境備註：** 跑測試與重現時 Python 在 repo 內產生了 untracked 的 `app/__pycache__/`（和 `tests/__pycache__`，若有）；你要求不刪除任何東西，所以沒清。repo 內沒有其他變動，`feature/order-pagination` 分支未動。
