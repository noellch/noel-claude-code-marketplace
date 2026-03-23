#!/usr/bin/env python3
"""Session Snap CLI — cross-project session search for Claude Code.

Usage:
    ss.py rename <name> [--id <session-id>]
    ss.py copy <session-id-prefix>
    ss.py find <keyword> [--project NAME] [--since Nd]
    ss.py list [COUNT] [--all]
    ss.py clean [--empty] [--older Nd] [--confirm]
    ss.py context
    ss.py rebuild          (force rebuild cache)
    ss.py --help
"""

import json
import glob
import os
import sys
import datetime

PROJECTS_BASE = os.path.expanduser("~/.claude/projects")
CACHE_PATH = os.path.expanduser("~/.claude/session-snap-cache.json")


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_dt(s):
    if not s:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


def time_ago(iso_str):
    dt = parse_dt(iso_str)
    if dt == datetime.datetime.min.replace(tzinfo=datetime.timezone.utc):
        return "?"
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h ago"
    days = hrs // 24
    return f"{days}d ago"


def project_name(path):
    if not path:
        return "?"
    return os.path.basename(path.rstrip("/")).lower()


# ── Cache layer ──────────────────────────────────────────────────────────────

def _load_cache():
    """Load the session-snap cache. Returns {sessionId: entry}."""
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))


def _extract_metadata(jsonl_path):
    """Read a .jsonl file to extract session metadata, first user message, and summary."""
    meta = {}
    first_user_text = None
    summary = None
    got_meta = False

    try:
        with open(jsonl_path) as fh:
            for i, line in enumerate(fh):
                if i > 150:
                    break
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Extract basic metadata from first line that has sessionId
                if not got_meta and data.get("sessionId"):
                    meta["sessionId"] = data["sessionId"]
                    meta["projectPath"] = data.get("cwd", "")
                    meta["gitBranch"] = data.get("gitBranch", "")
                    meta["created"] = data.get("timestamp", "")
                    got_meta = True

                # First user message (skip slash commands)
                if (data.get("type") == "user" and first_user_text is None):
                    msg = data.get("message", {})
                    content = msg.get("content", "") if isinstance(msg, dict) else ""
                    if isinstance(content, str):
                        cleaned = _clean_text(content)
                        if cleaned:
                            first_user_text = cleaned[:120]

                # Summary entry (keep last one — it's the most up-to-date)
                if data.get("type") == "summary":
                    summary = data.get("summary", "")

    except OSError:
        return None

    if not meta.get("sessionId"):
        return None

    meta["summary"] = summary or ""
    meta["firstPrompt"] = first_user_text or ""
    return meta


def _scan_all_jsonl():
    """Scan all project dirs and return {sessionId: (proj_dir, jsonl_path, mtime)}."""
    result = {}
    try:
        proj_dirs = os.listdir(PROJECTS_BASE)
    except OSError:
        return result

    for dirname in proj_dirs:
        proj_dir = os.path.join(PROJECTS_BASE, dirname)
        if not os.path.isdir(proj_dir):
            continue
        try:
            files = os.listdir(proj_dir)
        except OSError:
            continue
        for fname in files:
            if not fname.endswith(".jsonl"):
                continue
            sid = fname[:-6]  # strip .jsonl
            fpath = os.path.join(proj_dir, fname)
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            result[sid] = (proj_dir, fpath, mtime)

    return result


def _enrich_from_index(cache):
    """Supplement cache entries with data from sessions-index.json (summaries)."""
    for idx_path in glob.glob(os.path.join(PROJECTS_BASE, "*/sessions-index.json")):
        try:
            with open(idx_path) as f:
                raw = json.load(f)
            entries = raw.get("entries", raw) if isinstance(raw, dict) else raw
            if not isinstance(entries, list):
                continue
            for e in entries:
                sid = e.get("sessionId", "")
                if sid and sid in cache:
                    # Backfill summary if missing
                    if not cache[sid].get("summary") and e.get("summary"):
                        cache[sid]["summary"] = e["summary"]
                    if not cache[sid].get("firstPrompt") and e.get("firstPrompt"):
                        cache[sid]["firstPrompt"] = e["firstPrompt"]
                    if e.get("customTitle"):
                        cache[sid]["customTitle"] = e["customTitle"]
        except (OSError, json.JSONDecodeError):
            continue


def _get_index_max_mtime():
    """Get the max mtime of all sessions-index.json files."""
    max_mtime = 0
    for idx_path in glob.glob(os.path.join(PROJECTS_BASE, "*/sessions-index.json")):
        try:
            mtime = os.path.getmtime(idx_path)
            if mtime > max_mtime:
                max_mtime = mtime
        except OSError:
            continue
    return max_mtime


def load_all_sessions(force_rebuild=False):
    """Load all sessions using cache + incremental .jsonl scanning."""
    cache = {} if force_rebuild else _load_cache()
    meta = cache.pop("__meta__", {})

    # Scan filesystem for all .jsonl files (just stat, ~17ms)
    on_disk = _scan_all_jsonl()

    # Find sessions that need (re-)reading
    needs_read = []
    for sid, (proj_dir, fpath, mtime) in on_disk.items():
        cached = cache.get(sid)
        if cached and cached.get("_mtime", 0) >= mtime:
            continue  # Already cached and up-to-date
        needs_read.append((sid, fpath, mtime))

    # Remove sessions no longer on disk
    on_disk_ids = set(on_disk.keys())
    stale = [sid for sid in cache if sid not in on_disk_ids]
    for sid in stale:
        del cache[sid]

    # Read new/changed files
    for sid, fpath, mtime in needs_read:
        m = _extract_metadata(fpath)
        if m:
            m["_mtime"] = mtime
            m["modified"] = datetime.datetime.fromtimestamp(
                mtime, tz=datetime.timezone.utc
            ).isoformat()
            cache[sid] = m

    # Check if index files updated (for customTitle, summary backfill)
    idx_mtime = _get_index_max_mtime()
    need_save = bool(needs_read) or idx_mtime > meta.get("index_mtime", 0)

    if need_save:
        _enrich_from_index(cache)
        meta["index_mtime"] = idx_mtime
        cache["__meta__"] = meta
        _save_cache(cache)

    return list(cache.values())


# ── Session lookup ────────────────────────────────────────────────────────────

def _current_project_dir():
    """Encode cwd into the Claude project dir path (same encoding Claude Code uses)."""
    cwd = os.getcwd()
    encoded = cwd.replace("/", "-")
    return os.path.join(PROJECTS_BASE, encoded)


def _find_current_session_id():
    """Find the current session by most recently modified .jsonl in current project dir."""
    proj_dir = _current_project_dir()
    if not os.path.isdir(proj_dir):
        return None, proj_dir
    best_sid, best_mtime = None, 0
    for fname in os.listdir(proj_dir):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(proj_dir, fname)
        try:
            mtime = os.path.getmtime(fpath)
        except OSError:
            continue
        if mtime > best_mtime:
            best_mtime = mtime
            best_sid = fname[:-6]
    return best_sid, proj_dir


def _resolve_session_id(prefix):
    """Resolve a session ID prefix to a full session ID."""
    on_disk = _scan_all_jsonl()
    matches = [sid for sid in on_disk if sid.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches[0]  # best effort: return first match
    return None


def _find_index_path_for_session(session_id):
    """Find which project's sessions-index.json should contain this session."""
    on_disk = _scan_all_jsonl()
    if session_id in on_disk:
        proj_dir = on_disk[session_id][0]
        return os.path.join(proj_dir, "sessions-index.json"), proj_dir
    return None, None


# ── Display ──────────────────────────────────────────────────────────────────

def _clean_text(text):
    """Strip system tags and truncate for display."""
    if not text:
        return ""
    import re
    # Remove XML-style tags and their content (system reminders, caveats, etc.)
    text = re.sub(r"<[a-z_-]+>.*?</[a-z_-]+>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _display_text(session):
    """Pick the best display text for a session."""
    raw = (
        session.get("customTitle")
        or session.get("summary")
        or session.get("firstPrompt")
        or "(no summary)"
    )
    cleaned = _clean_text(raw)
    return cleaned if cleaned else "(no summary)"


def _is_observer_session(session):
    """Check if this is an automated observer session (claude-mem, etc.)."""
    fp = session.get("firstPrompt", "").lower()
    pp = session.get("projectPath", "").lower()
    return (
        "observer-session" in pp
        or "claude-mem" in pp
        or "memory agent" in fp
        or "claude-mem" in fp
        or fp.startswith("analyze this conversation")
    )


def _has_content(session):
    """Check if session has meaningful content to display."""
    return bool(
        session.get("customTitle")
        or session.get("summary")
        or session.get("firstPrompt")
    )


def format_table(sessions, max_count=None):
    """Format sessions as a table string."""
    if max_count:
        sessions = sessions[:max_count]
    if not sessions:
        print("  (no sessions found)")
        return

    print(f" {'#':>3}  {'Session ID':<10} {'Age':<8} {'Project':<14} {'Branch':<22} {'Summary'}")
    print(f" {'---':>3}  {'-'*10:<10} {'--------':<8} {'-'*14:<14} {'-'*22:<22} {'-'*40}")
    for i, s in enumerate(sessions, 1):
        sid = s.get("sessionId", "")[:8]
        proj = project_name(s.get("projectPath", ""))
        branch = s.get("gitBranch", "") or ""
        if branch == "HEAD":
            branch = ""
        summary = _display_text(s)
        age = time_ago(s.get("modified", ""))
        if len(branch) > 21:
            branch = branch[:20] + "…"
        if len(summary) > 50:
            summary = summary[:49] + "…"
        print(f" {i:>3}  {sid:<10} {age:<8} {proj:<14} {branch:<22} {summary}")


def print_resume_tip():
    print("\nResume: claude --resume <session-id-or-keyword>")


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_list(args):
    show_all = "--all" in args
    clean_args = [a for a in args if a != "--all"]
    count = int(clean_args[0]) if clean_args else 10
    sessions = load_all_sessions()
    sessions = [s for s in sessions if not _is_observer_session(s)]
    sessions.sort(key=lambda e: parse_dt(e.get("modified", "")), reverse=True)

    if not show_all:
        all_count = len(sessions)
        sessions = [s for s in sessions if _has_content(s)]
        hidden = all_count - len(sessions)
    else:
        hidden = 0

    showing = min(count, len(sessions))
    print(f"Recent sessions ({len(sessions)} total, showing {showing})\n")
    format_table(sessions, max_count=count)
    if hidden > 0:
        print(f"\n  ({hidden} empty sessions hidden. Use --all to show all)")
    print_resume_tip()


def cmd_find(args):
    if not args:
        print("Usage: ss.py find <keyword> [--project NAME] [--since Nd]")
        sys.exit(1)

    keyword = ""
    project_filter = ""
    since_days = 0
    i = 0
    positional = []
    while i < len(args):
        if args[i] == "--project" and i + 1 < len(args):
            project_filter = args[i + 1].lower()
            i += 2
        elif args[i] == "--since" and i + 1 < len(args):
            since_str = args[i + 1]
            since_days = int(since_str.rstrip("d"))
            i += 2
        else:
            positional.append(args[i])
            i += 1
    keyword = " ".join(positional).lower()

    sessions = load_all_sessions()
    sessions = [s for s in sessions if not _is_observer_session(s)]
    now = datetime.datetime.now(datetime.timezone.utc)

    # Filter: since
    if since_days > 0:
        cutoff = now - datetime.timedelta(days=since_days)
        sessions = [s for s in sessions if parse_dt(s.get("modified", "")) >= cutoff]

    # Filter: project
    if project_filter:
        sessions = [
            s for s in sessions
            if project_filter in project_name(s.get("projectPath", ""))
        ]

    # Filter: keyword
    if keyword:
        matched = []
        for s in sessions:
            blob = " ".join([
                s.get("summary", ""),
                s.get("firstPrompt", ""),
                s.get("customTitle", ""),
                s.get("gitBranch", ""),
                s.get("projectPath", ""),
            ]).lower()
            if keyword in blob:
                matched.append(s)
        sessions = matched

    # Sort
    sessions.sort(key=lambda e: parse_dt(e.get("modified", "")), reverse=True)

    # Dedup by sessionId
    seen = set()
    deduped = []
    for s in sessions:
        sid = s.get("sessionId", "")
        if sid and sid not in seen:
            seen.add(sid)
            deduped.append(s)
    sessions = deduped

    # Output
    parts = []
    if keyword:
        parts.append(f'keyword="{keyword}"')
    if project_filter:
        parts.append(f"project={project_filter}")
    if since_days:
        parts.append(f"since={since_days}d")
    query = ", ".join(parts) or "all"

    print(f"Search: {query} — {len(sessions)} found\n")
    format_table(sessions, max_count=30)
    if sessions:
        print_resume_tip()


def cmd_context():
    """Output current git context as JSON for the rename step."""
    import subprocess

    data = {"cwd": os.getcwd()}

    try:
        data["branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        data["branch"] = ""

    try:
        data["status"] = subprocess.check_output(
            ["git", "status", "--short"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        data["status"] = ""

    try:
        data["recent_commits"] = subprocess.check_output(
            ["git", "log", "--oneline", "-3"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        data["recent_commits"] = ""

    data["project"] = project_name(data["cwd"])

    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_clean(args):
    """Clean up old or empty sessions."""
    clean_empty = "--empty" in args
    confirm = "--confirm" in args
    older_days = 0

    for i, a in enumerate(args):
        if a == "--older" and i + 1 < len(args):
            older_days = int(args[i + 1].rstrip("d"))

    if not clean_empty and older_days == 0:
        print("Usage: ss.py clean [--empty] [--older Nd] [--confirm]")
        print("\nOptions:")
        print("  --empty    Sessions with no user message")
        print("  --older Nd Sessions older than N days")
        print("  --confirm  Actually delete (default: dry run)")
        print("\nWhen both flags are used, only sessions matching BOTH are removed.")
        sys.exit(0)

    sessions = load_all_sessions()
    on_disk = _scan_all_jsonl()
    now = datetime.datetime.now(datetime.timezone.utc)

    to_delete = []
    for s in sessions:
        sid = s.get("sessionId", "")
        if not sid or sid not in on_disk:
            continue

        is_empty = not _has_content(s)
        is_old = False
        if older_days > 0:
            modified = parse_dt(s.get("modified", ""))
            cutoff = now - datetime.timedelta(days=older_days)
            is_old = modified < cutoff

        if clean_empty and older_days > 0:
            if is_empty and is_old:
                to_delete.append((s, on_disk[sid]))
        elif clean_empty and is_empty:
            to_delete.append((s, on_disk[sid]))
        elif older_days > 0 and is_old:
            to_delete.append((s, on_disk[sid]))

    if not to_delete:
        print("No sessions match the criteria.")
        return

    to_delete.sort(key=lambda x: parse_dt(x[0].get("modified", "")))

    label = "Will delete" if confirm else "Would delete"
    print(f"{label} {len(to_delete)} sessions:\n")
    for s, (proj_dir, fpath, mtime) in to_delete[:20]:
        sid = s.get("sessionId", "")[:8]
        age = time_ago(s.get("modified", ""))
        proj = project_name(s.get("projectPath", ""))
        summary = _display_text(s)
        if len(summary) > 40:
            summary = summary[:39] + "…"
        print(f"  {sid}  {age:<8} {proj:<14} {summary}")

    if len(to_delete) > 20:
        print(f"  ... and {len(to_delete) - 20} more")

    if confirm:
        deleted = 0
        for s, (proj_dir, fpath, mtime) in to_delete:
            try:
                os.remove(fpath)
                deleted += 1
            except OSError:
                pass
        print(f"\nDeleted {deleted} session files.")
        load_all_sessions(force_rebuild=True)
        print("Cache rebuilt.")
    else:
        print(f"\nDry run. Add --confirm to actually delete.")


def cmd_rename(args):
    """Rename a session by appending a custom-title entry to .jsonl.

    This mirrors what Claude Code's native /rename does:
    - Appends {"type":"custom-title","customTitle":"...","sessionId":"..."} to .jsonl
    - Updates sessions-index.json for immediate visibility
    - Updates ss cache
    """
    session_id = None
    name_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--id" and i + 1 < len(args):
            session_id = args[i + 1]
            i += 2
        else:
            name_parts.append(args[i])
            i += 1
    name = " ".join(name_parts).strip()

    if not name:
        print("Usage: ss.py rename <name> [--id <session-id>]")
        sys.exit(1)

    # Auto-detect current session if no --id
    if not session_id:
        session_id, _ = _find_current_session_id()
        if not session_id:
            print("Error: Could not detect current session. Use --id <session-id>.")
            sys.exit(1)

    # Resolve prefix to full ID
    full_id = _resolve_session_id(session_id) or session_id

    # Find session on disk
    on_disk = _scan_all_jsonl()
    if full_id not in on_disk:
        print(f"Error: Session {session_id} not found on disk.")
        sys.exit(1)

    proj_dir, jsonl_path, _ = on_disk[full_id]

    # 1. Append custom-title entry to .jsonl (source of truth for Claude Code)
    title_entry = json.dumps({
        "type": "custom-title",
        "customTitle": name,
        "sessionId": full_id,
    }, ensure_ascii=False)
    with open(jsonl_path, "a") as f:
        f.write(title_entry + "\n")

    # 2. Update sessions-index.json for immediate visibility
    idx_path = os.path.join(proj_dir, "sessions-index.json")
    if os.path.isfile(idx_path):
        try:
            with open(idx_path) as f:
                index_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            index_data = {"version": 1, "entries": []}

        found = False
        for entry in index_data.get("entries", []):
            if entry.get("sessionId") == full_id:
                entry["customTitle"] = name
                found = True
                break

        if not found:
            index_data.setdefault("entries", []).append({
                "sessionId": full_id,
                "fullPath": jsonl_path,
                "customTitle": name,
                "projectPath": os.getcwd(),
                "isSidechain": False,
            })

        with open(idx_path, "w") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # 3. Update ss cache
    cache = _load_cache()
    if full_id in cache:
        cache[full_id]["customTitle"] = name
        _save_cache(cache)

    print(f"Renamed: {name}")
    print(f"Session: {full_id[:8]}")


def cmd_copy(args):
    """Copy a resume command to clipboard."""
    import subprocess

    if not args:
        print("Usage: ss.py copy <session-id-prefix>")
        sys.exit(1)

    prefix = args[0]
    full_id = _resolve_session_id(prefix)
    if not full_id:
        print(f"Error: No session matching '{prefix}'")
        sys.exit(1)

    cmd = f"claude --resume {full_id}"
    try:
        subprocess.run(["pbcopy"], input=cmd.encode(), check=True)
        print(f"Copied to clipboard: {cmd}")
    except (OSError, subprocess.CalledProcessError):
        print(f"Resume command: {cmd}")
        print("(pbcopy not available)")


def cmd_rebuild():
    """Force rebuild the cache from scratch."""
    import time
    t0 = time.time()
    sessions = load_all_sessions(force_rebuild=True)
    elapsed = time.time() - t0
    print(f"Cache rebuilt: {len(sessions)} sessions indexed in {elapsed:.2f}s")
    print(f"Cache: {CACHE_PATH}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "list":
        cmd_list(args)
    elif cmd == "find":
        cmd_find(args)
    elif cmd == "rename":
        cmd_rename(args)
    elif cmd == "copy":
        cmd_copy(args)
    elif cmd == "context":
        cmd_context()
    elif cmd == "clean":
        cmd_clean(args)
    elif cmd == "rebuild":
        cmd_rebuild()
    else:
        # Treat unknown command as keyword search
        cmd_find([cmd] + args)


if __name__ == "__main__":
    main()
