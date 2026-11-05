# Dependency commands (Phase 1)

Run every column for the detected stack. Record the exact command beside each table in the report. If a tool is missing, install it or write "tool unavailable: <name>" in the table — never fill the column from memory.

## Output table

| package | version | column | direct? | prod-path? | reachable? | fix / target | severity |
|---|---|---|---|---|---|---|---|

- **direct?** — listed in the manifest (`pnpm why <pkg>`, `npm ls <pkg>`, `pipdeptree -r -p <pkg>`, `go mod why -m <module>`).
- **prod-path?** — not under devDependencies / dev group / test-only usage.
- **reachable?** — for front-end bundles: is the package imported by shipped code? Grep imports first; if the project has a build or bundle-analyser script, run it (it writes only to its output directory) and search the output for the package. For back-ends: is the vulnerable function on a request or job path? Write 推測 if you cannot tell — and then the row cannot be downgraded to LOW on "unreachable".
- **severity** — see mapping below.

## Node (pnpm / npm / yarn)

```bash
# Vulnerable
pnpm audit --prod --json          # production tree only
pnpm audit --json                 # full tree, for the dev-only column
pnpm why <pkg>                    # direct vs transitive, which parent pulls it
# npm: npm audit --omit=dev --json ; npm ls <pkg>
# yarn: yarn npm audit --all --json ; yarn why <pkg>

# Outdated
pnpm outdated                     # add -r for workspaces
# npm outdated ; yarn outdated

# Unused (leads — confirm each)
pnpm dlx knip --dependencies      # preferred; drop the flag only if you also want unused exports/files
npx depcheck --ignores="@types/*,eslint-*,prettier,postcss"   # fallback when knip cannot load a config
```

If knip fails to load a config file (e.g. a Playwright or Storybook config), note the failure beside the table — the list is incomplete — and run depcheck as the second source. Do not report a package as unused on one tool's word.

Before any of the above, check the installed tree matches the lockfile (`pnpm install --frozen-lockfile --offline` as a dry check, or compare `pnpm ls --depth 0` with the lockfile). `pnpm audit` reads the **lockfile**; `pnpm outdated`'s *Current* column reads **node_modules**. If they differ, say so in the report header and prefer the lockfile numbers.

Confirm an "unused" lead before reporting: grep the package name in config files (`vite.config.*`, `eslint.config.*`, `postcss.config.*`, `tsconfig*.json`, `.github/workflows`), `package.json` scripts, and `import type` sites. A type-only import belongs in devDependencies, not removal.

Packages installed from a URL or tarball (not the registry) bypass `audit`; list them separately as MEDIUM with "not covered by registry audit".

## Python (pip / pyproject / poetry / uv)

```bash
# Vulnerable
pip-audit -r requirements.txt --desc on      # or: pip-audit (inside the venv)
# poetry: poetry export -f requirements.txt | pip-audit -r /dev/stdin
# uv:     uv pip freeze | pip-audit -r /dev/stdin

# Outdated
pip list --outdated --format=columns
# poetry show --outdated ; uv pip list --outdated

# Unused (leads — confirm each; package name != import name)
grep -v '^#' requirements.txt | grep -v '^$' | sed 's/[=<>!;].*//' | while read pkg; do
  import_name=$(echo "$pkg" | tr '[:upper:]' '[:lower:]' | sed 's/-/_/g')
  count=$(grep -rl "$import_name" --include='*.py' . 2>/dev/null | grep -v '/.venv/\|/.claude/' | wc -l)
  [ "$count" -eq 0 ] && echo "LEAD unused: $pkg"
done
```

Known name mismatches: Pillow → PIL, psycopg2-binary → psycopg2, PyYAML → yaml, beautifulsoup4 → bs4, scikit-learn → sklearn. Also check `INSTALLED_APPS`, Celery / gunicorn / pytest plugins, and `pyproject.toml` entry points before calling a package unused. Dev tools in the production group (ipython, debug toolbars) are a MEDIUM finding, not "unused".

## Go

```bash
# Vulnerable (call-graph aware: only reachable vulns by default)
govulncheck ./...
govulncheck -scan package ./...              # broader: any imported package

# Outdated
go list -m -u all | grep '\[' | grep -v '// indirect'

# Unused
go mod tidy -diff                            # Go ≥ 1.23: shows what tidy would drop
# older: go mod tidy -v 2>&1 | grep unused
```

## Severity mapping (single scale with the rest of the audit)

| Dependency condition | Severity | Note |
|---|---|---|
| Critical/High CVE, direct or transitive, **reachable** on a prod path | CRITICAL | Fix today; prefer the patch release |
| Medium CVE on a prod path; High CVE dev-only | HIGH | This sprint |
| Core framework 2+ majors behind (Django, React, Vite) | MEDIUM | Plan an epic; upgrade one step at a time |
| Transitive **and** unreachable CVE of any level | LOW | Note the parent; fix lands when the parent updates |
| Minor / patch behind | LOW | Bundle into a maintenance PR |
| Unused (confirmed) | LOW | Remove after confirming no side-effect imports |
| Installed from a non-registry URL | MEDIUM | Not covered by audit; pin a checksum or move to the registry |

## Update decision

```
Outdated package found
  ├─ Has CVE? → must update; prefer patch release
  ├─ Patch (x.y.Z)? → update directly, low risk
  ├─ Minor (x.Y.0)? → update, run CI to confirm
  ├─ Major (X.0.0)?
  │   ├─ Core framework? → separate branch, incremental upgrade
  │   ├─ Tooling (linter, formatter)? → low risk, upgrade directly
  │   └─ Narrow usage (1–2 files)? → low cost, upgrade directly
  └─ Archived / unmaintained? → find a replacement, plan migration
```

## Gotchas

- `pnpm audit` counts every path to a vulnerable version; the same CVE through five parents is one finding, listed once with its parents.
- Front-end: a server-only transitive (body-parser, form-data via a Node SDK) is unreachable in the browser bundle — LOW, and suggest moving the parent to devDependencies if it is type-only.
- `govulncheck` default already does reachability; `-scan package` widens it and raises false positives.
- Django must be upgraded one minor at a time (3.2 → 4.0 → 4.1 → 4.2); run deprecation checks at each step.
- Exclude `.venv/`, `node_modules/`, `.claude/worktrees/` (full repo copies) from every grep or counts multiply.
