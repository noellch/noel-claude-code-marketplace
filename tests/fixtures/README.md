# Skill test fixtures

Reproducible fixtures for the RED → GREEN → REFACTOR loop in `nl-writing-skills`. Each script builds a throwaway repo (or PR) with planted conditions, a fresh subagent runs the skill under test against it, and the result is checked against the ground truth listed here. Run history and verdicts: [skill-tdd-log.md](skill-tdd-log.md).

Generated repos land next to the scripts and are git-ignored. Run scripts with `python3 -I` from this directory.

| Script | Builds | Serves | Ground truth |
|--------|--------|--------|--------------|
| `build_fixtures.py` | `orders-clean/` and `orders-subtle/`: same base, feature branch `feature/order-pagination` with three commits | nl-code-review FP / FN measurement | clean: no defects (tie-breaker test gap is real). subtle: B1 `has_more` wrong at an exact page boundary; B2 `reports.first_order_date` broken by the ORDER BY flip in a file outside the diff; B3 paginated ORDER BY without a tiebreaker |
| `make_pcr_fixture.py <suffix> <clone-dir>` | A scratch PR on **this** repository from branch `scratch/pcr-fixture-<suffix>`: five inline review comments (one ```suggestion``` block, one false-premise ask, two on the same file), one review body, one PR-level comment | nl-pr-comment-resolve | seven items (more than AskUserQuestion's four-option limit); the "clamp is unused" ask is false; the review body and the PR-level comment need a reply path outside thread replies. **Close the PR afterwards; never merge it** (#19 was merged by mistake once and reverted in #23) |
| `make_devrepo.py [--reset]` | `devrepo.git/` (bare origin, HEAD = `develop`, plus `master`) and `devrepo/` clone with CLAUDE.md PR Strategy, a zh-TW `.github/pull_request_template.md`, and `feat/csv-export` carrying two commits | nl-create-pr (develop-based scenario) | base must resolve to `develop` from CLAUDE.md even when `gh` has no GitHub access; the existing branch must be kept; the repo template must shape the body |
| `make_stackrepo.py [--reset]` | `stackrepo.git/` (bare origin, HEAD = `develop`) and `stackrepo/` clone on `feat/b`: PR1 `feat/a` squash-merged and deleted, PR2 `feat/b` still open, the clone stale (never fetched PR1's last commit) | nl-stack-pr (collapse after a squash merge) | plain `git rebase origin/develop` replays PR1 and conflicts; `git rebase --onto origin/develop $(git merge-base feat/b <captured origin/feat/a>)` leaves exactly one own commit; PR1's final head is unreachable in the clone, so tips must be captured before the first fetch |

The main-based scenario for nl-create-pr needs no script: clone this repository, create a `feat/…` branch from `origin/main` with two README commits, and run the skill in dry mode (print `git push` / `gh pr create` instead of executing them).

The first nl-code-review fixture (`orders-svc`, SQL injection + rename with a stale `scripts/` caller + N+1 + weak assertion + compliant intentional swallow) was built by hand and is not scripted; its contents are described in the log.

## Running a loop

1. Build the fixture. Confirm tests are green on every branch and that the planted conditions manifest only where intended (each script prints this).
2. RED: dispatch a fresh subagent with only the skill path, the repo path, and the request. Ask it for the skill's output plus process notes (which commands it ran, which rule decided each judgment). Record failures and verbatim rationalizations in the log.
3. GREEN: edit the skill on a branch; rebuild or reset the fixture; dispatch again. Verify the outcome on disk or on GitHub, not from the agent's report.
4. REFACTOR: prune, then re-run at least a dry decision test for any sentence you changed.
