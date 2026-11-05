---
name: audit
description: Whole-repository health audit — weaknesses, optimisation leads, and vulnerable/outdated/unused dependencies — with evidence tiers, fresh-agent triage, and a fixed-format report. Type /nl-audit on a repo you want reviewed end to end.
disable-model-invocation: true
---

# Audit

Audit one repository for weaknesses and optimisation leads, including its dependencies (vulnerable, outdated, unused). Self-contained: no other skill is called; subagents go through the Agent tool; every command and checklist lives in `references/`.

**Core principle:** a finding is a *claim with evidence*. A grep count is a **lead**, not a finding. Coverage is **declared before** the scan, not confessed after it.

## When to use

- User asks for a project health check, 「哪裡可以優化」, 「有什麼弱點」, a tech-debt review, or a dependency audit of a whole repo.
- Not for: a diff or PR (`nl-code-review`), one hard bug (`nl-debug`), a single security-sensitive change (built-in `/security-review`).

## Vocabulary

- **lens** — one audit dimension, run by one subagent: `dependencies`, `security`, `hotspots`, `quality`, `tests-ci`, `build-ops`.
- **evidence tier** — 實證 (ran it, saw the output) / 讀碼 (read the code, did not run) / 推測 (needs someone to confirm).
- **reachability** — whether a vulnerable package sits on a production code path.
- **triage** — a fresh agent scores every finding; nothing enters the report unscored.

## Finding schema (every lens, every finding)

| Field | Rule |
|---|---|
| id | `<lens>-<n>`; the dependencies lens uses `dep-<n>` |
| severity | CRITICAL / HIGH / MEDIUM / LOW, by the lens rule in `references/lens-checklists.md` |
| evidence | 實證 / 讀碼 / 推測. CRITICAL and HIGH need at least 讀碼 |
| location | `file:line` of the **decisive** line, not the trigger line |
| detection | the command run or the code path read |
| recommendation | one concrete change |
| effort | S (<1h) / M (1–4h) / L (>4h) |

## Phase 0 — Scope (main conversation, before any scan)

1. Detect the stack from manifests (`package.json` + lockfile, `pyproject.toml` / `requirements*.txt`, `go.mod`, …). Monorepo → one audit per package, or ask which.
2. Read the project's convention docs: `CLAUDE.md`, `AGENTS.md`, guide-type files under `docs/` (skip records and plans). Read CI and hook config (`.github/workflows/`, `.husky/`, `.pre-commit-config.yaml`).
3. Write the **already-enforced list**: what lint, type-check, and CI already block. Those are never findings.
4. Write the **lens list** and the **out-of-scope list** (typical: runtime profiling, a11y, the deployment layer, anything needing a DB).

*Done when:* stack, already-enforced, lens list, and out-of-scope are written into the report skeleton — before Phase 1 starts.

## Phase 1 — Dependencies (run the commands)

First confirm the installed tree matches the lockfile (`pnpm install --frozen-lockfile --offline` dry check, `pip check`, `go mod verify`); if it does not, say so in the report and name which column reads the lockfile and which reads the installed tree.

Run the three columns in [references/dep-commands.md](references/dep-commands.md) for the detected stack: **vulnerable**, **outdated**, **unused**. Record the command next to each table. "From memory" is not a row.

- Every vulnerable row carries four extra columns: direct?, prod-path?, reachable?, fix version. Transitive **and** unreachable → LOW regardless of CVSS, with a note. Proving "unreachable" may use the project's own build or bundle-analyser script (it writes only to its output directory).
- Unused: tool output is a lead. Confirm each candidate against config files, scripts, and type-only imports before calling it unused.
- Each row worth reporting becomes a `dep-<n>` finding in the schema and goes through Phase 3 like every other finding.

*Done when:* three tables exist, each with its command; every vulnerable row has the four columns; dep findings are in schema.

## Phase 2 — Lenses (parallel subagents)

Dispatch one subagent per remaining lens — `security`, `hotspots`, `quality`, `tests-ci`, `build-ops` — using the prompt in [references/lens-checklists.md](references/lens-checklists.md). Each gets: repo path, stack, already-enforced list, out-of-scope list, its own lens section (pasted, or the file path plus the section heading), and the finding schema. Standard tier for most lenses; most capable tier for `security`. **Always specify the model explicitly.** No Agent tool available (you are already a subagent)? Run the lenses yourself, one at a time, with the same prompt and the same return format — the rules below still hold.

Rules every lens prompt restates:

- **Counts are leads.** To become a finding, sample at least three hits and read them; cite the sampled lines; state the count as an order of magnitude.
- **Read to the decisive line.** A security finding that stops at the trigger (route, decorator, `on:` block) is 推測 and goes to 未驗證, not to weaknesses.
- **Read-only.** No fixes, no commits, no edits inside the repo. Running the project's own scripts (build, analyser, test) into their normal output directories is allowed.
- **A denied read is a gap, not a puzzle.** If the harness refuses a file, list the path under "did not cover"; do not retry through another tool.
- **Cannot ask the user.** Unknowns go to the lens's own "did not cover" list.

*Done when:* every lens returned findings in schema plus its "did not cover" list.

## Phase 3 — Triage (fresh agent)

Dispatch one fresh agent (cheapest tier) per ~10 findings with [references/scoring-rubric.md](references/scoring-rubric.md) verbatim. It scores 0–100 and may lower an evidence tier. **Pre-existing is not a false positive here** — the whole audit is pre-existing code. No Agent tool? Score in a separate pass after all lenses are done, reading only each finding and its cited lines, and write 「triage：自評」 in the run log.

- Score ≥ 50 (verified real) → report under its severity. Score 25–49 → 未驗證 with the reason. Score 0 → dropped, id and reason kept in the run log. Never silently drop.
- CRITICAL or HIGH still tagged 推測 → either a read-only proof (trace the path end to end, or run an isolated snippet outside the repo) or demote to 未驗證.

*Done when:* every finding has a score; the report has zero unscored rows.

## Phase 4 — Report

Fill [references/report-template.md](references/report-template.md) in 繁體中文 and write it to `~/.nl-audit/<repo-name>/<YYYY-MM-DD>.md` — never inside the repo. Print the path. Sort findings by severity, then score. 未涵蓋 holds only the Phase 0 out-of-scope list plus unknowns that surfaced during the run.

*Done when:* the file exists, every section is present, and no finding lacks severity, evidence, or location.

## Rationalization table

| Excuse | Reality |
|---|---|
| "No time to run `pnpm outdated` / `pip-audit`; I know these versions" | Memory is not evidence. The command takes seconds; without it the whole section is 推測. |
| "67 `any` usages — that's a finding" | It is a lead. Sample three, read them, then write the finding with lines. |
| "I read the trigger; the rest is probably fine" | Then it is 未驗證. A weakness needs the decisive line. |
| "Pre-existing, so not worth flagging" | Everything here is pre-existing. Score on evidence, not on age. |
| "Transitive dep with high CVSS → HIGH" | Reachability decides. Unreachable transitive is LOW with a note. |
| "I'll list what I skipped at the end" | Scope is declared in Phase 0. Late additions are fine; a missing Phase 0 list is not. |
| "Scoring is overkill for a small repo" | Self-scoring is the failure mode. Fresh agent, every time. |
| "depcheck says unused, so remove it" | Tool output is a lead. Confirm config, scripts, and type-only imports first. |
| "Static scan is enough for a one-hour review" | Time pressure changes the lens list (declare fewer lenses), never the evidence rule. |

## Red flags — STOP

- A lens started before the Phase 0 lists exist.
- A dependency table row without the command that produced it.
- A finding with a count and no sampled lines.
- A CRITICAL or HIGH tagged 推測 in the final report.
- The report written inside the repo, or not in 繁體中文.
- A finding that the already-enforced list already covers.
- A lens agent that edited or committed anything.

## Integration

- Follow-up per finding: `nl-handle-issue` (fix one), `nl-asana-ticket` (track).
- Diff-scoped review: `nl-code-review`. One hard bug: `nl-debug`.
- Keep the report: `nl-kb` kb-collect.
