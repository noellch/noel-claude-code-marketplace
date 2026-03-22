#!/usr/bin/env python3
"""Session Snap CLI — cross-project session search for Claude Code.

Usage:
    ss.py find <keyword> [--project NAME] [--since Nd]
    ss.py list [COUNT]
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
                if i > 50:
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
                    if isinstance(content, str) and not content.startswith("<"):
                        first_user_text = content[:120]

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
                    if not cache[sid].get("customTitle") and e.get("customTitle"):
                        cache[sid]["customTitle"] = e["customTitle"]
        except (OSError, json.JSONDecodeError):
            continue


def load_all_sessions(force_rebuild=False):
    """Load all sessions using cache + incremental .jsonl scanning."""
    cache = {} if force_rebuild else _load_cache()

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
    if needs_read:
        for sid, fpath, mtime in needs_read:
            meta = _extract_metadata(fpath)
            if meta:
                meta["_mtime"] = mtime
                meta["modified"] = datetime.datetime.fromtimestamp(
                    mtime, tz=datetime.timezone.utc
                ).isoformat()
                cache[sid] = meta

        # Enrich from index files (backfill summaries)
        _enrich_from_index(cache)
        _save_cache(cache)

    return list(cache.values())


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
    count = int(args[0]) if args else 10
    sessions = load_all_sessions()
    sessions = [s for s in sessions if not _is_observer_session(s)]
    sessions.sort(key=lambda e: parse_dt(e.get("modified", "")), reverse=True)
    print(f"Recent sessions ({len(sessions)} total, showing {min(count, len(sessions))})\n")
    format_table(sessions, max_count=count)
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
    elif cmd == "context":
        cmd_context()
    elif cmd == "rebuild":
        cmd_rebuild()
    else:
        # Treat unknown command as keyword search
        cmd_find([cmd] + args)


if __name__ == "__main__":
    main()
