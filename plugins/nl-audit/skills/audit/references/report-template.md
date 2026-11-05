# Report template (Phase 4)

Write in 繁體中文 to `~/.nl-audit/<repo-name>/<YYYY-MM-DD>.md`. Keep every section, even if it only says 無. Findings tables sort by severity then score.

```markdown
# <repo> 體檢報告（<YYYY-MM-DD>）

## 範圍與方法
- 分支／commit：
- Stack：
- 讀過的規範文件：
- Lens：
- 事前排除（未涵蓋）：
- 方法：Phase 1 指令實跑；Phase 2 各 lens 一個 subagent；Phase 3 fresh agent 打分（≥50 進報告，25–49 未驗證）
- 安裝樹與 lockfile 是否一致：

## 已被 lint／type-check／CI 擋下（不重報）
- …

## 摘要
| 嚴重度 | 數量 |
|---|---|
| CRITICAL | |
| HIGH | |
| MEDIUM | |
| LOW | |

三句話：最該先做的一件事、最大的系統性風險、整體健康印象。

## 依賴
### 漏洞（指令：`…`）
| package | version | direct? | prod-path? | reachable? | fix | severity | score |
### 過期（指令：`…`）
| package | current | latest | 類型（major/minor/patch） | severity |
### 未用（指令：`…`，已逐一確認）
| package | 確認方式 | severity |

## 弱點
security 與 dep 的所有 finding（不分 severity），加上其他 lens 的 CRITICAL／HIGH。每條：
### <id> <標題>　<severity>／<evidence>／score <n>
- 位置：`file:line`
- 偵測：
- 問題：
- 建議：
- 工時：S／M／L

## 可優化
同上格式：hotspots／quality／tests-ci／build-ops 的 MEDIUM／LOW。

## 做得好的地方
- …（附 file:line）

## 未驗證
score 25–49、或 CRITICAL／HIGH 仍為 推測 的項目；每條附 triage 理由與「要怎麼驗」。

## 未涵蓋
Phase 0 事前排除清單＋執行中新冒出的未知（各 lens 的 DID NOT COVER 合併）。

## 下一步
1–5 條，按 severity × effort 排序；每條指到一個 finding id。

## 執行紀錄
- 各 lens 使用的 model、回傳 finding 數
- score < 25 被丟棄的 id 與理由
```
