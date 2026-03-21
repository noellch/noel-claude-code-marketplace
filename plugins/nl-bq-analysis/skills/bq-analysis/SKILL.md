---
name: bq-analysis
description: Use when querying BigQuery, analyzing data, writing SQL for BQ, or when user says "query", "BQ", "BigQuery", "data analysis", "check metrics", "event data", "funnel", "retention"
---

# BigQuery Analysis

## Overview

Structured BigQuery analysis workflow with mandatory dry-run cost estimation, reusable query patterns, and cost-aware execution. Works with any GCP project — reads project-specific configuration from the codebase's CLAUDE.md.

## When to Use

- User asks to query or analyze data in BigQuery
- User asks about metrics, funnels, retention, conversions
- User asks to investigate event data or table contents
- User mentions BigQuery, BQ, or SQL analysis

## MANDATORY: Dry-Run Before Execute

**Every query MUST go through dry-run first. No exceptions.**

```bash
# Step 1: ALWAYS dry-run first
bq query --dry_run --use_legacy_sql=false --project_id=PROJECT "SELECT ..."

# Step 2: Report estimated cost to user
# Pricing: $5/TB on-demand (adjust if user has flat-rate pricing)
# Show: bytes scanned -> GB -> estimated cost

# Step 3: Wait for user approval before executing
# Only proceed after user confirms
```

**Cost thresholds:**

| Estimated Scan | Action |
|---------------|--------|
| < 1 GB | Proceed (mention scan size) |
| 1-10 GB | Show cost estimate, ask to proceed |
| 10-100 GB | Warn, suggest optimizations (partitions, LIMIT) |
| > 100 GB | Stop. Discuss query design before proceeding |

## Project Discovery

**Do NOT hard-code project IDs. Discover them from context.**

1. **Check CLAUDE.md** — Look for GCP project mappings, dataset paths, or environment tables
2. **Check environment** — `gcloud config get-value project` for default project
3. **Check existing queries** — Search codebase for `bq query` or BigQuery client usage to find project/dataset patterns
4. **Ask the user** — If no project context is available, ask before assuming

```bash
# Discover default project
gcloud config get-value project 2>/dev/null

# List available datasets in a project
bq ls --project_id=PROJECT

# List tables in a dataset
bq ls PROJECT:DATASET

# Get table schema
bq show --schema --format=prettyjson PROJECT:DATASET.TABLE
```

**Always specify `--project_id` explicitly in queries.** Never rely on implicit defaults for analysis work.

## Query Patterns

### Pattern 1: Date-Partitioned Scan (Cost Optimization)

```sql
-- GOOD: Filter on partition column first to minimize scan
SELECT col_a, col_b
FROM `project.dataset.table`
WHERE DATE(created_at) BETWEEN '2026-01-01' AND '2026-01-31'
  AND status = 'delivered'

-- BAD: No partition filter (full table scan = expensive)
SELECT *
FROM `project.dataset.table`
WHERE status = 'delivered'
```

### Pattern 2: Sharded Table Access (GA4 Export, etc.)

```sql
-- Sharded tables use wildcard + _TABLE_SUFFIX
SELECT
  event_name,
  COUNT(*) AS event_count
FROM `project.analytics_PROPERTY_ID.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260101' AND '20260131'
GROUP BY event_name
ORDER BY event_count DESC
```

### Pattern 3: Funnel Analysis

```sql
-- Generic multi-step funnel with configurable event names
WITH events AS (
  SELECT
    user_id,
    event_name,
    event_timestamp
  FROM `project.dataset.events`
  WHERE DATE(event_timestamp) BETWEEN @start AND @end
    AND event_name IN ('step_1_event', 'step_2_event', 'step_3_event')
),
funnel AS (
  SELECT
    user_id,
    MAX(IF(event_name = 'step_1_event', 1, 0)) AS reached_step1,
    MAX(IF(event_name = 'step_2_event', 1, 0)) AS reached_step2,
    MAX(IF(event_name = 'step_3_event', 1, 0)) AS reached_step3
  FROM events
  GROUP BY user_id
)
SELECT
  COUNT(*) AS total_users,
  COUNTIF(reached_step1 = 1) AS step1,
  COUNTIF(reached_step2 = 1) AS step2,
  COUNTIF(reached_step3 = 1) AS step3,
  SAFE_DIVIDE(COUNTIF(reached_step2 = 1), COUNTIF(reached_step1 = 1)) AS step1_to_2_rate,
  SAFE_DIVIDE(COUNTIF(reached_step3 = 1), COUNTIF(reached_step2 = 1)) AS step2_to_3_rate
FROM funnel
```

### Pattern 4: Retention / Cohort

```sql
WITH cohort AS (
  SELECT
    user_id,
    DATE_TRUNC(MIN(DATE(first_event_time)), WEEK) AS cohort_week
  FROM `project.dataset.user_events`
  GROUP BY user_id
),
activity AS (
  SELECT
    user_id,
    DATE_TRUNC(DATE(event_time), WEEK) AS activity_week
  FROM `project.dataset.events`
  WHERE DATE(event_time) BETWEEN @start AND @end
)
SELECT
  c.cohort_week,
  DATE_DIFF(a.activity_week, c.cohort_week, WEEK) AS weeks_since_cohort,
  COUNT(DISTINCT a.user_id) AS active_users
FROM cohort c
JOIN activity a USING (user_id)
GROUP BY 1, 2
ORDER BY 1, 2
```

### Pattern 5: Table Profiling (Explore Unknown Tables)

```sql
-- Quick profile: row count, date range, null rates
SELECT
  COUNT(*) AS total_rows,
  MIN(created_at) AS earliest,
  MAX(created_at) AS latest,
  COUNTIF(user_id IS NULL) / COUNT(*) AS null_rate_user_id,
  COUNT(DISTINCT user_id) AS unique_users,
  APPROX_COUNT_DISTINCT(event_name) AS approx_event_types
FROM `project.dataset.table`
WHERE DATE(created_at) BETWEEN @start AND @end
```

### Pattern 6: Cost-Efficient Sampling

```sql
-- Use TABLESAMPLE for large tables when exactness isn't needed
SELECT *
FROM `project.dataset.large_table` TABLESAMPLE SYSTEM (1 PERCENT)

-- Or use LIMIT with a partition filter for cheap exploration
SELECT *
FROM `project.dataset.table`
WHERE DATE(created_at) = CURRENT_DATE()
LIMIT 100
```

## Cost Optimization Checklist

Before executing any query:

- [ ] **Partition filter** — Does the query filter on the partition column?
- [ ] **Column selection** — Replace `SELECT *` with specific columns
- [ ] **Date range** — Is the range as narrow as possible?
- [ ] **LIMIT for exploration** — Add `LIMIT` for exploratory queries
- [ ] **Dry-run passed** — Did you run `--dry_run` and report the cost?
- [ ] **Correct project** — Using the right GCP project for this data?
- [ ] **TABLESAMPLE** — For large tables where approximation is acceptable

## Query Execution Flow

```
1. Clarify Intent     -> What question is the user trying to answer?
2. Discover Context   -> Read CLAUDE.md, check gcloud config, find project/dataset
3. Explore Schema     -> bq show --schema to understand table structure
4. Draft Query        -> Write SQL with partition filters and column selection
5. Dry-Run            -> bq query --dry_run (MANDATORY)
6. Report Cost        -> Show estimated scan size and cost
7. User Approval      -> Wait for explicit OK
8. Execute            -> Run the query
9. Present Results    -> Format clearly, highlight key findings
10. Iterate           -> Refine based on user feedback
```

## Output Format

After executing a query, present results as:

```markdown
### Query Results

**Project:** project-id | **Scanned:** X.XX GB | **Cost:** ~$X.XX | **Rows:** N

| Column A | Column B | Column C |
|----------|----------|----------|
| value    | value    | value    |

**Key Findings:**
- Finding 1
- Finding 2
```

## Gotchas

| Mistake | Correct Approach |
|---------|------------------|
| Running query without dry-run | ALWAYS dry-run first. This is non-negotiable |
| Using `SELECT *` on wide tables | Select only needed columns to reduce scan cost |
| Missing partition filter | BQ charges for full table scan without partition pruning |
| Hard-coding project IDs | Discover from CLAUDE.md, gcloud config, or ask user |
| Querying sharded tables without `_TABLE_SUFFIX` | Always use `_TABLE_SUFFIX` filter for wildcard tables |
| Long-running query without LIMIT | For exploration, always add LIMIT first |
| Not specifying `--use_legacy_sql=false` | Always use standard SQL, never legacy SQL |
| Assuming column names | Run `bq show --schema` first to verify actual column names |
| Ignoring `INFORMATION_SCHEMA` | Use it to discover partitioning, clustering, and table metadata |
