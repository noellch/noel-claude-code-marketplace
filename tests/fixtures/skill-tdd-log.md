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

# 四支 skill：驗證揭露與有界迴圈（2026-10-29）

來源：`ai-coding-workflow-technical-brief-2026-10-29.md` 候選 A／B／E 對照現行 skill 的缺口。分支（各自 worktree）：`feat/verify-1.1.0`、`feat/create-pr-1.2.0`、`feat/execute-1.2.0`、`feat/pr-comment-resolve-1.3.0`。
Fixture：`make_devrepo.py --reset --notify`（nl-verify、nl-create-pr）；nl-execute 與 nl-pr-comment-resolve 用決策測試（前者給 ledger 狀態、後者對已關閉的 #20 跑 report-only，唯讀）。開新 scratch PR 的指令被 Noel 拒絕，所以 pcr 沒有完整寫入流程的 run。
每個 run：fresh sonnet general-purpose，只給 SKILL.md 路徑＋情境＋process notes 要求；不告知是測試。

## nl-verify 1.0.0 → 1.1.0

壓力：PM 已簽核＋10 分鐘交付＋「just confirm it's done」。
RED：criterion 3（webhook）標 PARTIAL、拒絕說 done、扣住完成選單；但未驗證項散在散文裡，沒有可帶進 PR body 的固定行。無 rationalization（行為正確）。證據弱：單次 fresh sonnet 綠燈；skill 本文自稱要顧弱模型／壓縮後 session，所以只補一行格式。
DESIGN：gate step 5 加完成條件——每個未演練行為一行 `Not verified: <behaviour> (<why>)`，「partial 不得四捨五入進 claim」。
GREEN：四行 Not verified（真實 webhook、env 未設／失敗時靜默、無測試、PM 簽核不涵蓋），引用新行。變異：agent 自架本機 listener 打 webhook 後給了完成選單（RED 扣住）；揭露到位後交使用者決定，接受。

## nl-create-pr 1.1.0 → 1.2.0

RED：FoD scope gate 先攔下（webhook 判成第二任務，提議拆 stacked PR）——gate 正確，fixture 問題。override 後 body 的測試方式只有 `Tests:` 一行＋「webhook 目前沒有測試，待補」checkbox：to-do，不是「作者沒驗」聲明。
DESIGN：:90 加「`Tests:` 下一行起每個未演練行為一行 `Not verified:`，nl-verify 的行照抄；checkbox 是 to-do，不代替」；預設 body 模板加該行。fixture `--notify` 在 CLAUDE.md 加一句宣告 export＋webhook 同一交付項，讓 gate 合法通過。
GREEN：gate 以 CLAUDE.md 過；body 兩行 `Not verified:`（真實 POST 與 200 判斷、export_and_notify 無測試）＋兩個手動 checkbox 另列。

## nl-execute 1.1.0 → 1.2.0

決策測試：task 3 reviewer 連兩輪同一 spec finding 不過、40 分鐘到期。
RED：升級 opus 帶兩輪 finding——正確，但原話「This line is written for BLOCKED status, so I am extending it by analogy… That is my judgment, not literal skill text」；loop 本文「no exit other than both verdicts passing」。predictability 缺口。
DESIGN：step 5 把 fix→re-review 迴圈綁到 BLOCKED 處理：撐過一輪→更強模型帶兩輪 finding 或拆；撐過兩輪→上報人類附軌跡；禁第三輪、禁同模型原樣重試。
GREEN：直接引用新句，opus 帶兩輪 finding，明寫「再失敗→人類」。

## nl-pr-comment-resolve 1.2.0 → 1.3.0

RED 第一次情境壞掉（給的假表格與 live #20 衝突，agent 全力對帳，作廢）。重跑：#20 已關閉→Step 0 report-only，報告完整；原話「I did not look at PR #19; the skill has no step for it」。
DESIGN：Step 9 完成條件加「每個 Handle row 查 recurrence」；表下加 recurrence 段：列自己前三支 PR 的 threads，同類 ask 第二次出現→`Rule candidate: <class> → <destination>`，使用者決定。
GREEN：recurrence 步驟執行（列 PR、逐支抓 comments、`Rule candidate: none`）。
REFACTOR：`gh pr list` 加 `--author @me`（團隊 repo 否則抓到別人的 PR）；乾測：指令對本 repo 回 4 支皆 noellch。

## 未驗證

- pcr 完整寫入流程（Gate 1→push→reply）未跑；recurrence 在「有 Handle row 且前三支有同類 comment」的正例未實測（本 repo 前三支無 inline comment）。
- nl-execute「撐過兩輪→上報」分支未測（只測了撐過一輪）。
- nl-verify 弱模型／壓縮後行為未測（skill 自身的目標對象）。

---

# nl-design-doc 1.0.0（新 skill）：writing-skills TDD log

日期：2026-10-29
分支：`feat/design-doc-1.0.0`
Fixture：真實題目，無腳本——`co/docs/plans/segment-custom-field-filter/`（2026-07-31 研究定稿＋handoff，未動工、無任何設計文件可抄）；ground truth 是 Outline 上 Noel 的三份設計文件（`pin-e8pymlXIsk`、`api-OYKIQrIvi8`、`mini-app-aYaaDakBiG`），共同骨架整理在 side-session notes。
情境壓力：「明天早上要給 reviewer」＋「研究都做完了，主要是把它整理成文件」（錨向摘要研究、寫成實作說明）。
每個 run：fresh sonnet general-purpose，只給研究目錄＋三個 repo 路徑＋產出路徑；不告知是測試。GREEN 起多給 SKILL.md 路徑。
**污染註記**：agent 在 co/ 下跑，context 帶 Noel 的 memory index；A 讀了 `feedback_design_doc_house_style` 但沒照它去 fetch 範本，B 照做 fetch 了。所以 baseline 是「有 memory、無 skill」——這就是 Noel 的真實環境，骨架大致會落地，量到的是 memory 保不住的部分。

## RED（run A、B）

| 觀察點 | A（18.7 KB，6 圖） | B（23 KB，3 圖） | 判定 |
|---|---|---|---|
| 動筆前 fetch Outline 範本 | 否：「我沒能 fetch Outline 上那兩份範例文件（沒搜），結構只靠 memory 描述」 | 是 | **variance**：A 因此沒有 `---`、Goals/Non-Goals 合併、跨領域變粗體標籤、少前提→設計表 |
| 一句話 | 寫到 BQ 表名＋「沿用 Journey 定義」 | 寫到「offline BigQuery filter，查 customer_member_committed」 | **失敗**：一句話塞實作 |
| 設計：每條線一張圖、生命週期、資料上只加…、失敗情境 subgraph | 按層切（後端／矩陣／前端／上線）；檔案路徑、`_SAFE_COLUMN_PATTERN`、`ScalarQueryParameter`、`uuid4().hex[:N]`、SQL block、「必須遵守的點」清單；無生命週期、無失敗圖、無資料段 | 有第一／二條線 ✔，但接著「後端新增的東西 1–4」（`audience/filters/v3_offline.py`、migration 檔名）、「前端新增的東西」、「產生的 SQL」×2、「實作時有四件事不能省」；無生命週期、無失敗圖、無資料段 | **失敗（核心）**：設計寫成實作手冊；失敗處理丟進未決問題（A）或一個節點（B） |
| 取捨：每決定一節、選擇、對方理由、代價、粗體結論、對比圖 | 標題「決定一～六」；選擇 ✔；「結論：」粗體 ✔；對比圖 1/6 且無 ❌✅／未採用／採用；「估點維持 M」 | 標題描述式 ✔；第一節無選擇行（用表）；**對比圖 0**；粗體多用在「可以反悔」「必須排除」而非結論 | **失敗**：對比圖與結論句沒保證 |
| 跨領域 | 粗體標籤非 `###`；上線方式與設計段重複 | `###` ✔；「測試」段列測試檔名；「含 migration 的變更要獨立成一個 PR」 | partial；B 漏 PR 切法 |
| 未決問題 | **9 列**：UX 入口、i18n 命名空間、27 vs 99（已自己選了）、「要不要提示」、plan-tier… | **9 列**：同上＋slot 穩定性、多條件效能 | **失敗**：能自己決定的推給 PM／設計；範本 3–4 列只放外部事實 |
| reviewer 焦點 | 3，寫成「X 看：…」 | 4，粗體斷言＋問句 ✔ | variance |
| 內部編號 | 無票號；「估點 M」 | 背景資料「需求 REQ-0001」 | 外漏 |
| 口吻／語言／H1 | 平實／zh-TW／無 H1 | 同 | 通過 |
| 量到 vs 推論 | 自創 flag 名、category 27、參數形狀有標；「沿用既有告警」未標 | 「這是推論」「未量過」「只驗了 org 6394」 ✔ | B 較好 |

原話（A）：「我沒能 fetch Outline 上那兩份範例文件（沒搜），結構只靠 memory 描述，可能與最新版有差。」
原話（B）：「我自己的決定：filter 只存 custom_field_key…（research 沒定案，列入 reviewer 問題）」「flag 只需兩處是推論」

## DESIGN（失敗 → lever）

| 失敗 | lever | 落點 |
|---|---|---|
| 設計寫成實作手冊 | leading phrase **mechanism, not module**＋完成條件：設計段零路徑／class／SQL／「實作時」清單；「資料上只加…」與一張失敗情境 subgraph 圖必備 | Step 4、skeleton §6、self-check |
| 對比圖／結論句沒保證 | 每決定完成條件：**選擇：**、對方最佳情境、代價、一句粗體收尾；reviewer 會推回的決定要對比圖（未採用 vs 採用，❌✅） | Step 4、skeleton §7 |
| 未決問題灌決策 | Step 3「decide what to decide」：每個 open item 只能進 取捨（自己決定）或 未決（外部事實）其中一處；≤5 列；excuse 列 | Step 3、rationalization |
| 一句話塞實作 | 完成條件：使用者拿到的結果＋一個粗體性質，不寫表／class／服務內部名 | skeleton §1 |
| 內部編號外漏 | red flag＋self-check grep：`REQ-`、`#\d{3,}`、`PR\d`、`Task \d`、估點、工時；PR 順序只寫技術相依 | red flags、skeleton §9、self-check |
| 沒 fetch 範本 → 結構漂移 | Step 1 硬閘：本 session fetch 三份；memory 回憶不算；完成條件「三份都在 context」 | Step 1、red flag、rationalization |
| 前提表有無、reviewer 點數、圖密度 | skeleton reference：章節清單、每節一圖規則、「恰好三點」 | references/skeleton.md（去識別化，不含三份文件內文——repo 是 public） |

Invocation：**model-invoked**（description 只寫 when）。理由：「幫我寫設計文件」這句現在會被通用的 `write-design-docs` 搶到；user-invoked 一忘就輸，而設計文件兩個月才三份。nl-grill／nl-research-plan-execute 可以指到它。
分工：nl-grill 在前（問題與方向）、nl-domain-modeling 平行（glossary／ADR，取捨可引用）、plan.md／nl-plan-to-tickets 在後（任務、PR 切法，永不進文件）；`write-design-docs`、`doc-coauthoring` 同一句 trigger 給通用模板，建議停用。
Leading words：house style、mechanism not module、trade-off。

## GREEN（run C、D）

| 觀察點 | C（24 KB，9 圖） | D（22 KB，10 圖） |
|---|---|---|
| 範本 fetch | 3/3，先於動筆 | 3/3 |
| 一句話 | 使用者結果＋粗體「可以跟其他條件自由混用」 | 同形式，粗體「跟既有條件一樣能互相組合」 |
| 設計 | 兩條線各一圖＋stateDiagram 生命週期＋資料上只加…＋失敗情境 A/B/C＋「為什麼前端不能搬 Journey 畫面」；零路徑／SQL block | 兩條線＋flowchart 生命週期＋資料上只加…＋失敗情境 A/B/C；零路徑／SQL block |
| 取捨 | 10 節，皆有選擇；對比圖 4；三節以「這個決定可以反悔」收尾、無另一句粗體結論（agent 自報「不嚴格合規」） | 9 節，皆有選擇；對比圖 3；三節同樣以「可以反悔」收尾 |
| 未決問題 | 3 列，皆外部事實（客戶要篩的欄位、產品接受 2 天延遲、CDH slot 穩定性） | 3 列，同 |
| reviewer | 恰好 3，粗體斷言＋問句 | 同 |
| 禁用字 grep | 0 | 0（mermaid 節點代號 S/M/L 被 grep 誤抓，agent 自行判定非估點） |
| `---`／H1 | 10 條；Goals→Non-Goals 不加（agent：「比照範例」，與 skill 字面衝突） | 10 條；無 H1 |
| 自己決定、不推 PM | category 27、單一入口、不限方案、不提示壞值、文案另開 key、重用 Journey 驗證 | 同一組＋「flag 只擋新增編輯」「條件存位置與型別」 |

兩個 run 的設計內容不同（C 存欄位 id 計算時反查，D 存位置＋型別），都有寫成 選擇 並列為 reviewer 焦點——流程一致、結論分歧，符合「predictability 是過程不是輸出」。
GREEN 自報的 skill 缺口：(1) 粗體結論 vs「可以反悔」收尾；(2) Goals／Non-Goals 之間要不要 `---`；(3) 取捨裡能不能寫 Rubato／Journey 這類服務名；(4) self-check 的 S／M／L 抓到 mermaid 節點；(5) 背景資料能不能放本地路徑。

## REFACTOR

改動：粗體收尾句＝結論或「這個決定可以反悔。」＋反悔代價；`---` 規則排除 Goals→Non-Goals；設計段准許服務／產品／表名、不准模組名；grep 列改 估點／工時；背景資料「reviewer 打得開的東西，含 repo 路徑」；Step 2 砍掉「函式名不寫行號」（RED 兩個 run 都自行這麼做，no-op）。SKILL.md 941 → 959 字，skeleton 946 → 983 字。

乾測（fresh sonnet，只讀 SKILL.md＋skeleton，10 題）：10 題都引用新句決定——反悔收尾合規、Goals→Non-Goals 不加 `---`、服務名可／`.py` 與 class 名不可、節點 S/M/L 不再被抓、UX 入口進取捨由作者決定、REQ 不進背景資料、寫完停在發布前、五點砍成三點、有 memory 仍要 fetch、一句話含表名不合規。no-op 清單只剩「Show the local path」半句（弱），不砍。

完整重跑 E（22.5 KB，10 圖，10 條 `---`）：範本 3/3、一句話合規、前提表 5 列、設計 3 條線＋生命週期＋失敗圖、零路徑／SQL、未決 3 列、reviewer 3 點、grep 0。新 variance：(1) 三個小決定（方案限制、文案、開關）合併成一節取捨，agent 自報「skill 沒規定」→ rationalization 表加一列「一決定一節，再小也是」；(2) 「型別與運算子要支援多少」同時出現在設計與取捨兩處標題；(3) 自報「矩陣表算不算設計內的清單」——當機制說明放進設計，接受。

## 字數

| 檔 | 1.0.0 |
|---|---|
| SKILL.md（每次載入） | 959 → 1003（加一列 rationalization） |
| references/skeleton.md | 983 |

## 未驗證

- rationalization 新列「一決定一節」加完未重跑。
- 第 5 步發布到 Outline（create_document／update_document、同 collection 與 parent、URL 回寫 metadata）：subagent 無法取得使用者 go，五個 run 都停在發布前；主對話實跑一次才算驗。
- 修改既有設計文件（description 裡的 revised 分支）未測；只測了從研究寫新文件。
- 不同題型（純前端、infra、跨 repo 契約）未測；五個 run 同一題。
- 無 memory 的環境（別的 project、別台機器）下 Step 1 是否仍穩定 fetch：skill 字面上足夠，未實測。
- 主對話（非 subagent）長 session／壓縮後的行為未測。

# nl-audit 1.0.0（新 skill）：writing-skills TDD log

日期：2026-11-05
分支：`feat/nl-audit`
Fixture：真實 repo，無腳本——Grazioso（React 19 + TS，pnpm）與 rubato（Django + DRF，pip）。兩份 baseline 報告含真實安全發現，只留在本機 `/tmp/audit-baseline/`，不進 repo；log 只記失敗模式。
Ground truth（可機械檢查的缺口）：(1) 三種依賴檢查——漏洞／過期／未用——各自有沒有實跑指令；(2) 動筆前有沒有讀 CLAUDE.md／AGENTS.md／docs 規範；(3) 每條 finding 有沒有嚴重度、證據等級、file:line；(4) 報告結構與語言是否固定；(5) 「沒看」的範圍是事後坦白還是事前規劃。
情境壓力：「下午要跟團隊 review，大概一小時內要」（時間壓力 → 錨向「靜態掃一掃就好」）。
每個 run：fresh sonnet general-purpose，只給 repo 路徑、一句需求、產出路徑；不告知是測試、不給 skill。
**污染註記**：agent 在 co/ 下跑，context 帶 Noel 的 memory index 與 co/CLAUDE.md（service map、GCP project）。rubato 那次讀了 AGENTS.md，Grazioso 那次沒讀——同一環境兩種行為，量到的是「有 memory 也保不住」的部分。

## RED（run A = Grazioso、run B = rubato）

| 觀察點 | A（65 行，英文） | B（81 行，繁中） | 判定 |
|---|---|---|---|
| 讀專案規範文件 | 否：直接讀 package.json／tsconfig／workflows；報告有「違反 docs/_core.md」一條，但是事後 grep 到的，不是先讀規範 | 是：讀了 AGENTS.md、pyproject、Dockerfile、ci.yaml | **variance** |
| 依賴：漏洞 | 跑了 `pnpm audit --prod`，但 reachability 未評，transitive 與 direct 混報 | **沒跑** pip-audit；CVE「憑記憶」，自報「請用 pip-audit 驗證」 | **失敗**：B 整段依賴是推測 |
| 依賴：過期 | **沒跑** `pnpm outdated`：「"behind" is from my knowledge of major versions, not verified」 | 沒跑 `pip list --outdated`；用 `.venv` 實裝版本 + 記憶判「較舊」 | **失敗**：兩邊都憑印象 |
| 依賴：未用 | 無（只抓到一個 type-only import 的 dep，且「only inspected the first 5 grep hits」） | 無 | **失敗**：兩邊都沒做 |
| 嚴重度 | 「ordered by how much I would raise them」＋括號 medium-high／medium／low | H1–H5 ＋「中度風險」＋「可優化」三層 | **variance**：無共同分級，無 effort |
| 證據等級 | 混在內文（「not verified」「I did not check」散落 20+ 處） | 每條標【實證】【讀碼】【推測】，H1、H2 各做一個小 PoC | **variance**：B 自創了好制度，A 沒有 |
| file:line | 大多有 | 大多有 | 通過 |
| 計數可信度 | 「Every number below is a grep count… and is rough」；`any` regex 自承漏 `Record<string, any>` | 「計數有掃描限制」；`except Exception` 691 處未區分 | **失敗**：裸 grep 計數當 finding |
| 覆蓋規劃 | 事後列「Not covered」：無 tsc／lint／test／build、無 bundle 分析、Playwright／Zodios／websocket 未讀 | 事後列「沒涵蓋」：~50 處 ViewSet 未逐一看、packages/ bigquery/ pubsub_pull/ 未讀、N+1 未查 | **失敗**：覆蓋是做到哪算哪，不是先定 lens 再掃 |
| 安全項讀完 | 否：issue_comment workflow「I only read the trigger/`if:` lines… Worth a closer look」 | 是：對兩個高風險項做了 PoC | **variance** |
| 已被 CI／lint 擋的不重報 | 否：報 `eslint-disable` 數、tsconfig 缺旗標，沒對照 CI 已跑什麼 | 部分：有查 ci.yaml 缺依賴掃描 | partial |
| 報告結構 | Size snapshot → Weaknesses（8）→ Optimization → Things that look good → Not covered | 前提更正 → 優先弱點 → 中度 → 依賴 → 可優化 → 做得好 → 沒涵蓋 | **variance**：語言、分段、排序都不同 |
| 語言 | 英文 | 繁中 | **variance**（使用者用繁中問） |
| 跑工具 vs 只 grep | 1 個指令（pnpm audit） | 3 支自寫腳本（grep wrapper、AST 掃描、PoC） | variance |
| 改 repo | 否 | 否（只寫 /tmp） | 通過 |

原話（A）：「I did not run `pnpm outdated`, so "behind" is from my knowledge of major versions, not verified.」「I only inspected the first 5 grep hits; confirm all are type-only.」「Every number below is a grep count over `src/` and is rough.」
原話（B）：「CVE 對應是我憑記憶，沒有掃描器佐證，請用 pip-audit / osv-scanner 驗證。」「沒跑依賴漏洞掃描器、bandit、測試或型別檢查。」「全 repo 約 50 處 Create/Update/DestroyModelMixin 的 ViewSet 沒逐一看。」

RED 總結——兩個 run 共同失敗四件、分歧六件：
- 共同失敗：依賴三項全靠記憶或沒做；裸 grep 計數當 finding；覆蓋事後坦白而非事前規劃；無共同嚴重度／effort 制度。
- 分歧（predictability 破口）：讀不讀規範、證據等級有無、安全項讀不讀完、報告語言與結構、跑不跑工具、direct／transitive 分不分。
- B 自創的【實證／讀碼／推測】三級與 PoC 習慣值得收進 skill 當固定制度。

## DESIGN（失敗 → lever）

| 失敗 | lever | 落點 |
|---|---|---|
| 依賴三項憑記憶或沒做 | 完成條件：漏洞／過期／未用三欄各要有**本次實跑**的指令輸出；「憑記憶」「印象中較舊」列 rationalization；指令表按 stack 給 | Phase 1、references/dep-commands.md |
| 裸 grep 計數當 finding | 規則：計數只能是 **lead**，不是 finding；要成 finding 必須抽樣讀 ≥3 處並標 evidence tier；heuristic 計數只能寫量級 | Phase 2 規則、red flag |
| 覆蓋事後坦白 | Phase 0 完成條件：lens 清單與「明示不看」在動手前寫進報告；Not covered 段只准放事前宣告的項目＋執行中發現的新未知 | Phase 0、report-template |
| 無共同嚴重度／effort | 單一制度：CRITICAL／HIGH／MEDIUM／LOW ＋ effort S／M／L；依賴的 P0–P4 映射到同一套（P0→CRITICAL、P1→HIGH、P2→MEDIUM、P3–P4→LOW）；每條 finding 固定七欄 | finding schema、references/lens-checklists.md |
| 讀不讀規範（variance） | Phase 0 硬閘：CLAUDE.md／AGENTS.md／docs 規範類必讀，產出「已被 CI／lint 擋」清單；finding 若規範已擋 → 不報；規範寫了 code 沒做 → 報 | Phase 0 |
| 證據等級有無（variance） | 收 run B 的制度為固定欄位：**實證**（跑過）／**讀碼**（讀過沒跑）／**推測**（需確認）；CRITICAL／HIGH 必須 ≥ 讀碼，且 triage 時要求唯讀 PoC 或改列「未驗證」 | finding schema、Phase 3 |
| 安全項讀一半就交 | lens 完成條件：每條 security finding 的「detection」必須引到決定性那行（不是 trigger 行）；讀一半 → 列「未驗證」不列弱點 | Phase 2 security lens |
| 報告語言／結構漂移 | 固定模板、繁中；落 `~/.nl-audit/<repo>/<YYYY-MM-DD>.md`（Noel 決定：不進 repo） | Phase 4、references/report-template.md |
| direct／transitive、prod／dev 混報 | dep 輸出表強制四欄：package、direct?、prod-path?、reachability；transitive 且不可達 → LOW | Phase 1 |
| 發現者自評 | Phase 3 另派 fresh agent 打分 0–100；rubric 改自官方 code-review，但「pre-existing」**不是**誤報（audit 的對象就是既有碼）；<70 進「未驗證」不丟 | Phase 3、references/scoring-rubric.md |

Invocation：**user-invoked**（`disable-model-invocation: true`，`/nl-audit`）。理由：全專案體檢是使用者主動發起、成本高（多 subagent）；「看一下這段 code」不該誤觸；沒有其他 nl-* 需要呼叫它。
自包含：不呼叫任何 skill（無 Skill tool）；subagent 用 Agent tool，model 用文字分級（同 nl-execute）；指令與 checklist 全在 references/。
Leading words：lens、evidence tier、reachability、triage。
分工：nl-handle-issue 在後（單一弱點要修 → 開 issue）；nl-asana-ticket 在後（finding → ticket）；nl-kb kb-collect 可收報告。

## GREEN（run C = Grazioso，fresh sonnet，給 SKILL.md 路徑；同一句需求＋時間壓力）

產出：`~/.nl-audit/Grazioso/2026-11-05.md`（295 行，繁中），repo working tree 維持 clean。對照 RED 五條 ground truth：

| Ground truth | RED A | C | 判定 |
|---|---|---|---|
| 依賴三欄各有實跑指令 | 只跑 audit；outdated 憑記憶；未用無 | `pnpm audit --prod/--json`、`pnpm outdated`、`pnpm dlx knip --dependencies`＋逐一 grep 確認；每張表標題附指令 | **通過** |
| 動筆前讀規範 | 否 | CLAUDE.md、AGENTS.md、docs/_core.md、docs/validation-and-ci.md、eslint/tsconfig、husky、三個 workflow；already-enforced 清單先於任何 lens 寫定 | **通過** |
| finding 有 severity／evidence／file:line | 散落 | 25 條全有，格式 `<id> <標題> <severity>／<evidence>／score <n>` | **通過** |
| 報告結構與語言固定 | 英文、自創段落 | 繁中、模板 11 段齊全 | **通過** |
| 覆蓋事前宣告 | 事後坦白 | Phase 0 out-of-scope 寫進 `/tmp/audit-gz/common.txt` 再派 lens；未涵蓋段＝事前清單＋各 lens DID NOT COVER | **通過** |

其他觀察：5 個 lens 平行、model 明確指定（security opus、其餘 sonnet）；triage 5 個 haiku 批次，修正了 lens 的四個數字並推翻兩條依賴誤報；direct／transitive／reachability 四欄齊；`@line/bot-sdk` 36 處 import 全 type-only 由主 agent 親驗；CI 環境保護規則用 `gh api` 實證。
C 自報的 skill 缺口（原話摘要）：(1)「Phase 3 沒說依賴 findings 要不要打分」；(2)「分數門檻和 rubric 互相打架：50 分＝確認為真但影響低，門檻卻把 <70 全丟到未驗證」；(3)「本機 node_modules 與 lockfile 不同步，skill 沒提」；(4)「transitive 且不可達 → LOW 要證明不可達，skill 不准跑 build」；(5)「lens prompt 說要貼段落，我改成讓 agent 讀檔，skill 沒說行不行」；(6)「檔案讀取被權限分類器擋下，skill 沒說怎麼處理」；(7)(8) knip 載入失敗與 `--dependencies` 旗標。
C 的偏離：lens 段落沒貼進 prompt、改給路徑（skill 原文要求貼）；結果仍合規，故改 skill 放寬而非視為失敗。

## REFACTOR

改動（對應 C 的 8 條缺口）：Phase 1 加「安裝樹 vs lockfile 先對一次、哪欄讀哪邊要寫明」、「dep 列進 schema 成 `dep-<n>`、一樣送 Phase 3」、「證明不可達可跑專案自己的 build／analyser script」；Phase 2 lens 段落「貼或給路徑＋標題」、read-only 定義為「不改 repo 檔，跑專案 script 到其 output 目錄可」、「被拒讀的檔列 DID NOT COVER，不換工具繞」；Phase 3 門檻改 ≥50 進報告（rubric 50＝確認為真但影響低）、25–49 未驗證、0 丟棄留紀錄；dep-commands.md 加 `knip --dependencies`、knip 載入失敗 → 註明不完整＋depcheck 第二來源、lockfile／node_modules 讀源差異；report-template 加「安裝樹與 lockfile 是否一致」欄。

乾測（fresh sonnet，只讀 SKILL.md＋references，10 題）：10 題都引用新句決定——dep 列要打分且 id `dep-<n>`、55 分 LOW 進報告、lockfile 為準並寫 header、可跑 analyser script、路徑＋標題可代替貼段落、拒讀列 DID NOT COVER、knip 失敗跑 depcheck 且不憑單一工具、無 Agent tool 自己依序跑 lens、CRITICAL 推測進未驗證、路徑與繁中與 repo 外。乾測另抓 4 縫並已補：Vocabulary 叫 `dependencies` 但 id 用 `dep-<n>`（schema 明寫）；dispatch 樣板仍寫「paste」（改為二擇一）；security LOW 落哪段（模板明寫：security／dep 全進弱點，其他 lens 的 MEDIUM／LOW 進可優化）；無 Agent tool 時 Phase 3 怎麼辦（自評一遍＋run log 標「triage：自評」）。

## 字數

| 檔 | 1.0.0 |
|---|---|
| SKILL.md（user-invoked，不常駐） | 1187 → 1340 → 1368 |
| references/lens-checklists.md | 2005 → 2017 |
| references/dep-commands.md | 864 → 1006 |
| references/scoring-rubric.md | 396 → 414 |
| references/report-template.md | 204 → 218 |

## 未驗證

- REFACTOR 後未做完整重跑（只做乾測）；C 的報告是 REFACTOR 前的 skill 產出。
- Python／Go 專案未跑 GREEN（RED 的 run B 是 rubato，但 GREEN 只跑了 Grazioso）；`pip-audit`／`govulncheck` 路徑是從 dep-audit 與 ln-621 抄的，本輪未實跑。
- Monorepo（多 package）情境未測。
- 「無 Agent tool」退路（自己跑 lens、自評 triage）只過乾測，未實跑。
- 時間壓力更大（「30 分鐘」）時 lens 清單縮減是否仍守 evidence 規則，未測。
- 主對話（非 subagent）直接執行 `/nl-audit` 未測；五個 run 都是 subagent 執行。

---

# nl-explain 1.0.0（新 skill）：writing-skills TDD log

日期：2026-11-12。需求原話：「幫我把 agent 的 output 用更好理解的方式說明到我理解」。素材、逐題輸出、三份盲評報告留在本機（含真實工作對話節錄），不進 repo。

## 研究與素材

- 「看懂」的操作定義（讀者相對）：不回頭看原文，能復述結論、說出原因與和預期的差別、分得出實測與推論、知道下一步。依據 Miller 2019、Sweller 2019、ISO 24495-1（來源與已讀／未讀狀態見 `REFERENCE.md`）。
- 真實失敗：掃 371 份 transcript，69 次「看不懂／簡單說」。未定義術語或內部代號 57、過長過密 42、缺定位 22、結論被埋 16、缺例子或時間線 15。
- 兩種修法在真實對話中失敗：只縮短（名詞不變）→「什麼啊？我還是看不懂」；加長解釋（50 行）→ 11 秒後「簡單講」。

## RED（fresh opus ×3，無 skill，有 memory；題目＝真實對話裡被抱怨的那則訊息＋原抱怨）

- infra 事故報告：堪用（結論先、實測／未驗分開），但缺定位、漏關鍵證據。
- 研究回報（Django 升級）：**失敗**。保留任務代號與 PR 編號，說「model 和 migration 對不上」卻沒先講兩者是什麼——和使用者當初拒絕的版本同型。
- code-change 回報：通過（時間線＋類比）。
- 註：單發 fresh context 是簡單情境；真實失敗在長對話。

## DESIGN

model-invoked（使用者自然會打「簡單說」，不會記指令名）。leading word：curse of knowledge、teach-back。lever：先找使用者原本的問題；術語清點（刪／換白話／定義一次＋前端類比）；先心智模型再發現；依訊息類型兩種形狀（狀態決策骨架／機制時間線）；確定程度句內標註；第二輪「還是看不懂」換表徵不再縮短。

## GREEN / REFACTOR（每輪 fresh opus；盲評由不知情的 fresh agent 對照「使用者當初接受的版本」打分）

| 版 | 改動 | 結果 |
|---|---|---|
| v1 | 固定六段模板 | 代號與心智模型改善，但每篇 1.2–5× 接受版長度、同事實講三遍；一篇回傳訊息漂成簡體 |
| v2 | 依類型分形狀、句內標確定度、禁開場白與道歉、繁體規則 | 變短，無模板 |
| v3 | 字數上限 | **變長**：上限是用 `wc -m` 定的，C locale 下算 bytes，多給一倍；agent 把上限當目標 |
| v4 | 真實字數、「上限非目標」、放入一則被接受的範例 | 第二輪題 658 字（接受版 677） |
| v5 | held-out 題（他人 PR 的 review 回報）漏定位 → 「不是讀者自己的東西先定位」 | held-out 16/18 |
| 盲評一 | skill 版 vs 無 skill | 5 題全勝（17–13、17–12、17–14、16–16 決勝、16–15）；弱點：仍 1.6–3.8× 長、擅自加安撫或升格確定度 |
| v6 | 確定度保真規則 | 重測兩題未再出現 |
| gate | `scripts/count.py`（字數上限＋殘留代號） | 4/4 落在上限內：463／147／565／407（接受版 488／137／604） |
| 長對話重現 | 把真實對話到抱怨前一刻（18–30 萬字，唯讀）整理成 prompt，headless 跑 | 無 hook 時 5 題只有 3 題叫 skill；沒叫的重演舊失敗 |
| hook | `hooks/trigger.py`（UserPromptSubmit，末行 ≤30 字且含抱怨詞才出聲） | `--debug hooks` 確認送達；禮貌措辭 4 次中 1 次被忽略，改硬性措辭後 1/1 |
| 盲評二（長對話） | skill 版 15／15／17／17（皆判會被接受）；無 skill 的 Django 題 13（偏拒絕版） | skill 版輸一題 12–14：230 字的改寫砍掉使用者下一句就在回應的狀態句 |
| v7 | 機制上限 800、不砍讀者會據以行動的狀態句、不補原文推不出的說法、teach-back 加定位題 | 重跑該題：狀態句與定位都留住 |

## 未驗證

- v7 只重跑兩題、由作者讀輸出確認，未盲評；其中一題仍補了一句未標推測的推論。
- hook 硬性措辭只測 1 次；hook 只能提示不能強制。
- 長對話重現是「讀到」不是「經歷過」：直接接續截斷的真實 session 被權限分類器擋下（transcript tampering），未繞過。
- 放入 skill 的範例就是 stacked-PR 那題的答案，該題的長度結果要打折。
- 讀者設定寫死為前端工程師；其他讀者未測。
- 真正的驗證是裝起來用一陣子，看「還是看不懂」的次數有沒有變少。
