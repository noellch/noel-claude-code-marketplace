"""Stacked-PR fixture for nl-stack-pr: PR1 (feat/a → develop) was squash-merged and its
branch auto-deleted; PR2 (feat/b → feat/a) is still open and must be collapsed onto develop.

Layout (all local, no GitHub):
  stackrepo.git/   bare origin, HEAD = develop
  stackrepo/       the user's clone, checked out on feat/b, clean

History:
  develop: init ── S "feat(a): ... (#1)"   (squash of a1 a2 a3)
  feat/a : init ── a1 ── a2 ── a3           (deleted on origin after merge; the clone's
                                             origin/feat/a is STALE at a2 — it never fetched a3)
  feat/b : init ── a1 ── a2 ── b1           (branched from a2; the only commit that is PR2's own is b1)

Ground truth for the collapse:
  plain `git rebase origin/develop`                 → replays a1 a2 → conflict on f.txt
  `git rebase --onto origin/develop <a2 or a3>`     → replays only b1; origin/develop..feat/b == 1 commit
  final feat/b must contain g.txt (b1) and f.txt identical to develop's

usage: python3 make_stackrepo.py [--reset]
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BARE = ROOT / "stackrepo.git"
WORK = ROOT / "stackrepo"
SIDE = ROOT / "stackrepo-side"   # a second clone used to push a3 and perform the squash merge

if "--reset" in sys.argv:
    for d in (BARE, WORK, SIDE):
        if d.exists():
            shutil.rmtree(d)
for d in (BARE, WORK, SIDE):
    if d.exists():
        sys.exit(f"refusing: {d} exists (use --reset)")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def put(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def setup_identity(repo):
    git(repo, "config", "user.email", "fixture@example.com")
    git(repo, "config", "user.name", "fixture")


BARE.mkdir()
git(BARE, "init", "-q", "--bare", "-b", "develop")
git(ROOT, "clone", "-q", str(BARE), str(WORK))
setup_identity(WORK)

# develop
git(WORK, "checkout", "-q", "-b", "develop")
put(WORK, "CLAUDE.md", """# stack-svc conventions

## PR Strategy
- Branch from `develop` and open every PR against `develop`; `master` only receives release PRs.
- Squash merge; head branches are deleted automatically after merge.
- Run tests with `python3 -m unittest discover -s tests`.
""")
put(WORK, "f.txt", "base\n")
put(WORK, "tests/test_f.py", """import pathlib
import unittest


class FTest(unittest.TestCase):
    def test_f_has_base(self):
        self.assertIn("base", pathlib.Path("f.txt").read_text())
""")
git(WORK, "add", "-A")
git(WORK, "commit", "-q", "-m", "init: stack service")
git(WORK, "push", "-q", "-u", "origin", "develop")
git(BARE, "symbolic-ref", "HEAD", "refs/heads/develop")
git(WORK, "remote", "set-head", "origin", "develop")

# PR1: feat/a with a1 a2 (the clone sees these)
git(WORK, "checkout", "-q", "-b", "feat/a")
put(WORK, "f.txt", "base\na1\n")
git(WORK, "commit", "-q", "-am", "feat(a): add a1")
put(WORK, "f.txt", "base\na1\na2\n")
git(WORK, "commit", "-q", "-am", "feat(a): add a2")
git(WORK, "push", "-q", "-u", "origin", "feat/a")
a2 = git(WORK, "rev-parse", "HEAD")

# PR2: feat/b branched from a2 with its own commit b1
git(WORK, "checkout", "-q", "-b", "feat/b")
put(WORK, "g.txt", "b1\n")
git(WORK, "add", "g.txt")
git(WORK, "commit", "-q", "-m", "feat(b): add g.txt")
git(WORK, "push", "-q", "-u", "origin", "feat/b")

# Elsewhere: PR1 gets a3, then is squash-merged into develop and its branch deleted.
git(ROOT, "clone", "-q", str(BARE), str(SIDE))
setup_identity(SIDE)
git(SIDE, "checkout", "-q", "feat/a")
put(SIDE, "f.txt", "base\na1\na2\na3\n")
git(SIDE, "commit", "-q", "-am", "feat(a): add a3 (review fix)")
git(SIDE, "push", "-q", "origin", "feat/a")
a3 = git(SIDE, "rev-parse", "HEAD")
git(SIDE, "checkout", "-q", "develop")
git(SIDE, "merge", "--squash", "-q", "feat/a")
git(SIDE, "commit", "-q", "-m", "feat(a): add a1-a3 (#1)")
git(SIDE, "push", "-q", "origin", "develop")
git(SIDE, "push", "-q", "origin", "--delete", "feat/a")
squash = git(SIDE, "rev-parse", "HEAD")

# The user's clone: on feat/b, clean, has NOT fetched since (origin/feat/a stale at a2, origin/develop stale)
git(WORK, "branch", "-q", "-D", "feat/a")
git(WORK, "checkout", "-q", "feat/b")

print("PR1 head (final):", a3[:7], "| clone's stale origin/feat/a:", git(WORK, "rev-parse", "--short", "origin/feat/a"), "(= a2)")
print("squash commit on origin/develop:", squash[:7])
print("clone branch:", git(WORK, "branch", "--show-current"), "| status:", repr(git(WORK, "status", "--porcelain")))
print("remote branches:", git(WORK, "ls-remote", "--heads", "origin").replace("\n", " | "))
(ROOT / "stackrepo-ground-truth.txt").write_text(f"a2={a2}\na3={a3}\nsquash={squash}\n")
