"""Create a scratch PR with review threads for testing nl-pr-comment-resolve.

usage: python3 make_pcr_fixture.py <suffix> <clone-dir>

Creates branch scratch/pcr-fixture-<suffix> from origin/HEAD in <clone-dir>, adds a tiny
Python module + test + README, pushes, opens a PR, posts one review (5 inline comments +
a body) and one PR-level comment. Prints the PR URL. Leaves the clone on the new branch.

Items (7 total, > AskUserQuestion's 4-option limit):
  1 calc.py:2   Handle   guard b == 0
  2 calc.py:6   Handle   ```suggestion``` block (byte-for-byte); breaks test_percent → must update test
  3 calc.py:10  Discuss  "clamp is unused, delete it" — wrong, test_calc.py uses it
  4 test:8      Handle   add divide-by-zero test (same file as 5)
  5 test:11     Handle   nit assertAlmostEqual (same file as 4)
  6 review body          claim to verify (README "safe to delete")
  7 issue comment        PR-level ask: reply "ack"
"""
import json
import pathlib
import subprocess
import sys

suffix, clone = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
branch = f"scratch/pcr-fixture-{suffix}"


def run(*args, **kw):
    return subprocess.run(args, cwd=clone, check=True, capture_output=True, text=True, **kw).stdout.strip()


def put(rel, text):
    p = clone / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


assert run("git", "status", "--porcelain") == "", "clone is dirty"
run("git", "fetch", "-q", "origin")
run("git", "checkout", "-q", "-b", branch, "origin/HEAD")

put("scratch/pcr_fixture/calc.py", """def divide(a, b):
    return a / b


def percent(part, whole):
    return divide(part, whole) * 100


def clamp(x, lo, hi):
    return max(lo, min(x, hi))
""")
put("scratch/pcr_fixture/test_calc.py", """import unittest

from calc import clamp, divide, percent


class CalcTest(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(10, 4), 2.5)

    def test_percent(self):
        self.assertEqual(percent(1, 3), 33.33333333333333)

    def test_clamp(self):
        self.assertEqual(clamp(15, 0, 10), 10)
""")
put("scratch/pcr_fixture/README.md", """# pcr_fixture

Scratch fixture for nl-pr-comment-resolve review-thread tests. Safe to delete.

Run tests: `python3 -m unittest discover -s scratch/pcr_fixture`
""")

run("git", "add", "scratch")
run("git", "commit", "-q", "-m", f"scratch: fixture for nl-pr-comment-resolve review-thread tests ({suffix})")
run("git", "push", "-q", "-u", "origin", branch)

base = run("git", "rev-parse", "--abbrev-ref", "origin/HEAD").split("/", 1)[1]
pr_url = run(
    "gh", "pr", "create", "--base", base, "--head", branch,
    "--title", f"scratch: pr-comment-resolve fixture {suffix} (do not merge)",
    "--body", "Scratch PR used as a fixture for nl-pr-comment-resolve RED/GREEN runs. "
              "Will be closed afterwards. Do not merge.",
)
pr = int(pr_url.rstrip("/").rsplit("/", 1)[1])

review = {
    "event": "COMMENT",
    "body": "Overall fine for a scratch module. One claim to verify before merge: the README says "
            "this module is \"safe to delete\" — please confirm nothing outside scratch/ imports it "
            "and reply here with what you checked.",
    "comments": [
        {"path": "scratch/pcr_fixture/calc.py", "line": 2, "side": "RIGHT",
         "body": "Guard `b == 0` and raise `ValueError(\"whole must not be zero\")` before dividing; "
                 "a bare `ZeroDivisionError` leaks the implementation detail to callers."},
        {"path": "scratch/pcr_fixture/calc.py", "line": 6, "side": "RIGHT",
         "body": "Callers display this, so round it:\n```suggestion\n    return round(divide(part, whole) * 100, 2)\n```"},
        {"path": "scratch/pcr_fixture/calc.py", "line": 10, "side": "RIGHT",
         "body": "`clamp` is unused anywhere in the repo — please delete it so we do not ship dead code."},
        {"path": "scratch/pcr_fixture/test_calc.py", "line": 8, "side": "RIGHT",
         "body": "Add a test that `divide(1, 0)` raises `ValueError` once the guard lands."},
        {"path": "scratch/pcr_fixture/test_calc.py", "line": 11, "side": "RIGHT",
         "body": "nit: use `assertAlmostEqual` here; exact float equality is brittle."},
    ],
}
review_json = clone.parent / f"pcr-review-{suffix}.json"
review_json.write_text(json.dumps(review))
review_id = run("gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{pr}/reviews", "--input", str(review_json), "--jq", ".id")
run("gh", "pr", "comment", str(pr), "--body",
    "PR-level ask (not on any line): just reply \"ack\" to this comment so we know PR-level comments are handled.")

threads = run(
    "gh", "api", "graphql", "-F", f"pr={pr}", "-f",
    "query=query($pr:Int!){repository(owner:\"noellch\",name:\"noel-claude-code-marketplace\"){"
    "pullRequest(number:$pr){reviewThreads(first:20){nodes{isResolved path line}}}}}",
    "--jq", ".data.repository.pullRequest.reviewThreads.nodes | length",
)
print(f"PR={pr_url} review_id={review_id} threads={threads} branch={branch}")
