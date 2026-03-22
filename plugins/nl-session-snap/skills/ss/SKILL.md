---
name: ss
description: Use when user wants to save, find, or resume Claude Code sessions. Triggers on "save session", "find session", "resume session", "哪個 session", "上次做到哪", or /ss command with save/list/find/resume/del/tidy args.
user-invocable: true
---

# Session Snap (`/ss`)

Save, find, and resume Claude Code sessions across projects. Enriches Claude Code's native session tracking with curated names, todos, next-action notes, and optional claude-mem integration.

## Sub-Command Routing

Parse the user's input after `/ss` to determine which command to run:

| Input | Route |
|-------|-------|
| `/ss` (no args) | Show help |
| `/ss help` | Show help |
| `/ss save [note]` | [Save command](#ss-save) |
| `/ss list [count]` | [List command](#ss-list) |
| `/ss find <query> [--project X] [--since Nd]` | [Find command](#ss-find) |
| `/ss resume <target> [--switch]` | [Resume command](#ss-resume) |
| `/ss del <target>` | [Delete command](#ss-del) |
| `/ss tidy [--since Nd]` | [Tidy command](#ss-tidy) |

If the command is not recognized, show help.

## Help Output

When no args, unknown command, or `/ss help`, display:

```
Session Snap — save, find, and resume sessions

Usage: /ss <command> [args]

Commands:
  save  [note]                        Save current session with enrichment data
  list  [count]                       List recent sessions across all projects (default: 10)
  find  <query> [--project X] [--since Nd]  Search sessions by keyword
  resume <target> [--switch]          Show resume context (--switch to open)
  del   <target>                      Delete enrichment for a session
  tidy  [--since Nd]                  Batch rename unnamed sessions

<target> can be a session ID, autoName substring, or list index (#1, #2…)
```

## /ss save

**Purpose:** Snapshot the current session with a curated name, todos, and next action.

Follow these steps exactly:

### Step 1 — Collect context

Run these shell commands to gather context (run them in parallel where possible):

```bash
git branch --show-current
```
```bash
git status --short
```
```bash
git log --oneline -3
```

Also determine:
- **Project name**: basename of the current working directory (e.g., `Grazioso` from `/Users/noel/Crescendolab/co/Grazioso`), lowercased for the auto-name.
- **Session ID**: Obtain from the current conversation context. If not directly available, find the most recently modified `.jsonl` file under the current project's session directory.
- **User note**: If the user provided text after `save` (e.g., `/ss save halfway through migration`), capture it as `userNote`. Otherwise set to `null`.

### Step 2 — Generate session name

Format: `[project-lowercase] short task description`

Examples:
- `[grazioso] richmenu zodios migration`
- `[rubato] fix audience segment pagination`
- `[dbt-models] add cdh event dedup model`

Derive the task description from what the user has been working on in this conversation. Keep it under 60 characters total.

### Step 3 — Rename the native session

Execute the `/rename` command to update Claude Code's built-in session name:

```
/rename <generated-name>
```

### Step 4 — AI-generate todos and next action

Review the full conversation and identify:
- **todos**: A list of specific remaining tasks (strings). If everything is done, use an empty list `[]`.
- **nextAction**: The single most logical next step to resume this work. If nothing remains, set to `null`.

### Step 5 — Write enrichments.json

Ensure the directory exists and then atomically merge the new entry into the enrichment store.

```bash
mkdir -p ~/.claude/sessions
```

Then run the following, replacing the placeholder values with actual data collected above:

```bash
python3 -c "
import json, os, datetime

path = os.path.expanduser('~/.claude/sessions/enrichments.json')

try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {'version': 1, 'sessions': {}}

data['sessions']['SESSION_ID'] = {
    'autoName': 'AUTO_NAME',
    'savedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'projectPath': 'PROJECT_PATH',
    'todos': ['todo1', 'todo2'],
    'nextAction': 'NEXT_ACTION_OR_None',
    'userNote': 'USER_NOTE_OR_None'
}

with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Saved.')
"
```

Replace in the template:
- `SESSION_ID` — the actual session UUID
- `AUTO_NAME` — the name generated in Step 2
- `PROJECT_PATH` — absolute path to the project root
- `todos` list — actual todo strings from Step 4
- `NEXT_ACTION_OR_None` — next action string or Python `None`
- `USER_NOTE_OR_None` — user note string or Python `None`

### Step 6 — Optional: claude-mem observation

If claude-mem MCP tools are available (check for `mcp__plugin_claude-mem_mcp-search__smart_search` or similar), write an observation:

```
[session-snap] saved: <autoName> | todos: <count> | branch: <branch>
```

If claude-mem tools are not available, skip this step silently. Do not warn or error.

### Step 7 — Display confirmation

Show the user a summary:

```
Session saved.

  Name:        [project] task description
  Session:     <session-id (first 8 chars)>…
  Branch:      <branch>
  Todos:       <count> items
  Next action: <next action>
  Note:        <user note or "—">
  Stored in:   ~/.claude/sessions/enrichments.json
```

### Enrichments.json Schema Reference

```json
{
  "version": 1,
  "sessions": {
    "<session-uuid>": {
      "autoName": "[project] short description",
      "savedAt": "ISO 8601 datetime with timezone",
      "projectPath": "/absolute/path/to/project",
      "todos": ["remaining task 1", "remaining task 2"],
      "nextAction": "most logical next step",
      "userNote": "optional user-provided note or null"
    }
  }
}
```

### Native sessions-index.json Reference (read-only)

Claude Code stores session metadata at `~/.claude/projects/*/sessions-index.json`. The file is a JSON object with a `version` key and an `entries` array:

```json
{
  "version": 1,
  "entries": [
    {
      "sessionId": "uuid",
      "summary": "auto-generated summary",
      "created": "ISO datetime",
      "modified": "ISO datetime",
      "gitBranch": "branch-name",
      "projectPath": "/absolute/path",
      "messageCount": 47,
      "isSidechain": false
    }
  ]
}
```

**Parsing pattern** — always unwrap the `entries` key:

```python
raw = json.load(f)
if isinstance(raw, dict) and 'entries' in raw:
    entries = raw['entries']
elif isinstance(raw, list):
    entries = raw
else:
    entries = []
```

The `elif isinstance(raw, list)` branch is a backward-compatibility fallback in case older files use the flat-list format.

These files are **read-only** — never modify them. Use them for lookups and cross-referencing.

## /ss list

**Purpose:** List recent sessions across ALL projects, sorted by most recently modified.

**Args:** Optional count (default 10). Example: `/ss list 20`

Follow these steps exactly:

### Step 1 — Parse arguments

Extract the optional count from the user's input. If not provided, default to `10`.

### Step 2 — Collect and display sessions

Run the following Python script, replacing `MAX_COUNT` with the parsed count:

```bash
python3 -c "
import json, glob, os, datetime

MAX_COUNT = MAX_COUNT_PLACEHOLDER

# --- Collect native sessions ---
index_files = glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json'))
all_sessions = []
for fpath in index_files:
    try:
        with open(fpath) as f:
            raw = json.load(f)
        if isinstance(raw, dict) and 'entries' in raw:
            entries = raw['entries']
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = []
        all_sessions.extend(entries)
    except (json.JSONDecodeError, OSError):
        continue

# --- Load enrichments ---
enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')
enrichments = {}
try:
    with open(enrich_path) as f:
        enrichments = json.load(f).get('sessions', {})
except (FileNotFoundError, json.JSONDecodeError):
    pass

# --- Sort by modified descending ---
def parse_dt(s):
    if not s:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

all_sessions.sort(key=lambda e: parse_dt(e.get('modified', '')), reverse=True)
top = all_sessions[:MAX_COUNT]

# --- Time-ago formatting ---
now = datetime.datetime.now(datetime.timezone.utc)
def time_ago(iso_str):
    dt = parse_dt(iso_str)
    if dt == datetime.datetime.min.replace(tzinfo=datetime.timezone.utc):
        return '?'
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f'{secs}s ago'
    mins = secs // 60
    if mins < 60:
        return f'{mins}m ago'
    hrs = mins // 60
    if hrs < 24:
        return f'{hrs}h ago'
    days = hrs // 24
    return f'{days}d ago'

# --- Project name from path ---
def project_name(path):
    if not path:
        return '?'
    return os.path.basename(path.rstrip('/')).lower()

# --- Build table ---
rows = []
for i, s in enumerate(top, 1):
    sid = s.get('sessionId', '')
    proj = project_name(s.get('projectPath', ''))
    branch = s.get('gitBranch', '') or ''
    summary = s.get('summary', '') or ''
    age = time_ago(s.get('modified', ''))
    has_enrich = sid in enrichments
    # Prefer enrichment autoName over native summary
    if has_enrich and enrichments[sid].get('autoName'):
        summary = enrichments[sid]['autoName']
    # Truncate long fields
    branch = (branch[:20] + '…') if len(branch) > 21 else branch
    summary = (summary[:40] + '…') if len(summary) > 41 else summary
    star = ' ★' if has_enrich else '  '
    rows.append((i, age, proj, branch, summary, star))

# --- Print ---
print('Recent Sessions')
print(f\" {'#':>2}  {'Age':<8} {'Project':<12} {'Branch':<21} {'Summary':<42}\")
print(f\" {'—'*2}  {'—'*8} {'—'*12} {'—'*21} {'—'*42}\")
for (idx, age, proj, branch, summary, star) in rows:
    print(f' {idx:>2}  {age:<8} {proj:<12} {branch:<21} {summary:<40}{star}')
if any(r[5].strip() for r in rows):
    print()
    print('★ = has enrichment data (todos/notes)')
if not rows:
    print('  (no sessions found)')
"
```

Replace `MAX_COUNT_PLACEHOLDER` with the actual integer count (e.g., `10` or `20`).

### Step 3 — Display output

The script output is the final result. Display it directly to the user with no additional wrapping.

## /ss find

**Purpose:** Multi-dimensional search across all sessions by keyword, project, and/or time range.

**Args parsing:**
- Positional keyword: e.g., `/ss find richmenu`
- `--project X`: filter by project name (case-insensitive)
- `--since Nd`: only sessions from the last N days (e.g., `--since 7d`)
- All flags can be combined: `/ss find richmenu --project grazioso --since 7d`

Follow these steps exactly:

### Step 1 — Parse arguments

Extract from the user's input:
- `KEYWORD` — the positional search term (may be empty if only flags are used)
- `PROJECT_FILTER` — value of `--project` flag, or empty string if not provided
- `SINCE_DAYS` — integer from `--since Nd` flag, or `0` if not provided (meaning no time filter)

### Step 2 — Search native and enrichment data

Run the following Python script, replacing the three placeholder values:

```bash
python3 -c "
import json, glob, os, datetime

KEYWORD = 'KEYWORD_PLACEHOLDER'
PROJECT_FILTER = 'PROJECT_FILTER_PLACEHOLDER'
SINCE_DAYS = SINCE_DAYS_PLACEHOLDER  # integer, 0 means no filter

now = datetime.datetime.now(datetime.timezone.utc)

# --- Collect native sessions ---
index_files = glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json'))
all_sessions = {}
for fpath in index_files:
    try:
        with open(fpath) as f:
            raw = json.load(f)
        if isinstance(raw, dict) and 'entries' in raw:
            entries = raw['entries']
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = []
        for e in entries:
            sid = e.get('sessionId', '')
            if sid:
                all_sessions[sid] = e
    except (json.JSONDecodeError, OSError):
        continue

# --- Load enrichments ---
enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')
enrichments = {}
try:
    with open(enrich_path) as f:
        enrichments = json.load(f).get('sessions', {})
except (FileNotFoundError, json.JSONDecodeError):
    pass

# --- Helpers ---
def parse_dt(s):
    if not s:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

def project_name(path):
    if not path:
        return ''
    return os.path.basename(path.rstrip('/')).lower()

def time_ago(iso_str):
    dt = parse_dt(iso_str)
    if dt == datetime.datetime.min.replace(tzinfo=datetime.timezone.utc):
        return '?'
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f'{secs}s ago'
    mins = secs // 60
    if mins < 60:
        return f'{mins}m ago'
    hrs = mins // 60
    if hrs < 24:
        return f'{hrs}h ago'
    days = hrs // 24
    return f'{days}d ago'

# --- Ensure enrichment-only sessions are included ---
for sid, enr in enrichments.items():
    if sid not in all_sessions:
        all_sessions[sid] = {
            'sessionId': sid,
            'summary': enr.get('autoName', ''),
            'modified': enr.get('savedAt', ''),
            'projectPath': enr.get('projectPath', ''),
            'gitBranch': '',
            'messageCount': 0,
        }

# --- Filter: since ---
if SINCE_DAYS > 0:
    cutoff = now - datetime.timedelta(days=SINCE_DAYS)
    all_sessions = {
        sid: s for sid, s in all_sessions.items()
        if parse_dt(s.get('modified', '')) >= cutoff
    }

# --- Filter: project ---
if PROJECT_FILTER:
    pf = PROJECT_FILTER.lower()
    all_sessions = {
        sid: s for sid, s in all_sessions.items()
        if pf in project_name(s.get('projectPath', ''))
    }

# --- Filter: keyword ---
if KEYWORD:
    kw = KEYWORD.lower()
    matched = {}
    for sid, s in all_sessions.items():
        fields = [
            s.get('summary', ''),
            s.get('gitBranch', ''),
        ]
        enr = enrichments.get(sid, {})
        fields.extend([
            enr.get('autoName', ''),
            enr.get('userNote', '') or '',
            enr.get('nextAction', '') or '',
        ])
        fields.extend(enr.get('todos', []) or [])
        blob = ' '.join(str(f) for f in fields).lower()
        if kw in blob:
            matched[sid] = s
    all_sessions = matched

# --- Sort by modified descending ---
results = sorted(all_sessions.values(), key=lambda e: parse_dt(e.get('modified', '')), reverse=True)

# --- Build table ---
query_parts = []
if KEYWORD:
    query_parts.append(f'keyword=\"{KEYWORD}\"')
if PROJECT_FILTER:
    query_parts.append(f'project={PROJECT_FILTER}')
if SINCE_DAYS > 0:
    query_parts.append(f'since={SINCE_DAYS}d')
query_str = ', '.join(query_parts) if query_parts else 'all'

print(f'Search Results ({query_str}) — {len(results)} found')
print(f\" {'#':>2}  {'Age':<8} {'Project':<12} {'Branch':<21} {'Summary':<42}\")
print(f\" {'—'*2}  {'—'*8} {'—'*12} {'—'*21} {'—'*42}\")

for i, s in enumerate(results, 1):
    sid = s.get('sessionId', '')
    proj = project_name(s.get('projectPath', ''))
    branch = s.get('gitBranch', '') or ''
    summary = s.get('summary', '') or ''
    age = time_ago(s.get('modified', ''))
    has_enrich = sid in enrichments
    if has_enrich and enrichments[sid].get('autoName'):
        summary = enrichments[sid]['autoName']
    branch = (branch[:20] + '…') if len(branch) > 21 else branch
    summary = (summary[:40] + '…') if len(summary) > 41 else summary
    star = ' ★' if has_enrich else '  '
    print(f' {i:>2}  {age:<8} {proj:<12} {branch:<21} {summary:<40}{star}')

if any(sid in enrichments for sid in all_sessions):
    print()
    print('★ = has enrichment data (todos/notes)')
if not results:
    print('  (no sessions found)')
"
```

Replace in the template:
- `KEYWORD_PLACEHOLDER` — the search keyword string (use empty string `''` if none)
- `PROJECT_FILTER_PLACEHOLDER` — the project filter string (use empty string `''` if none)
- `SINCE_DAYS_PLACEHOLDER` — integer number of days (use `0` if no `--since` flag)

### Step 3 — Optional: claude-mem augmented search

If claude-mem MCP tools are available (check for `mcp__plugin_claude-mem_mcp-search__smart_search`), and a keyword was provided, also run:

```
smart_search(query="session: <KEYWORD>")
```

If results are returned, cross-reference any session IDs found in the claude-mem results with the table above. Append any new sessions not already shown (deduplicate by sessionId) to the bottom of the results.

If claude-mem tools are not available, skip this step silently. Do not warn or error.

### Step 4 — Display output

The script output is the final result. Display it directly to the user with no additional wrapping.

## /ss resume

**Purpose:** Restore context from a previous session so you can continue where you left off.

Follow these steps exactly:

### Step 1 — Resolve target session

The user specifies a target after `resume`. Determine the type and resolve to a `sessionId`:

**Load all sessions first:**

```bash
python3 -c "
import json, glob, os

sessions = []
for idx_path in glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json')):
    try:
        with open(idx_path) as f:
            raw = json.load(f)
        if isinstance(raw, dict) and 'entries' in raw:
            entries = raw['entries']
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = []
        sessions.extend(entries)
    except (json.JSONDecodeError, FileNotFoundError):
        pass

# Load enrichments
enrich = {}
enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')
try:
    with open(enrich_path) as f:
        enrich = json.load(f).get('sessions', {})
except (FileNotFoundError, json.JSONDecodeError):
    pass

# Sort by modified descending (same order as /ss list)
sessions.sort(key=lambda s: s.get('modified', ''), reverse=True)

# Attach enrichment data and 1-based index
for i, s in enumerate(sessions):
    sid = s.get('sessionId', '')
    s['_index'] = i + 1
    s['_enrichment'] = enrich.get(sid)

import sys
json.dump(sessions, sys.stdout, indent=2, ensure_ascii=False)
"
```

Then match the target using these rules (in priority order):

| Target format | Resolution |
|---------------|------------|
| Integer (e.g., `1`, `3`) | Use as 1-based index into the sorted list above. If index is out of range, display: `Index <n> is out of range. Run /ss list to see available sessions.` and stop. |
| UUID-like string (contains `-` and length >= 36) | Match directly against `sessionId`. If not found, display: `Session not found: <target>` and stop. |
| Keyword string | Search `autoName` (from enrichment), `summary`, `gitBranch`, and `projectPath` for case-insensitive substring match. See keyword matching rules below. |

**Keyword matching rules:**
- If exactly **one** session matches → auto-select it
- If **multiple** sessions match → display a numbered selection menu and ask the user to pick:
  ```
  Multiple sessions match "<keyword>":
    1. [grazioso] richmenu zodios migration  (2h ago)
    2. [grazioso] richmenu api cleanup       (3d ago)
  Enter number to resume:
  ```
- If **no** sessions match → display `No session found matching "<keyword>"` and stop

### Step 2 — Preview card (always shown)

Display a preview card for the resolved session. Merge data from sessions-index.json and enrichments.json:

```bash
python3 -c "
import json, os, datetime, glob

# ---- Replace this placeholder with the actual resolved session ID ----
SESSION_ID = 'TARGET_SESSION_ID'

# Load native session data
session = None
for idx_path in glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json')):
    try:
        with open(idx_path) as f:
            raw = json.load(f)
        if isinstance(raw, dict) and 'entries' in raw:
            entries = raw['entries']
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = []
        for e in entries:
            if e.get('sessionId') == SESSION_ID:
                session = e
                break
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    if session:
        break

if not session:
    print(f'Session {SESSION_ID} not found in any sessions-index.json')
    exit(1)

# Load enrichment
enrich = None
enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')
try:
    with open(enrich_path) as f:
        enrich = json.load(f).get('sessions', {}).get(SESSION_ID)
except (FileNotFoundError, json.JSONDecodeError):
    pass

# Compute relative time
modified = session.get('modified', '')
try:
    mod_dt = datetime.datetime.fromisoformat(modified.replace('Z', '+00:00'))
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - mod_dt
    if delta.days > 0:
        rel = f'{delta.days} day{\"s\" if delta.days != 1 else \"\"} ago'
    else:
        hours = delta.seconds // 3600
        if hours > 0:
            rel = f'{hours} hour{\"s\" if hours != 1 else \"\"} ago'
        else:
            mins = delta.seconds // 60
            rel = f'{mins} minute{\"s\" if mins != 1 else \"\"} ago'
except Exception:
    rel = 'unknown'

# Display name: prefer autoName from enrichment, fall back to native summary
display_name = (enrich or {}).get('autoName') or session.get('summary', SESSION_ID[:8])

print(f'Session: {display_name}')
print('━' * 40)
print(f'  Project:     {session.get(\"projectPath\", \"unknown\")}')
print(f'  Branch:      {session.get(\"gitBranch\", \"unknown\")}')
print(f'  Last active: {modified[:16].replace(\"T\", \" \")} ({rel})')
print(f'  Messages:    {session.get(\"messageCount\", \"?\")}')

if enrich:
    todos = enrich.get('todos', [])
    if todos:
        print()
        print('  Todos:')
        for t in todos:
            print(f'    □ {t}')
    na = enrich.get('nextAction')
    if na:
        print()
        print(f'  Next action: {na}')
    note = enrich.get('userNote')
    if note:
        print(f'  Note:        {note}')

print()
print('Resume this session? (y/n)')
print('━' * 40)
"
```

Replace `TARGET_SESSION_ID` with the actual resolved session ID from Step 1.

**Wait for user confirmation before proceeding.** If the user declines, stop.

### Step 3 — Check for `--switch` flag

If the user included `--switch` in the command (e.g., `/ss resume richmenu --switch`):

1. Output the resume command:
   ```
   claude --resume <session-id>
   ```
2. Copy to clipboard:
   ```bash
   echo "claude --resume <session-id>" | pbcopy
   ```
3. Display:
   ```
   Command copied to clipboard. Open a new terminal and paste to resume the full session.
   ```
4. **Stop here.** Do not proceed to context import.

If `--switch` is **not** present, continue to Step 4.

### Step 4 — Read enrichment data

Load the enrichment entry for the target session:

```bash
python3 -c "
import json, os

SESSION_ID = 'TARGET_SESSION_ID'

path = os.path.expanduser('~/.claude/sessions/enrichments.json')
try:
    with open(path) as f:
        data = json.load(f)
    entry = data.get('sessions', {}).get(SESSION_ID)
    if entry:
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    else:
        print('NO_ENRICHMENT')
except (FileNotFoundError, json.JSONDecodeError):
    print('NO_ENRICHMENT')
"
```

Replace `TARGET_SESSION_ID` with the actual session ID.

If output is `NO_ENRICHMENT`, note that — you will still have native session data from Step 2.

### Step 5 — Read session JSONL for conversation context

Locate and parse the session's JSONL conversation log to extract recent context:

```bash
python3 -c "
import json, glob, os

SESSION_ID = 'TARGET_SESSION_ID'

# Try to find the JSONL file
# Pattern: ~/.claude/projects/*/<sessionId>.jsonl
matches = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{SESSION_ID}.jsonl'))

if not matches:
    print('JSONL_NOT_FOUND')
    exit(0)

jsonl_path = matches[0]

# Read and parse JSONL
messages = []
with open(jsonl_path) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            role = msg.get('role', '')
            if role in ('human', 'assistant', 'user'):
                content = msg.get('content', '')
                # Handle content that is a list of blocks
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block['text'])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = ' '.join(text_parts)
                if isinstance(content, str) and len(content.strip()) > 0:
                    messages.append({'role': role, 'content': content[:500]})
        except json.JSONDecodeError:
            continue

# Extract last 10 human/assistant pairs
# Walk backwards to find pairs
pairs = []
i = len(messages) - 1
while i >= 0 and len(pairs) < 10:
    if messages[i]['role'] in ('assistant',):
        assistant_msg = messages[i]
        # Look for preceding human message
        j = i - 1
        while j >= 0 and messages[j]['role'] not in ('human', 'user'):
            j -= 1
        if j >= 0:
            pairs.append({'human': messages[j]['content'], 'assistant': assistant_msg['content']})
            i = j - 1
        else:
            i -= 1
    else:
        i -= 1

pairs.reverse()

for idx, pair in enumerate(pairs):
    print(f'--- Pair {idx+1} ---')
    print(f'Human: {pair[\"human\"][:200]}')
    print(f'Assistant: {pair[\"assistant\"][:200]}')
    print()
"
```

Replace `TARGET_SESSION_ID` with the actual session ID.

Review the output and identify the **key topics, decisions, and discoveries** from the conversation. Summarize them into 3-7 concise bullet points.

If the output is `JSONL_NOT_FOUND`, skip this step and note it in the briefing.

### Step 6 — Query claude-mem (optional)

If claude-mem MCP tools are available (check for `mcp__plugin_claude-mem_mcp-search__smart_search` or similar), search for related observations:

1. Search by branch name from the session's `gitBranch`:
   ```
   smart_search(query="branch: <gitBranch>")
   ```
2. Search by key terms from the session's `autoName` or `summary`:
   ```
   smart_search(query="session: <key terms from autoName>")
   ```
3. Search for `[session-snap]` tagged observations:
   ```
   smart_search(query="[session-snap] <autoName>")
   ```

Include any relevant findings as additional context bullets in the briefing.

If claude-mem tools are not available, skip this step silently. Do not warn or error.

### Step 7 — Synthesize and display context briefing

Combine all gathered data into a structured briefing:

```
=== Session Context Restored ===

Project: <projectPath>
Branch: <gitBranch>

Summary: <autoName or native summary — what the user was working on>

Key Context from Previous Session:
- <key decision or discovery 1>
- <key decision or discovery 2>
- <key decision or discovery 3>

Remaining Todos:
- <todo 1>
- <todo 2>

Next Action: <nextAction or "None specified">

User Note: <userNote or "—">
================================
```

**Data source mapping for the briefing:**
- `Project`, `Branch`: from sessions-index.json
- `Summary`: prefer `autoName` from enrichments.json, fall back to `summary` from sessions-index.json
- `Key Context`: synthesized from JSONL conversation log (Step 5) and claude-mem observations (Step 6)
- `Remaining Todos`, `Next Action`, `User Note`: from enrichments.json

If no enrichment exists for the session, omit the `Remaining Todos`, `Next Action`, and `User Note` sections entirely, and append: `(No enrichment data saved for this session)`

If the JSONL file was not found, replace the `Key Context from Previous Session` bullets with: `(Conversation log not available)`

After displaying the context briefing, tell the user:

```
Context loaded. What would you like to continue with?
```

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Session ID not found in any sessions-index.json | Display: `Session not found: <target>` and stop |
| No enrichment data for the session | Show preview card with native data only (no todos/notes sections). In context briefing, omit enrichment sections and note `(No enrichment data saved for this session)` |
| JSONL file missing or unreadable | Skip conversation context extraction. In briefing, show `(Conversation log not available)` under Key Context |
| Keyword matches multiple sessions | Show numbered list with autoName/summary, project, branch, and last modified. Ask user to pick |
| Index out of range | Display: `Index <n> is out of range. Run /ss list to see available sessions.` and stop |
| claude-mem unavailable | Skip silently — no warning, no error |
| No target provided (`/ss resume` with no argument) | Display: `Usage: /ss resume <target> [--switch]` and show help for target formats |

## /ss del

**Purpose:** Delete enrichment data for sessions. Only affects `~/.claude/sessions/enrichments.json` — never modifies native Claude Code files.

**Target formats:**
- `/ss del 3` — delete enrichment for list item #3
- `/ss del <uuid>` — delete by session ID
- `/ss del --before 30d` — delete all enrichments older than 30 days
- `/ss del --all` — clear all enrichments

Follow these steps exactly:

### Step 1 — Parse arguments

Extract the target from the user's input after `del`:

| Input pattern | Type | Value |
|---------------|------|-------|
| Integer (e.g., `3`) | `index` | The 1-based index number |
| UUID-like string (contains `-`, length >= 36) | `uuid` | The session ID string |
| `--before Nd` (e.g., `--before 30d`) | `before` | Integer number of days |
| `--all` | `all` | n/a |

If no argument is provided, display `Usage: /ss del <target>` and the target format table above, then stop.

### Step 2 — Resolve targets and preview

Run the following Python script, replacing the placeholders with the parsed values:

```bash
python3 -c "
import json, os, datetime, sys

MODE = 'MODE_PLACEHOLDER'        # one of: index, uuid, before, all
VALUE = 'VALUE_PLACEHOLDER'       # the parsed value (index number, uuid string, or days integer)

enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')

try:
    with open(enrich_path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print('No enrichments.json found or file is empty. Nothing to delete.')
    sys.exit(0)

sessions = data.get('sessions', {})
if not sessions:
    print('No enrichment entries found. Nothing to delete.')
    sys.exit(0)

now = datetime.datetime.now(datetime.timezone.utc)

def parse_dt(s):
    if not s:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

# --- Determine which sessions to delete ---
to_delete = {}

if MODE == 'all':
    to_delete = dict(sessions)

elif MODE == 'before':
    days = int(VALUE)
    cutoff = now - datetime.timedelta(days=days)
    for sid, entry in sessions.items():
        saved_at = parse_dt(entry.get('savedAt', ''))
        if saved_at < cutoff:
            to_delete[sid] = entry

elif MODE == 'uuid':
    if VALUE in sessions:
        to_delete[VALUE] = sessions[VALUE]
    else:
        print(f'Session ID not found in enrichments: {VALUE}')
        sys.exit(1)

elif MODE == 'index':
    # Re-run list logic: load all native sessions, sort by modified desc, resolve index
    import glob
    all_sessions = []
    for idx_path in glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json')):
        try:
            with open(idx_path) as f:
                raw = json.load(f)
            if isinstance(raw, dict) and 'entries' in raw:
                entries = raw['entries']
            elif isinstance(raw, list):
                entries = raw
            else:
                entries = []
            all_sessions.extend(entries)
        except (json.JSONDecodeError, OSError):
            continue
    all_sessions.sort(key=lambda e: e.get('modified', ''), reverse=True)
    idx = int(VALUE)
    if idx < 1 or idx > len(all_sessions):
        print(f'Index {idx} is out of range. Run /ss list to see available sessions.')
        sys.exit(1)
    target_sid = all_sessions[idx - 1].get('sessionId', '')
    if target_sid not in sessions:
        name = all_sessions[idx - 1].get('summary', target_sid[:8])
        print(f'Session #{idx} ({name}) has no enrichment data to delete.')
        sys.exit(1)
    to_delete[target_sid] = sessions[target_sid]

# --- Preview ---
if not to_delete:
    print('No matching enrichment entries found. Nothing to delete.')
    sys.exit(0)

print(f'Will delete {len(to_delete)} enrichment(s):')
print()
for sid, entry in to_delete.items():
    name = entry.get('autoName', sid[:8])
    saved = entry.get('savedAt', '?')[:16].replace('T', ' ')
    print(f'  - {name}  (saved: {saved}, id: {sid[:8]}…)')

print()
print('AWAITING_CONFIRMATION')
"
```

Replace in the template:
- `MODE_PLACEHOLDER` — one of `index`, `uuid`, `before`, `all`
- `VALUE_PLACEHOLDER` — the parsed value as a string (index number, uuid, or days count). For `--all` mode, use an empty string.

### Step 3 — Confirm with user

**Wait for user confirmation before proceeding.** Display the preview output from Step 2 and ask:

```
Confirm deletion? (y/n)
```

If the user declines, display `Cancelled.` and stop.

### Step 4 — Execute deletion

After the user confirms, run the following Python script with the same placeholders:

```bash
python3 -c "
import json, os, datetime, sys, glob

MODE = 'MODE_PLACEHOLDER'
VALUE = 'VALUE_PLACEHOLDER'

enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')

with open(enrich_path) as f:
    data = json.load(f)

sessions = data.get('sessions', {})
now = datetime.datetime.now(datetime.timezone.utc)

def parse_dt(s):
    if not s:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

to_delete = set()

if MODE == 'all':
    to_delete = set(sessions.keys())
elif MODE == 'before':
    days = int(VALUE)
    cutoff = now - datetime.timedelta(days=days)
    for sid, entry in sessions.items():
        if parse_dt(entry.get('savedAt', '')) < cutoff:
            to_delete.add(sid)
elif MODE == 'uuid':
    to_delete.add(VALUE)
elif MODE == 'index':
    all_sessions = []
    for idx_path in glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json')):
        try:
            with open(idx_path) as f:
                raw = json.load(f)
            if isinstance(raw, dict) and 'entries' in raw:
                entries = raw['entries']
            elif isinstance(raw, list):
                entries = raw
            else:
                entries = []
            all_sessions.extend(entries)
        except (json.JSONDecodeError, OSError):
            continue
    all_sessions.sort(key=lambda e: e.get('modified', ''), reverse=True)
    idx = int(VALUE)
    to_delete.add(all_sessions[idx - 1]['sessionId'])

deleted_names = []
for sid in to_delete:
    entry = sessions.pop(sid, None)
    if entry:
        deleted_names.append(entry.get('autoName', sid[:8]))

data['sessions'] = sessions

with open(enrich_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Deleted {len(deleted_names)} enrichment(s):')
for name in deleted_names:
    print(f'  - {name}')
print()
print(f'Remaining enrichments: {len(sessions)}')
"
```

Replace `MODE_PLACEHOLDER` and `VALUE_PLACEHOLDER` with the same values used in Step 2.

### Step 5 — Display confirmation

The script output from Step 4 is the final result. Display it directly to the user with no additional wrapping.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| enrichments.json missing or empty | Display `No enrichments found. Nothing to delete.` and stop |
| Index out of range | Display `Index <n> is out of range. Run /ss list to see available sessions.` and stop |
| Session has no enrichment data | Display `Session #<n> (<name>) has no enrichment data to delete.` and stop |
| UUID not found in enrichments | Display `Session ID not found in enrichments: <uuid>` and stop |
| `--before` matches zero entries | Display `No enrichments older than <N> days found.` and stop |
| No argument provided | Display usage help and stop |

## /ss tidy

**Purpose:** Batch rename unnamed sessions to improve the `claude --resume` picker experience. Scans for sessions that lack enrichment data, reads their conversation logs to understand context, and proposes descriptive names.

**Args:** `--since Nd` (default `7d`) — only process sessions from the last N days.

**Limitation:** The `/rename` command only works for the **current** session. For other sessions, tidy saves the proposed names to `enrichments.json` as `autoName`. These names will appear in `/ss list` and `/ss find` output but will not change the native Claude Code session name shown in `claude --resume`. This is a known limitation.

Follow these steps exactly:

### Step 1 — Parse arguments

Extract `SINCE_DAYS` from `--since Nd` flag. If not provided, default to `7`.

### Step 2 — Find unnamed sessions

Run the following Python script, replacing the placeholder:

```bash
python3 -c "
import json, glob, os, datetime

SINCE_DAYS = SINCE_DAYS_PLACEHOLDER

now = datetime.datetime.now(datetime.timezone.utc)
cutoff = now - datetime.timedelta(days=SINCE_DAYS)

# --- Load enrichments ---
enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')
enrichments = {}
try:
    with open(enrich_path) as f:
        enrichments = json.load(f).get('sessions', {})
except (FileNotFoundError, json.JSONDecodeError):
    pass

# --- Collect native sessions ---
index_files = glob.glob(os.path.expanduser('~/.claude/projects/*/sessions-index.json'))
unnamed = []

for fpath in index_files:
    try:
        with open(fpath) as f:
            raw = json.load(f)
        if isinstance(raw, dict) and 'entries' in raw:
            entries = raw['entries']
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = []
        for entry in entries:
            sid = entry.get('sessionId', '')
            if not sid:
                continue
            # Skip sessions that already have enrichment data
            if sid in enrichments:
                continue
            # Filter by time range
            modified = entry.get('modified', '')
            if not modified:
                continue
            try:
                mod_dt = datetime.datetime.fromisoformat(modified)
                if mod_dt < cutoff:
                    continue
            except Exception:
                continue
            # Skip sidechains
            if entry.get('isSidechain', False):
                continue
            unnamed.append(entry)
    except (json.JSONDecodeError, OSError):
        continue

# Sort by modified descending
unnamed.sort(key=lambda e: e.get('modified', ''), reverse=True)

if not unnamed:
    print('NO_UNNAMED_SESSIONS')
else:
    print(f'Found {len(unnamed)} unnamed session(s) from the last {SINCE_DAYS} day(s):')
    print()
    for s in unnamed:
        sid = s.get('sessionId', '')
        proj = os.path.basename((s.get('projectPath', '') or '').rstrip('/')).lower()
        branch = s.get('gitBranch', '') or '—'
        summary = s.get('summary', '') or '(no summary)'
        msgs = s.get('messageCount', '?')
        modified = s.get('modified', '')[:16].replace('T', ' ')
        print(f'  {sid[:8]}…  [{proj}]  branch={branch}  msgs={msgs}  modified={modified}')
        print(f'             native summary: {summary[:80]}')
    # Output JSON for next step
    import sys
    print()
    print('JSON_DATA_START')
    json.dump(unnamed, sys.stdout, ensure_ascii=False)
    print()
    print('JSON_DATA_END')
"
```

Replace `SINCE_DAYS_PLACEHOLDER` with the actual integer (e.g., `7`).

If the output is `NO_UNNAMED_SESSIONS`, display `No unnamed sessions found in the last <N> days. Nothing to tidy.` and stop.

### Step 3 — Read conversation logs and generate names

For each unnamed session from Step 2, read the first few messages from the JSONL file to understand what the session was about. Run the following for **each session** (batch into a single script):

```bash
python3 -c "
import json, glob, os

# List of session IDs to process (from Step 2 output)
SESSION_IDS = SESSION_IDS_PLACEHOLDER  # e.g., ['uuid1', 'uuid2', ...]

results = []
for sid in SESSION_IDS:
    matches = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{sid}.jsonl'))
    snippet = ''
    if matches:
        lines_read = 0
        messages = []
        with open(matches[0]) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    role = msg.get('role', '')
                    if role in ('human', 'user'):
                        content = msg.get('content', '')
                        if isinstance(content, list):
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get('type') == 'text':
                                    text_parts.append(block['text'])
                                elif isinstance(block, str):
                                    text_parts.append(block)
                            content = ' '.join(text_parts)
                        if isinstance(content, str) and content.strip():
                            messages.append(content[:300])
                            lines_read += 1
                            if lines_read >= 5:
                                break
                except json.JSONDecodeError:
                    continue
        snippet = ' | '.join(messages)
    results.append({'sessionId': sid, 'snippet': snippet[:600]})

import sys
json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
"
```

Replace `SESSION_IDS_PLACEHOLDER` with the actual Python list of session ID strings from Step 2.

### Step 4 — Generate proposed names

For each session, review:
- The JSONL snippet from Step 3 (what the user was asking about)
- The native session metadata (project, branch, summary) from Step 2

Generate a name in the format: `[project-lowercase] short task description`

Examples:
- `[grazioso] richmenu zodios migration`
- `[rubato] fix audience segment pagination`
- `[dbt-models] add cdh event dedup model`

Keep each name under 60 characters total. Derive the task description from the conversation snippet content.

### Step 5 — Present proposed renames

Display a table of proposed renames for user approval:

```
Proposed renames (last <N> days, <count> sessions):

  #  Session     Current Name                  Proposed Name
  —  ————————    ————————————                  —————————————
  1  <id[:8]>…   <native summary[:30]>         [project] new name
  2  <id[:8]>…   <native summary[:30]>         [project] new name
  3  <id[:8]>…   <native summary[:30]>         [project] new name

Approve all? Or enter numbers to approve selectively (e.g., 1,3), or "n" to cancel.
```

**Wait for user input:**
- `y` or `yes` or empty — approve all
- Comma-separated numbers (e.g., `1,3`) — approve only those
- `n` or `no` — cancel

If the user cancels, display `Cancelled.` and stop.

### Step 6 — Apply approved renames

For each approved session, save the proposed name to enrichments.json. Run the following Python script:

```bash
python3 -c "
import json, os, datetime

enrich_path = os.path.expanduser('~/.claude/sessions/enrichments.json')

try:
    with open(enrich_path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {'version': 1, 'sessions': {}}

# Approved renames: list of (sessionId, autoName, projectPath) tuples
RENAMES = RENAMES_PLACEHOLDER  # e.g., [['uuid1', '[proj] name', '/path'], ...]

now = datetime.datetime.now(datetime.timezone.utc).isoformat()

for sid, auto_name, project_path in RENAMES:
    data['sessions'][sid] = {
        'autoName': auto_name,
        'savedAt': now,
        'projectPath': project_path,
        'todos': [],
        'nextAction': None,
        'userNote': 'Auto-named by /ss tidy'
    }

with open(enrich_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Saved {len(RENAMES)} enrichment(s) to enrichments.json.')
print()
for sid, auto_name, _ in RENAMES:
    print(f'  {sid[:8]}…  →  {auto_name}')
"
```

Replace `RENAMES_PLACEHOLDER` with the actual Python list of `[sessionId, autoName, projectPath]` lists for the approved sessions.

### Step 7 — Display results

Show the final summary:

```
Tidy complete.

  Saved to enrichments: <count>

These names will now appear in /ss list and /ss find output.

Note: Native session names (shown in `claude --resume`) are unchanged.
      The /rename command only works for the current session.
```

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| No unnamed sessions in time range | Display `No unnamed sessions found in the last <N> days. Nothing to tidy.` and stop |
| JSONL file missing for a session | Use the native `summary` from sessions-index.json as the basis for the generated name. Note `(no conversation log)` next to that entry in the preview table |
| enrichments.json missing | Create it with `{"version": 1, "sessions": {}}` structure |
| User cancels at approval step | Display `Cancelled.` and stop |
| Session already has enrichment data | Skip it — Step 2 already filters these out |
| Very short conversation (1-2 messages) | Generate name from whatever is available; note `(short session)` in preview |
