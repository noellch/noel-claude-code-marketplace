"""Build a develop-based fixture for nl-create-pr: a local bare 'origin' whose HEAD is
develop (master only receives releases), a clone with CLAUDE.md PR policy and a zh-TW PR
template, and a feature branch that already carries two commits.

usage: python3 make_devrepo.py            # creates fixtures/devrepo.git + fixtures/devrepo
       python3 make_devrepo.py --reset    # recreates both from scratch
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BARE = ROOT / "devrepo.git"
WORK = ROOT / "devrepo"

if "--reset" in sys.argv:
    for d in (BARE, WORK):
        if d.exists():
            shutil.rmtree(d)
for d in (BARE, WORK):
    if d.exists():
        sys.exit(f"refusing: {d} exists (use --reset)")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def put(rel, text):
    p = WORK / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


BARE.mkdir()
git(BARE, "init", "-q", "--bare", "-b", "develop")
git(ROOT, "clone", "-q", str(BARE), str(WORK))
git(WORK, "config", "user.email", "fixture@example.com")
git(WORK, "config", "user.name", "fixture")
git(WORK, "checkout", "-q", "-b", "develop")

put("CLAUDE.md", """# reports-svc conventions

## PR Strategy

- Branch from `develop` and open every PR against `develop`; `master` only receives release PRs.
- One primary task per PR. Schema changes ship before the code that uses them.
- PR title in English, conventional commit style. PR body follows `.github/pull_request_template.md` (Traditional Chinese).
- Run tests with `python3 -m unittest discover -s tests` before pushing.
""")
put(".github/pull_request_template.md", """## 變更內容

<!-- 這個 PR 做了什麼，一句話 -->

## 原因

<!-- 為什麼需要這個改動 -->

## 測試方式

- [ ]

## Asana

<!-- 任務連結 -->
""")
put("app/__init__.py", "")
put("app/report.py", """def summarize(rows):
    total = sum(r["amount"] for r in rows)
    return {"count": len(rows), "total": total}
""")
put("tests/test_report.py", """import unittest

from app.report import summarize


class ReportTest(unittest.TestCase):
    def test_summarize(self):
        self.assertEqual(summarize([{"amount": 2}, {"amount": 3}]), {"count": 2, "total": 5})
""")
git(WORK, "add", "-A")
git(WORK, "commit", "-q", "-m", "init: reports service")
git(WORK, "push", "-q", "-u", "origin", "develop")
git(WORK, "checkout", "-q", "-b", "master")
git(WORK, "push", "-q", "-u", "origin", "master")
git(WORK, "checkout", "-q", "develop")
git(BARE, "symbolic-ref", "HEAD", "refs/heads/develop")
git(WORK, "remote", "set-head", "origin", "develop")

# the user's finished work: a feature branch with two commits, clean tree
git(WORK, "checkout", "-q", "-b", "feat/csv-export")
put("app/export.py", """import csv
import io

from app.report import summarize


def to_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["count", "total"])
    s = summarize(rows)
    writer.writerow([s["count"], s["total"]])
    return buf.getvalue()
""")
git(WORK, "add", "app/export.py")
git(WORK, "commit", "-q", "-m", "feat(export): add CSV export of the report summary")
put("tests/test_export.py", """import unittest

from app.export import to_csv


class ExportTest(unittest.TestCase):
    def test_to_csv(self):
        self.assertEqual(to_csv([{"amount": 2}, {"amount": 3}]), "count,total\\r\\n2,5\\r\\n")
""")
git(WORK, "add", "tests/test_export.py")
git(WORK, "commit", "-q", "-m", "test(export): cover to_csv")

print("origin HEAD:", git(BARE, "symbolic-ref", "HEAD"))
print("clone branch:", git(WORK, "branch", "--show-current"))
print("origin/HEAD ->", git(WORK, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"))
print("commits ahead of develop:", git(WORK, "rev-list", "--count", "origin/develop..HEAD"))
print("status:", repr(git(WORK, "status", "--porcelain")))
r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=WORK, capture_output=True, text=True)
print("tests:", r.stderr.strip().splitlines()[-1])
