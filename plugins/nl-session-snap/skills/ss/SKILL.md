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
| `/ss copy <id-prefix>` | [Copy](#ss-copy--clipboard-resume) resume command to clipboard |
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

**Step 3.** Apply the name via ss.py (writes custom-title to .jsonl + sessions-index.json so it persists in `/resume`):

```bash
python3 "<skill_base_dir>/ss.py" rename "<generated-name>"
```

This auto-detects the current session. No user action required.

**Step 4.** Confirm with the script output (shows session ID and name).

## `/ss find` — Cross-Project Search

```bash
python3 "<skill_base_dir>/ss.py" find <keyword> [--project NAME] [--since Nd]
```

Copy the script output into your text response as a fenced code block so it is fully visible to the user (tool output may be collapsed by the UI). All flags are combinable.

## `/ss list` — Browse Recent

```bash
python3 "<skill_base_dir>/ss.py" list [count]
```

Copy the script output into your text response as a fenced code block. Default count: 10.

## `/ss copy` — Clipboard Resume

```bash
python3 "<skill_base_dir>/ss.py" copy <session-id-prefix>
```

Copies `claude --resume <full-id>` to the system clipboard. User can then paste in a new terminal to resume.
