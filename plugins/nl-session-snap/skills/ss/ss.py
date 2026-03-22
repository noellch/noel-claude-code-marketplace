#!/usr/bin/env python3
"""Session Snap CLI — cross-project session search for Claude Code.

Usage:
    ss.py find <keyword> [--project NAME] [--since Nd]
    ss.py list [COUNT]
    ss.py context
    ss.py --help
"""

import json
import glob
import os
import sys
import datetime

SESSIONS_GLOB = os.path.expanduser("~/.claude/projects/*/sessions-index.json")


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


def load_all_sessions():
    """Load all sessions from every project's sessions-index.json."""
    all_sessions = []
    for fpath in glob.glob(SESSIONS_GLOB):
        try:
            with open(fpath) as f:
                raw = json.load(f)
            if isinstance(raw, dict) and "entries" in raw:
                entries = raw["entries"]
            elif isinstance(raw, list):
                entries = raw
            else:
                entries = []
            all_sessions.extend(entries)
        except (json.JSONDecodeError, OSError):
            continue
    return all_sessions


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
        summary = s.get("summary", "") or "(no summary)"
        age = time_ago(s.get("modified", ""))
        if len(branch) > 21:
            branch = branch[:20] + "…"
        if len(summary) > 50:
            summary = summary[:49] + "…"
        print(f" {i:>3}  {sid:<10} {age:<8} {proj:<14} {branch:<22} {summary}")


def print_resume_tip():
    print("\nResume: claude --resume <session-id-or-keyword>")


def cmd_list(args):
    count = int(args[0]) if args else 10
    sessions = load_all_sessions()
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
    else:
        # Treat unknown command as keyword search
        cmd_find([cmd] + args)


if __name__ == "__main__":
    main()
