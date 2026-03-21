---
name: bq-analysis
description: Use when querying BigQuery, analyzing data, writing SQL for BQ, or when user says "query", "BQ", "BigQuery", "data analysis", "check metrics", "funnel", "retention"
---

# BigQuery Analysis

## Overview

Cost-aware BigQuery workflow. Every query goes through discovery, dry-run, and approval before execution. Never guess schema or partition columns — verify them.

## Execution Flow (MANDATORY order)

```
1. Discover   → project, dataset, table, schema, partition column
2. Draft      → SQL with verified partition filters and column selection
3. Dry-Run    → bq query --dry_run (NEVER skip)
4. Report     → show scan size, cost estimate, wait for approval
5. Execute    → only after user says OK
6. Present    → standardized output format
```

**Skipping steps 1-4 is not allowed.** The baseline failure mode is guessing partition columns and writing SQL before verifying the schema.

## Step 1: Discover

**Before writing ANY SQL, verify these. Do not guess.**

```bash
# Find the right project (check CLAUDE.md or gcloud config)
gcloud config get-value project 2>/dev/null
cat CLAUDE.md 2>/dev/null | grep -i "gcp\|project\|bigquery"

# List datasets in the project
bq ls --project_id=PROJECT

# List tables in a dataset
bq ls PROJECT:DATASET

# Get table schema (column names, types)
bq show --schema --format=prettyjson PROJECT:DATASET.TABLE

# CRITICAL: Check partitioning and clustering — do NOT guess
bq show --format=prettyjson PROJECT:DATASET.TABLE | grep -A5 "partitioning\|clustering"

# Or use INFORMATION_SCHEMA
bq query --use_legacy_sql=false \
  "SELECT column_name, is_partitioning_column, clustering_ordinal_position
   FROM \`PROJECT.DATASET.INFORMATION_SCHEMA.COLUMNS\`
   WHERE table_name = 'TABLE_NAME'"

# Check data freshness
bq query --use_legacy_sql=false \
  "SELECT MAX(partition_column) AS latest_data FROM \`PROJECT.DATASET.TABLE\`
   WHERE partition_column >= CURRENT_DATE() - 7"
```

**Why verify partitions?** Baseline testing showed agents consistently guess partition columns (assuming `event_timestamp` or `created_at`) instead of checking. A wrong partition filter means BQ ignores it and does a full table scan — the exact cost problem we're trying to avoid.

## Step 2: Draft SQL

Rules:
- **Never `SELECT *`** — list specific columns
- **Always filter on the verified partition column** — not a guessed one
- **Add `LIMIT` for exploratory queries** — use `LIMIT 100` until you know the data
- **Use `TABLESAMPLE` for large tables** when exactness isn't needed:

```sql
-- Cheap exploration of a large table
SELECT * FROM `project.dataset.table` TABLESAMPLE SYSTEM (1 PERCENT)
```

## Step 3: Dry-Run (NEVER skip)

```bash
bq query --dry_run --use_legacy_sql=false --project_id=PROJECT "SQL"
```

**This is not optional.** It costs nothing and prevents expensive mistakes.

## Step 4: Report and Wait

**Calculate cost and present to user before executing:**

```
Estimated scan: X.XX GB
Estimated cost: ~$Y.YY ($5/TB on-demand)
```

| Scan Size | Action |
|-----------|--------|
| < 1 GB | Proceed, mention the size |
| 1-10 GB | Show estimate, ask to proceed |
| 10-100 GB | Warn, suggest optimizations |
| > 100 GB | Stop. Redesign query first. |

**Wait for explicit user approval before executing.**

## Step 5: Execute

Only after user confirms.

```bash
bq query --use_legacy_sql=false --project_id=PROJECT "SQL"
```

## Step 6: Present Results (MANDATORY format)

```markdown
### Query Results

**Project:** project-id | **Scanned:** X.XX GB | **Cost:** ~$X.XX | **Rows:** N

| Column A | Column B | Column C |
|----------|----------|----------|
| value    | value    | value    |

**Key Findings:**
- Finding 1
- Finding 2

**Data Freshness:** Latest record is from YYYY-MM-DD
```

## Rationalizations That Lead to Expensive Queries

| Excuse | Reality |
|--------|---------|
| "I'll just guess the partition column" | WRONG. Verify with INFORMATION_SCHEMA or bq show. A wrong filter = full scan. |
| "Dry-run is overkill for a small query" | Dry-run costs zero. There's no query too small to dry-run. |
| "The user wants it fast, I'll skip discovery" | Fast and wrong costs more than slow and right. |
| "SELECT * is fine for exploration" | Use TABLESAMPLE or LIMIT with specific columns instead |
| "I know this table's schema from before" | Schemas change. Verify every time. |
| "The user gave me a query, I'll run it as-is" | You're the safety net. Add partition filter and dry-run even for user-provided queries. |
| "User already told me the table, skip discovery" | Even with a known table, verify partition column and schema. Discovery is not just about finding the table. |
| "INFORMATION_SCHEMA queries cost money too" | INFORMATION_SCHEMA queries are free in BigQuery. Zero bytes scanned. No excuse to skip. |

## Gotchas

| Mistake | Correct Approach |
|---------|------------------|
| Guessing partition columns | Use INFORMATION_SCHEMA or `bq show` to verify |
| Missing partition filter | BQ charges for full table scan without partition pruning |
| Not checking data freshness | Query `MAX(partition_col)` to confirm data is up to date |
| Using legacy SQL | Always `--use_legacy_sql=false` |
| Relying on MEMORY.md for dry-run discipline | Dry-run is part of THIS workflow. Follow it regardless of other instructions. |
| Running user-provided queries without review | Always add safety (partition filter, dry-run) even for direct queries |
