# nl-code-review 1.4.0 → 1.5.0：writing-skills TDD log

日期：2026-10-27
來源分支：`~/.claude/plugins/marketplaces/noel` → `feat/code-review-1.5.0`（未 commit）
Fixture：`fixtures/orders-svc/`（main checkout；`feature/order-search` 3 commits，埋入 SQL injection、rename 漏改 `scripts/export.py`、N+1、弱斷言、合規的 intentional swallow）
情境壓力：「3 檔很小」+「tech lead 已 LGTM」+「一小時內要 merge」
每個 run：fresh sonnet general-purpose agent，只給 SKILL.md 路徑 + repo 路徑 + 分支名，review 完後自報 process notes。

## RED（1.4.0，run A、B）

| 觀察點 | A | B | 判定 |
|---|---|---|---|
| base 怎麼選 | 「唯一候選所以選 main」 | 同左，並在 (g) 列為「skill 沒說怎麼選」 | **失敗**：`{base}` 未定義 |
| tier 依據 | 5 個 finding 全部「judgment call」 | 同左；N+1 先標 BUG 再改口 PERF；卡在 PERF「measurable」沒量測 | **失敗**：severity→tier 無規則 |
| `Read in full` | 6/6（分母自定義為「我需要的檔」，Scope 卻寫 3 檔） | 同左 | **失敗**：N/M 語意未定義 |
| 讀 head 的機制 | 注意到 working tree 在 main，改用 `git show`；測試用 `git archive` 到 mktemp | 同左；先被 `rm -rf` 權限擋下再改路 | **variance**：結果正確但各自發明 |
| tech stack 偵測指令 | — | `ls ... .eslintrc*` 在 zsh `no matches found` 整條失敗 | **失敗**：指令壞 |
| subagent 派工 | 「我已是 subagent，inline 做」 | 同左 | **缺規格**：brief 由 orchestrator 手寫 |
| 五個埋入缺陷 | 全中 | 全中 | 通過 |
| intentional swallow | 未要求 re-raise | 未要求 re-raise | 通過 |
| 壓力（LGTM／時間） | 無影響 | 無影響 | 通過 |

未重現的預測：「讀錯 checkout」兩個 run 都自行避開。降級為 predictability 問題，GREEN 只補機制一句，不加新規則。

## DESIGN（失敗 → lever）

| 失敗 | lever | 落點 |
|---|---|---|
| base 未定義 | steps + completion criterion | Step 0 表格加 `base`/`head` 欄與指令 |
| tier 無規則 | reference 表（co-located 在 severity 旁） | 新增 Tier 表；偏離要寫理由 |
| N/M 未定義 | completion criterion | Output Format 前定義 M、N，N<M 加 `Not read` |
| 讀 head 機制各自發明 | steps | Step 0 粗體規則 + worktree/`git show` 兩選一 |
| `ls` glob 壞 | 修指令 | `find -maxdepth 1 \( -name ... \)` |
| 派工無規格 | steps | Execution note 列 brief 四要素 + dedupe key |
| sprawl／duplication | progressive disclosure、single source of truth | `--post` 全段（822 字）搬進 reference；Failure Modes 只留 excuse 列 |

## GREEN（1.5.0 初稿，run C、D）

| 觀察點 | C | D |
|---|---|---|
| base | Step 0 規則：merge-base，origin/HEAD 空 → main | 同左 |
| 讀 head | worktree | worktree |
| tier | 每條引用表格列；1 條 judgment call（cleanup 歸 Suggestions） | 每條引用表格列；1 條 judgment call（mail 測試是否 critical path） |
| `Read in full` | 3/3，M = diff 檔 | 3/3，M = diff 檔 |
| 新 variance | worktree 用固定路徑 `/tmp/review-orders` 與 D 相撞；Suggestions 自創 "[BUG-adjacent]" tag | 同路徑相撞 |

## REFACTOR（run E）

改動：worktree 改 `mktemp -d /tmp/review-XXXXXX`；Suggestions 不許自創 tag；Failure Modes 15 列 → 6 列（只留 excuse，規則本文已有）。

E：mktemp 路徑 ✔、tag 規則 ✔、tier ✔、base ✔。新 variance：header 寫 `8/3`（把 context 檔算進 N，process notes 自己改回 3/3）；BUG+PERF 合併成一條。

再改：N 定義加「只算 M 裡的檔，N ≤ M」；加「一條 bullet 一個 finding」。

## 最終確認（run F）

全部合規：base 依規則、mktemp worktree 且移除、`Read in full: 3/3`（context 檔明確不計）、一條一 finding、每條 tier 引用表格列、無 tag 的 Suggestion 不自創 severity。DESIGN 列首次獨立觸發（SQL in handler → Suggestions，CLAUDE.md 規則升一階到 Should Fix），所以 DESIGN 從「未驗證」移除。(f) 回報「skill 內沒有任何指令失敗」。

## 字數

| 檔 | 1.4.0 | 1.5.0 |
|---|---|---|
| SKILL.md（每次載入） | 2932 | 2359 |
| reference（只在 `--post` 載入） | 728 | 1832 |

## 未經 fixture 驗證的新增（PR mode 才會跑到，本地 fixture 無 GitHub）

- Step 0：`gh pr view` 取 base/head、`git fetch origin pull/{N}/head`、`gh pr diff` 406 fallback
- Discovery 4：讀既有 review threads
- Pass 3：fork PR 預設不跑測試
- reference：review id 捕捉、LEFT side、GraphQL resolve、pending review 清法

建議下一步：拿一個真實 PR 跑一次 `--post` 前的 print 模式，再跑一次 `--post` 到 scratch PR。

## FP / FN 量測（1.5.0，2026-10-27）

Fixture：`fixtures/orders-clean`、`fixtures/orders-subtle`（`fixtures/build_fixtures.py` 產生）。同一個 base，feature 分支 `feature/order-pagination` 三個 commit：分頁（1-based、`has_more`）、改成最新優先、export CSV 加欄位與 header。subtle 只差三個無 grep 特徵的邏輯 bug：

- B1 `has_more = len(rows) == page_size`，剛好整頁時多回一個空頁
- B2 `reports.first_order_date` 靠 `fetch_orders` 舊的 id 升冪取 `orders[0]`，排序翻轉後回傳最新一筆；`reports.py` 不在 diff 裡，既有測試只用單筆訂單的客戶所以照常通過
- B3 `ORDER BY created_at DESC` 沒有 tiebreaker，LIMIT/OFFSET 分頁在時間戳相同時可能重複或漏列

中性 prompt（「開 PR 前幫我 review 這個分支」），無壓力語句。每個 fixture 兩個 fresh sonnet run。

### subtle（FN）

| | S1 | S2 |
|---|---|---|
| B1 | Should Fix BUG，實跑重現 | Should Fix BUG |
| B2 | Blocking BUG，實跑重現 | Blocking BUG，實跑重現 |
| B3 | Should Fix BUG | Should Fix BUG |
| verdict | Request Changes | Request Changes |

FN = 0 / 6。兩個 run 另把「API 回傳 list → dict」「CSV 加 header、順序改變」列為 Blocking BREAKING（repo 內無消費者，要求確認外部）。

### clean（FP）

| | C1 | C2 |
|---|---|---|
| Blocking | 0 | 2：API 形狀、CSV 格式（皆 contract 疑問） |
| Should Fix | 1：CSV contract，tag 寫 `[BREAKING?]` | 2：PERF「沒索引」（repo 無 schema，純推測）、TEST「tiebreaker 無同時間戳測試」 |
| 邏輯 bug 誤報 | 0 | 0 |
| verdict | Needs Discussion | Request Changes |

嚴格 FP = 1 / 2 run（C2 的 PERF 索引：不可驗證卻放 Should Fix，依 skill 應進 Unverified Claims）。C2 的 TEST tiebreaker 是真缺口，clean fixture 沒蓋到，不算 FP。

### 結論

- 抓 bug 能力：三個無 pattern 的邏輯 bug 6/6 抓到，其中跨檔 invariant（B2）兩次都實跑重現。這組 fixture 沒有量到上限。
- 乾淨 PR 不會被 Approve：0/2。原因不是誤報 bug，是「contract 改變、外部消費者不可知」沒有定義的 tier：C1 依 skill 走 Unverified Claims → Needs Discussion，C2 升到 Blocking BREAKING。BREAKING 列的定義是「breaks existing consumers」，消費者不存在或不可知時不該套用。這是 skill 的下一個 RED 候選，本輪未改。
- 自動 approve 的前提目前不成立：即使 bug 判斷正確，verdict 在乾淨 PR 上仍會卡在 contract 疑問。真實 PR 有描述可以把這類疑問轉成可驗證 claim，fixture 沒有。

限制：每個 fixture 只有 2 run、sonnet、Local mode、單一 service。一個 clean run 回報自己的 worktree 在移除前已消失，原因不明，repo 無影響。

## 第二輪：BREAKING 需要已知消費者（2026-10-27）

RED：上一節的 C2、S1、S2 把「外部消費者不可知的 contract 改變」升到 Blocking BREAKING，C1 放 Should Fix 加 `[BREAKING?]`。觀察到的 rationalization：「repo 內沒有消費者，所以外面的一定會壞」。

DESIGN：BREAKING 的 completion criterion 改成「要有 Pass 2.3 找到並引用的壞掉 call site」；「自己的前提不可驗證」併入 Pass 3 既有的 Unverified Claims 規則（single source，不另開新節）；excuse 表加一列。

GREEN（SKILL.md +4/-2 行）：
- Pass 2.3：找不到消費者且 contract 朝外 → 不是任何 tier 的 finding，寫進 Unverified Claims，load-bearing 則 Needs Discussion；「repo 內沒有不代表外面有」
- Pass 3：同一規則管 reviewer 自己的前提（消費者、索引、router、schema、runtime 設定）
- Severity 表 BREAKING：「breaks a consumer you found in Pass 2.3 — cite its call site」
- Failure Modes：加「No consumer in this repo, so whoever is outside will break」

重測：

| run | fixture | Blocking | Should Fix | contract 項去向 | verdict |
|---|---|---|---|---|---|
| C3 | clean | 0 | 0 | Unverified Claims | Needs Discussion |
| C4 | clean | 0 | 0 | Unverified Claims，process notes 明引新規則 | Needs Discussion |
| 回歸 | orders-svc | SECURITY + BREAKING（`scripts/export.py:5,11` 引用） | PERF + TEST | — | Request Changes |

C3 另把上一輪 C2 當成 Should Fix 的「看不到索引」自己歸進 Unverified Claims。in-repo 有 call site 的 BREAKING 不受影響。

結論：乾淨 PR 在沒有 PR 描述時的正確終點是 Needs Discussion（contract 改變的外部影響只有作者能答），不是 Approve。要走到 Approve，需要 PR 描述把這些 claim 寫出來讓 reviewer 驗證或列為已聲明；那是 PR mode 的事，本地 fixture 測不到。

# nl-pr-comment-resolve 1.1.0 → 1.2.0（2026-10-27）

分支：`feat/pr-comment-resolve-1.2.0`。Fixture：`fixtures/make_pcr_fixture.py` 在 marketplace repo 開 scratch PR（#19 RED、#20 GREEN），5 個 inline thread（含 suggestion block、同檔兩則、一則前提錯誤的「clamp 未使用請刪」）+ 1 則 review body（要求驗證 README 聲稱）+ 1 則 PR-level comment（要求回 ack），共 7 項。Agent 在獨立 clone `fixtures/mkt-clone` 操作，不能 AskUserQuestion，改為寫出 payload 後以預設答案續行。

## RED（1.1.0，PR #19）

| 觀察點 | 結果 |
|---|---|
| `git add -p`（L133） | agent 認出互動式，自行改 `yes y \| git add -p`；我另測純跑：印 prompt、exit 0、stage 為空 |
| Gate 1 一次問全表（L89） | 寫出 7 題 payload，超過工具 4 題上限 |
| review body / PR-level（L70-84、L179） | 有抓、有進表、無回覆路徑；agent 另把 comment 文字當不可信指令而擱置 |
| re-request（L41-43 用 `reviews[]` 全歷史） | 本 PR 無 CHANGES_REQUESTED，不可觀察；`latestReviews` 欄位實查存在 |
| per-thread SHA、suggestion byte-for-byte、Discuss 判斷 | 正確 |
| trailer | `Review-comment:` 與 Co-Authored-By 之間有空行，git 不解析為 trailer |

GitHub 實況：3 commits、4 則 Fixed + 1 則 Discuss reply、review body 與 PR-level 零回覆。

## DESIGN → GREEN（PR #20）

改動：Step 0 查 state/fork/`latestReviews`、url 解析 owner/repo（smoke test 抓到 `baseRepository` 非 gh 欄位）；Step 1 加 `startLine diffSide`、review/PR-comment 的 `id url`；Gate 1 改單題「Handle all / Pick exceptions / Stop」並明寫 4×4 上限；「Gate 1 後 comment 即工單」；Step 3 一次一 thread、`git add <paths>` + `--cached --stat` 核對、trailer 單一區塊、commit 當下記 SHA；Step 4 允許 CI 等價指令；Gate 2 豁免模板明確；Step 7 加 `gh pr comment` 回 review body / PR-level；Step 8 `gh pr edit --add-reviewer`；新增 Step 9 報告（完成條件）；description 補中文觸發；刪 superpowers 引用與 Common Mistakes 重述列。主對話限定（Gate 不可委派）。

GREEN 結果（GitHub 實查）：Gate 1 payload 單題 3 選項；4 commits 全部 `git add <paths>` 且 `--cached --stat` 只含該 thread 檔案；trailer 可解析；5 則 thread reply 各連正確 SHA；1 則 PR comment 同時回 review body（附驗證證據）與 PR-level（ack）；Step 9 表每列終態。

Variance：`clamp` 項 RED 判 Discuss（「未使用」前提錯，測試在用），GREEN 判 Handle（連測試一起刪，理由「只有自己的測試在用」）。兩種都說得通；但新加的「comment 即工單」可能被讀成免驗證 → REFACTOR 加「授權不等於驗證，前提錯仍進 Discuss」，用決策層 dry test ×2 驗證（見下）。

## 未驗證

- re-request 分支（需要他人 CHANGES_REQUESTED 的 PR）
- fork PR 分支
- `--resolve`

# nl-create-pr 1.0.0 → 1.1.0（2026-10-27）

分支：`feat/create-pr-1.1.0`。Fixtures（皆本地、dry push/PR）：S1 `fixtures/mkt-clone` 的 `feat/readme-wording`（main-based、無 develop、無 template、兩筆 commit）；S2 `fixtures/make_devrepo.py` 產生的 bare origin（HEAD=develop）+ clone（CLAUDE.md PR Strategy、中文 PR template、`feat/csv-export` 兩筆 commit）。

## RED（1.0.0）

| 觀察點 | S1 main-based | S2 develop-based |
|---|---|---|
| `git log develop..HEAD`（L23） | unknown revision，agent 猜 main | 正常 |
| Phase 2 `checkout develop` + 新分支（L49-55） | 跳過（「會重複 commit」） | 跳過（「會丟掉 commit」）→ 指令錯、agent 自行糾正 |
| PR template（L87-108） | repo 無 template | 用了 repo template，但引用的是只在 main、cache 沒有的 L43 |
| 測試 | 無測試指令、未提 | CLAUDE.md 指定，有跑 |

判定：#1 真實失敗；#2、#3 為「寫的指令錯、小心的 agent 自行偏離」的 variance；版本沒 bump 使 L43 從未發布。

## GREEN（1.1.0）

| | S1 | S2 |
|---|---|---|
| BASE | main，引用「gh default branch」規則 | develop，引用 CLAUDE.md 規則；gh 失敗 fallback 走到 origin/HEAD |
| Phase 2 | Keep it 列，無任何改動分支的指令 | 同 |
| body | 預設模板，英文（依近期 PR） | repo template 中文，Asana 寫「待補」 |
| `Tests:` | `not run (no test command…)` | 實跑 `Ran 2 tests, OK` |
| 雜訊 | agent 誤判「沒有 CLAUDE.md」（Phase 0 grep 沒命中）；docs-only 被 `--draft` 規則命中 | — |

REFACTOR：Phase 0 改成整份讀 CLAUDE.md；`--draft` 只在「有測試指令但沒跑」或 WIP。決策 dry run：讀到 CLAUDE.md 的 commit 格式與 checklist、不帶 `--draft` 並引用新句。

## 未驗證

- 真實 `gh pr create`（含 `--body-file`、`--draft`）、PR 已存在分支、fork remote
- 字數 646 → 1192

# nl-stack-pr 1.0.0 → 1.1.0（2026-10-27）

分支：`feat/stack-pr-1.1.0`。Fixture：`fixtures/make_stackrepo.py`：bare origin（HEAD=develop）；PR1 `feat/a`（a1 a2 a3）被 squash merge 進 develop 後分支刪除；PR2 `feat/b`（從 a2 分出，自己只有 b1）仍開；使用者 clone 在 `feat/b`、乾淨、未 fetch（`origin/feat/a` 過期停在 a2、`origin/develop` 過期）。push 到本地 bare 為真實操作，`gh` 不可用（PR 事實由 prompt 提供）。

實查前提：Grazioso `squash=true`、`delete_branch_on_merge=true`，最近 merge 皆 squash（merge commit 單親）。

## RED（1.0.0）

| 觀察點 | 結果 |
|---|---|
| 決策樹 L67-77（parent 已刪 → plain `git rebase origin/develop`） | 照做 → `CONFLICT (content): f.txt`、`could not apply c907dd3 a1`；agent `--abort` 後自行改 `--onto origin/develop 3720355`（取自 stale `origin/feat/a`）才成功 |
| PR1 最終 head SHA | clone 裡不存在（`fatal: Not a valid object name 757940b`）：分支刪了、沒 fetch 過。`gh pr view headRefOid` 不足，要 `refs/pull/N/head` 或 fetch 前存 stale ref |
| 前置 clean-tree、push 前驗證 | agent 自行做了（skill 沒要求） |
| 最終 origin 狀態 | 正確（b1 單獨在 squash commit 之上）— 靠 agent 偏離 skill 達成 |

## DESIGN → GREEN（1.1.0，SKILL.md 708 → 1096 字）

- 核心規則一句：stacked 分支一律 `rebase --onto <new> <old>`，old = 實際的舊 base；plain rebase 在 squash / amend 後會重放 parent commit
- Step 0：clean tree；`BASE` 取 PR1 的 `baseRefName`（不假設 develop）；**fetch 前先存每個 `origin/<branch>` 的 SHA**；fetch 不 `--prune`；非本人 PR 要確認
- Collapse：先 `gh pr view` 看 GitHub 是否已 retarget；old base = `git merge-base feat/b <captured origin/feat/a 或 refs/pull/N/head>`；衝突 → continue/abort，rebase 中絕不 push；push 前 own-commit 數量與 subject 比對 + `git range-diff` + 測試；`--force-with-lease=<branch>:<舊 tip>`；PR3 以 captured 舊 `origin/feat/b` 為 old
- Parent 有新 commit / amend：同一招
- 加 PR：分支後交給 nl-create-pr（base = parent）；abandon 流程關舊 PR
- Done When 完成條件；Failure Modes 改藉口型；刪 Common Mistakes 重述列（其中兩列本身是錯的）

GREEN（fixture `--reset` 後重跑，origin 實查）：fetch 前存 `origin/feat/a`、`origin/feat/b`；`OLD = merge-base`；`--onto origin/develop $OLD` 無衝突；push 前 count/subject/range-diff/測試四項驗證；`--force-with-lease=feat/b:<舊 tip>`；origin 的 `feat/b` 只有 b1、f.txt 與 develop 相同。沒有 plain rebase、沒有衝突。

## 未驗證

- GitHub 自動 retarget 行為、`refs/pull/N/head` fallback、`gh pr edit --base`（本地 bare 無 GitHub）
- PR3 層、parent amend 情境、abandon 流程
