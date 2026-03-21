---
name: bq-analysis
description: Use when querying BigQuery, analyzing data, writing SQL for BQ, or when user says "query", "BQ", "BigQuery", "data analysis", "check metrics", "event data", "funnel", "retention"
---

# BigQuery Analysis

## Overview

Structured BigQuery analysis workflow with mandatory dry-run cost estimation, common query patterns for Crescendo Lab's data infrastructure, and GCP project routing.

## When to Use

- User asks to query or analyze data in BigQuery
- User asks about metrics, funnels, retention, conversions
- User asks to investigate data in MDS, GA, or event tables
- User mentions BigQuery, BQ, or SQL analysis

## MANDATORY: Dry-Run Before Execute

**Every query MUST go through dry-run first. No exceptions.**

```bash
# Step 1: ALWAYS dry-run first
bq query --dry_run --use_legacy_sql=false "SELECT ..."

# Step 2: Report estimated cost to user
# Pricing: $5/TB on-demand
# Show: bytes scanned → GB → estimated cost

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

## GCP Project Routing

**Always specify the correct project based on product and region.**

| Product | Region | Project ID | Common Usage |
|---------|--------|------------|-------------|
| MAAC | TW | `cresclab` | Production MAAC data |
| MAAC | JP | `maac-production` | JP region MAAC data |
| CDH | TW | `cresclab-warehouse` | Data warehouse, dbt models |
| CDH | JP | `jp-cresclab-warehouse` | JP data warehouse |

```bash
# Always specify project explicitly
bq query --project_id=cresclab --use_legacy_sql=false "SELECT ..."
bq query --project_id=cresclab-warehouse --use_legacy_sql=false "SELECT ..."
```

**Routing rules:**
- Raw MAAC data (messages, journeys, users) → `cresclab` or `maac-production`
- Aggregated/modeled data (dbt models) → `cresclab-warehouse` or `jp-cresclab-warehouse`
- When unsure, ask user which product/region

## Common Dataset Paths

### MDS (Message Delivery Service)

```sql
-- MDS events (partitioned by date)
`cresclab.mds_dataset.mds_message_event`

-- Journey node tracking (available from Dec 2025)
-- app_ref_type = 'journey_node_message'
WHERE app_ref_type = 'journey_node_message'
  AND DATE(created_at) BETWEEN @start_date AND @end_date
```

### GA (Google Analytics)

```sql
-- GA events export (partitioned by date, sharded tables)
`cresclab.analytics_PROPERTY_ID.events_*`

-- Use _TABLE_SUFFIX for date filtering on sharded tables
WHERE _TABLE_SUFFIX BETWEEN '20260101' AND '20260131'
```

### dbt Models (Warehouse)

```sql
-- dbt models live in the warehouse project
`cresclab-warehouse.SCHEMA.MODEL_NAME`

-- Check available models
-- Refer to dbt-models/ directory for schema definitions
```

## Query Patterns

### Pattern 1: Date-Partitioned Scan (Cost Optimization)

```sql
-- GOOD: Filter on partition column first
SELECT *
FROM `project.dataset.table`
WHERE DATE(created_at) BETWEEN '2026-01-01' AND '2026-01-31'
  AND status = 'delivered'

-- BAD: No partition filter (full table scan)
SELECT *
FROM `project.dataset.table`
WHERE status = 'delivered'
```

### Pattern 2: Funnel Analysis

```sql
WITH step1 AS (
  SELECT DISTINCT user_id
  FROM `project.dataset.events`
  WHERE event_name = 'message_sent'
    AND DATE(event_time) BETWEEN @start AND @end
),
step2 AS (
  SELECT DISTINCT user_id
  FROM `project.dataset.events`
  WHERE event_name = 'message_delivered'
    AND DATE(event_time) BETWEEN @start AND @end
),
step3 AS (
  SELECT DISTINCT user_id
  FROM `project.dataset.events`
  WHERE event_name = 'message_opened'
    AND DATE(event_time) BETWEEN @start AND @end
)
SELECT
  'sent' AS step,
  COUNT(*) AS users
FROM step1
UNION ALL
SELECT 'delivered', COUNT(*) FROM step2
UNION ALL
SELECT 'opened', COUNT(*) FROM step3
ORDER BY
  CASE step
    WHEN 'sent' THEN 1
    WHEN 'delivered' THEN 2
    WHEN 'opened' THEN 3
  END
```

### Pattern 3: Retention / Cohort

```sql
WITH cohort AS (
  SELECT
    user_id,
    DATE_TRUNC(MIN(first_event_date), WEEK) AS cohort_week
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

### Pattern 4: Journey Node Performance

```sql
-- Compare delivery metrics across journey nodes
SELECT
  journey_id,
  node_id,
  COUNT(*) AS total_sent,
  COUNTIF(status = 'delivered') AS delivered,
  COUNTIF(status = 'opened') AS opened,
  SAFE_DIVIDE(COUNTIF(status = 'delivered'), COUNT(*)) AS delivery_rate,
  SAFE_DIVIDE(COUNTIF(status = 'opened'), COUNTIF(status = 'delivered')) AS open_rate
FROM `cresclab.mds_dataset.mds_message_event`
WHERE app_ref_type = 'journey_node_message'
  AND DATE(created_at) BETWEEN @start AND @end
GROUP BY journey_id, node_id
ORDER BY total_sent DESC
```

## Cost Optimization Checklist

Before executing any query:

- [ ] **Partition filter** — Does the query filter on the partition column (usually `DATE(created_at)` or `_TABLE_SUFFIX`)?
- [ ] **Column selection** — Using `SELECT *`? Replace with specific columns needed
- [ ] **Date range** — Is the date range as narrow as possible?
- [ ] **LIMIT for exploration** — Add `LIMIT 100` for exploratory queries
- [ ] **Dry-run passed** — Did you run `--dry_run` and report the cost?
- [ ] **Correct project** — Using the right GCP project for this data?

## Query Execution Flow

```
1. Clarify Intent     → What question is the user trying to answer?
2. Identify Source    → Which project/dataset/table?
3. Draft Query        → Write SQL with partition filters
4. Dry-Run            → bq query --dry_run (MANDATORY)
5. Report Cost        → Show estimated scan size and cost
6. User Approval      → Wait for explicit OK
7. Execute            → Run the query
8. Present Results    → Format results clearly, highlight key findings
9. Iterate            → Refine based on user feedback
```

## Output Format

After executing a query, present results as:

```markdown
### Query Results

**Scanned:** X.XX GB | **Cost:** ~$X.XX | **Rows:** N

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
| Wrong GCP project | Double-check product/region mapping before querying |
| Querying sharded GA tables without `_TABLE_SUFFIX` | Always use `_TABLE_SUFFIX` filter for `events_*` tables |
| Assuming MDS has data before Dec 2025 | MDS journey node tracking started Dec 2025 |
| Long-running query without LIMIT | For exploration, always add LIMIT first |
| Not specifying `--use_legacy_sql=false` | Always use standard SQL, never legacy SQL |
