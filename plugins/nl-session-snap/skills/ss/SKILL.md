---
name: ss
description: Use when needing to name the current session for easier retrieval, or when searching for a previous session across multiple projects. Triggers on /ss, "rename session", "find session", or "哪個 session".
user-invocable: true
---

# Session Snap (`/ss`)

Name and find Claude Code sessions across all projects.

The helper script `ss.py` is in this skill's base directory. Use its full path when running commands.

## Routing

| Input | Action |
|-------|--------|
| `/ss` | [Rename](#ss--rename-current-session) current session |
| `/ss find <keyword> [--project X] [--since Nd]` | [Search](#ss-find--cross-project-search) sessions |
| `/ss list [count]` | [List](#ss-list--browse-recent) recent sessions |
| Otherwise | Show this command table |

## `/ss` — Rename Current Session

**Step 1.** Collect git context:

```bash
python3 "<skill_base_dir>/ss.py" context
```

Returns JSON with `project`, `branch`, `status`, `recent_commits`.

**Step 2.** Generate a structured name from **conversation context + git info**.

Format: `[project] task description (branch)`

- `project`: from the JSON `project` field, lowercase. If it's a monorepo root (e.g., `co`) and the conversation clearly targets a specific service, use that service name instead
- Task description: what the user is working on **in this conversation**
- If conversation is too early or vague, derive from branch name and recent commits
- Abbreviate branch if over 30 chars; omit `(branch)` entirely if branch is empty
- Total max 80 characters

Examples:

```
[grazioso] richmenu zodios migration (feat/richmenu-zodios)
[rubato] fix segment pagination bug (fix/segment-page)
[dbt-models] add cdh event dedup (feat/cdh-dedup)
```

**Step 3.** Apply: `/rename <generated-name>`

**Step 4.** Confirm:

```
Session renamed: <name>
```

## `/ss find` — Cross-Project Search

```bash
python3 "<skill_base_dir>/ss.py" find <keyword> [--project NAME] [--since Nd]
```

Display output directly. All flags are combinable.

## `/ss list` — Browse Recent

```bash
python3 "<skill_base_dir>/ss.py" list [count]
```

Display output directly. Default count: 10.
