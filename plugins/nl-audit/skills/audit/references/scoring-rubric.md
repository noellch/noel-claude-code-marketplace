# Triage rubric (Phase 3)

Dispatch a fresh agent (cheapest tier) per batch of ~10 findings. Give it the repo path, the already-enforced list, the batch, and this rubric verbatim. It must not see the lens agent's process notes — only the findings.

```
You are triaging audit findings for a repository. For each finding, verify it against the code yourself (read the cited lines and enough surrounding context), then return a score 0–100 and, if needed, a corrected evidence tier. Read-only: change nothing in the repo. You cannot ask the user.

Repo: <absolute path>
Already enforced by lint/type-check/CI: <list>

Scale (apply verbatim):
  0   — False positive. The cited line does not show the issue, the project's convention docs explicitly allow it, or lint/CI already blocks it.
  25  — Might be real, but you could not verify it from the cited lines, and the finding gives no path to verify. Keep as 推測.
  50  — Verified real, but low impact: rarely hit, cosmetic, or already mitigated elsewhere (say where).
  75  — Verified real from the cited lines; impact is plausible in practice; the recommendation is the right shape.
  100 — Verified real; you traced the path or reproduced it read-only; impact is certain.

Rules:
- "Pre-existing" is NOT a reason to lower the score. Every finding in an audit is pre-existing code.
- Severity is not confidence. A LOW finding can score 100; a CRITICAL can score 25.
- If the lens tagged 實證 or 讀碼 but you cannot see it from the cited lines, lower the tier and say what is missing.
- If a CRITICAL/HIGH is 推測 and you can make it 讀碼 by reading one more file, do that and say so.
- Do not add new findings. Do not rewrite recommendations except to flag one that would not fix the issue.

Return ONLY, one block per finding:
  id: <id>
  score: <0-100>
  evidence: <實證|讀碼|推測, corrected if needed>
  reason: <one or two sentences, cite file:line you read>
```

## Applying the scores

| Score | Where it goes |
|---|---|
| ≥ 50 | Report, under its severity (50 = verified real, low impact — still a finding) |
| 25–49 | 未驗證 section, with the triage reason |
| 0 | Dropped; keep the id and reason in the run log at the end of the report |

Dependency rows (`dep-<n>`) are scored like every other finding.

CRITICAL or HIGH still at 推測 after triage → 未驗證, not the weaknesses section.
