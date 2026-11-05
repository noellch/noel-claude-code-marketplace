# Lens checklists (Phase 2)

One subagent per lens. Fill the dispatch prompt below, paste in the lens's section, and send. Checks are leads; the agent turns a lead into a finding only by reading the decisive lines.

## Dispatch prompt (fill the `<…>`)

```
You are auditing one lens of a repository. Read-only: do not edit, create, or commit anything inside the repo. You cannot ask the user; unknowns go to your "did not cover" list.

Repo: <absolute path>
Stack: <e.g. React 19 + TypeScript, pnpm / Django 4.2 + DRF, pip / Go 1.23>
Lens: <security | hotspots | quality | tests-ci | build-ops>
Already enforced by lint/type-check/CI (never report these): <list from Phase 0>
Out of scope (do not spend time here): <list from Phase 0>
Exclude from every grep: node_modules/, .venv/, dist/, build/, .claude/worktrees/, generated files, test fixtures.

Checks for this lens:
<paste the lens section below, or give this file's absolute path plus the heading "## Lens: <name>">

Rules:
1. A grep count is a lead, not a finding. To report it, sample ≥ 3 hits, read them, cite the sampled file:line, and state the count as an order of magnitude ("~60").
2. Cite the decisive line. For security: the line where the check is missing or the unsafe call happens — not the route, decorator, or trigger. If you did not reach it, tag the finding 推測.
3. Evidence tier on every finding: 實證 (you ran something and saw output) / 讀碼 (read, did not run) / 推測 (needs confirmation). CRITICAL and HIGH need at least 讀碼.
4. Severity and effort by the lens rule. If a check's severity rule does not fit, say why in the finding.
5. Do not report anything on the already-enforced list, and nothing a linter or compiler would catch.

Return ONLY:
FINDINGS (one block each):
  id: <lens>-<n>
  severity: CRITICAL|HIGH|MEDIUM|LOW
  evidence: 實證|讀碼|推測
  location: file:line[, file:line]
  detection: <command run or path read>
  issue: <one or two sentences>
  recommendation: <one concrete change>
  effort: S|M|L
DID NOT COVER: <bullet list of what you skipped or could not reach, with why>
STRENGTHS: <≤ 5 bullets of things done well, with file:line>
```

## Exclusions (all lenses)

Never report: placeholders in `.env.example` or docs; test fixtures and mocks; generated or vendored code; sample/demo directories; anything behind a lint-ignore comment that the project's convention docs explicitly allow.

---

## Lens: security

| # | Check | Detection | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| 1 | Hardcoded secrets or default secrets without fail-fast | grep `AKIA[0-9A-Z]{16}`, `-----BEGIN .* PRIVATE KEY`, `SECRET_KEY\s*=\s*['"]`, `os.environ.get('…', '<literal>')`; read settings for defaults used outside local | CRITICAL if real credential; HIGH if a usable default survives in non-local env | Remove literal; fail at startup when unset outside local | S–M |
| 2 | Injection: SQL / shell / template | `.raw(`, `.extra(`, `cursor.execute(f"`, string-built SQL; `subprocess(… shell=True`; `mark_safe`, `\|safe`; `dangerouslySetInnerHTML`, `innerHTML =` | CRITICAL if user input reaches it; HIGH if internal input | Parameterise; sanitise with the stack's library | S–M |
| 3 | Missing authorization on write endpoints | For each ViewSet / handler with update/delete: is object-level ownership (org, tenant, owner) checked on **every** method, including the ones inherited from mixins? Read the method that handles the verb, not the class decorator | CRITICAL if cross-tenant write; HIGH if cross-user read | Override or add a permission class covering every verb | S–M |
| 4 | Token and session handling | Where are access/refresh tokens stored (localStorage vs httpOnly cookie)? Cookie flags (`Secure`, `HttpOnly`, `SameSite`)? Token lifetime and rotation? | HIGH if long-lived token readable by JS and no CSP | httpOnly cookie, or short-lived access + rotation + CSP | M–L |
| 5 | Crypto misuse | AES without MAC (CBC/ECB), `md5`/`sha1` for anything security-related, home-grown crypto, static IV | CRITICAL if used for auth tokens; HIGH otherwise | AEAD (GCM) or signed tokens; vetted library | M |
| 6 | Unverified inbound callbacks and webhooks | For each endpoint that receives provider callbacks: is the signature or shared secret verified **in that view**? | HIGH if it mutates state; MEDIUM if read-only | Verify signature before any side-effect | S–M |
| 7 | Trusting client-controlled headers | IP allow-lists reading `X-Forwarded-For[0]`; `Host` used to build URLs | HIGH if gating auth; MEDIUM otherwise | Take the proxy-appended hop; configure trusted proxies | S |
| 8 | Input validation and CORS | Endpoints accepting raw dicts, file uploads without type/size checks, `CORS_ALLOW_ALL_ORIGINS`, wildcard with credentials | HIGH for uploads/wildcard with credentials; MEDIUM otherwise | Schema validation at the boundary; explicit origins | S–M |
| 9 | CI/CD trust boundary | `.github/workflows`: missing top-level `permissions:`; `pull_request_target` or `issue_comment` that checks out the PR head and runs it with secrets; secrets echoed in logs | CRITICAL if PR head code runs with write token or secrets; HIGH for missing `permissions:` | Least-privilege `permissions:`; gate on author association; never run untrusted code with secrets | S–M |
| 10 | Security headers (where the repo controls hosting) | `firebase.json`, nginx, `next.config`, Cloudflare config: CSP, HSTS, Referrer-Policy, Permissions-Policy, X-Content-Type-Options | MEDIUM (LOW if headers are known to be set at the edge — then 推測) | Add headers at the layer the repo controls | S |
| 11 | Outbound calls without timeout / retry bounds | `requests.<verb>(` without `timeout=`, `fetch` without `AbortController` in server code, Celery tasks without `time_limit` | MEDIUM (HIGH if on a request path that can hang workers) | Default timeout wrapper; task time limits | S–M |

## Lens: hotspots

| # | Check | Detection | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| 1 | Giant files and functions | `wc -l` top 20 source files; functions > 300 lines (AST or `grep -n "^def\|^function"` spacing) | HIGH if > 2000 lines and actively changed; MEDIUM > 1000; LOW otherwise | Split by responsibility; move pasted payloads to data files | M–L |
| 2 | Churn × size | `git log --since='6 months' --name-only --pretty=format: \| sort \| uniq -c \| sort -rn \| head -30`, cross with size | HIGH when a top-churn file is also a giant file | Prioritise these for refactor and tests | — |
| 3 | Pasted or generated data in source | Files whose header says "copy from …" or that are mostly literals | MEDIUM if bundled into a shipped chunk; LOW otherwise | Lazy-load JSON or fetch from the backend | M |
| 4 | Duplicate libraries by purpose | Two date libs, two chart stacks, two utility libs, two HTTP clients in the manifest; count imports of each | MEDIUM | Consolidate on one; migrate the minority | M–L |
| 5 | Duplicated logic | Same validation / error mapping / SQL fragment in ≥ 3 places (grep a distinctive line) | MEDIUM | Extract once | S–M |
| 6 | Stale TODO / FIXME / HACK | `git blame` the top hits; age > 12 months | LOW (MEDIUM if on an auth/payment path) | Resolve or delete; link an issue | S |
| 7 | Legacy shims and compat layers | `@deprecated`, `Legacy*`, `*Shim`, `*Compat`, `// backward compat` | MEDIUM if the new path has been live > 6 months | Remove after confirming no callers | S–M |

## Lens: quality

| # | Check | Detection | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| 1 | Type-safety escapes **not** already enforced | `: any`, `as any`, `as X` outside tests, `@ts-expect-error`, `# type: ignore`, `eslint-disable` by rule — only rules the already-enforced list does not block | MEDIUM for a concentrated cluster (one module); LOW diffuse | Type guards; targeted fixes in the cluster | S–M |
| 2 | Swallowed errors | `except Exception: pass`, empty `catch {}`, `.catch(() => {})`; sample 3 and read what is lost | HIGH if on a request/job path hiding failures; MEDIUM otherwise | Log with context or re-raise; narrow the exception | S |
| 3 | N+1 and unbounded queries | ORM access in loops, `SerializerMethodField` hitting relations, `.objects.all()` without pagination; React Query without `select`/pagination | HIGH on list endpoints; MEDIUM otherwise | `select_related` / `prefetch_related`; paginate | S–M |
| 4 | Mutable default arguments / shared module state | AST or grep `def .*=\[\]\|=\{\}` ; module-level caches without invalidation | MEDIUM | `None` default; explicit cache policy | S |
| 5 | Dead exports and unreachable code (leads) | `knip` / `ts-prune` / `vulture` output; confirm 3 | LOW (MEDIUM if a whole module is dead) | Delete; git keeps history | S |
| 6 | Compiler / interpreter strictness left off | `tsconfig`: `noUncheckedIndexedAccess`, `noImplicitOverride`; `pyright` strictness; `go vet` in CI | LOW (MEDIUM if a flag would catch an observed bug class) | Enable per flag in its own PR | M |
| 7 | Hand-written memoisation under React 19 | `useMemo\|useCallback\|memo(` order of magnitude; is React Compiler configured? | LOW | Trial the compiler on one route | M |

## Lens: tests-ci

| # | Check | Detection | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| 1 | Modules with zero tests | Per top-level module: count `*.test.*` / `test_*.py`; cross with e2e specs before reporting | HIGH if the module is on auth/payment/data-export; MEDIUM otherwise | Add characterisation tests on the critical path first | M |
| 2 | CI does not run what hooks run (or vice versa) | Read `.husky/*`, `.pre-commit-config.yaml`, workflows: which of lint / type-check / unit / e2e run where | MEDIUM | Make CI the superset | S |
| 3 | No coverage signal | Coverage collected but no threshold or trend; or not collected | LOW | Threshold on changed lines | S |
| 4 | Skipped / flaky markers | `it.skip`, `xit`, `@pytest.mark.skip`, `retries:` in e2e config; sample 3 | MEDIUM if on critical paths | Fix or delete with a reason | S–M |
| 5 | No dependency or SAST scan in CI | Workflows lack `audit`, `pip-audit`, `govulncheck`, CodeQL, bandit | MEDIUM | Add a scheduled scan job | S |
| 6 | Test quality on critical paths | Read 3 tests on auth/payment: do they assert behaviour or only "no exception"? | MEDIUM | Assert outcomes and failure branches | S–M |

## Lens: build-ops

| # | Check | Detection | Severity | Recommendation | Effort |
|---|---|---|---|---|---|
| 1 | Heavy libraries imported statically | Grep imports of chart/excel/editor/diagram libs; are they behind `lazy`/`import()`? Run the bundle analyser if a script exists; otherwise 推測 | MEDIUM | Dynamic import at the feature boundary | S–M |
| 2 | Source maps and secrets in build output | Build config `sourcemap`, post-build deletion ordering, upload-to-Sentry step | HIGH if maps or env secrets ship to the public bucket | Upload then delete, in one script; verify in CI | S |
| 3 | Cache headers vs hashed assets | Hosting config `Cache-Control` for `/static/*` vs filename hashing | LOW | `immutable` + long max-age for hashed files | S |
| 4 | Container hygiene | `Dockerfile`: `USER` set? default `CMD` is a dev server? multi-stage? pinned base image? | HIGH if root + dev server is the production entry; MEDIUM otherwise | Non-root user; production CMD; pin digest | S–M |
| 5 | Deprecated config flags | Config comments saying "remove after …", `legacy.*` options, deprecation warnings in the build log | LOW | Remove with the upgrade they belong to | S |
| 6 | Observability basics | Structured logging vs `console.log`/`print`; health/readiness endpoint; error tracking sample rates | MEDIUM if no health endpoint on a service; LOW otherwise | Add `/health`, structured logger | S–M |
| 7 | Background job limits | Celery / queue workers without time limits, retries, or idempotency keys | MEDIUM | Global `task_time_limit`; idempotent handlers | S–M |
