# Claude Code Marketplace

Claude Code plugins by [noellch](https://github.com/noellch).

> All plugins in this marketplace use the `nl-` prefix (noellch).

## Installation

```bash
/plugin marketplace add noellch/noel-claude-code-marketplace
```

## Available Plugins

### nl-asana-ticket

Asana ticket creation and issue investigation for Crescendo Lab.

```bash
/plugin install nl-asana-ticket@noel
```

**Skills:**

| Skill | Trigger | Description |
|-------|---------|-------------|
| `asana-ticket` | "create ticket", "open bug" | Standardized ticket creation with project routing and custom fields |
| `analyze-issue` | "分析 issue", "analyze ticket" | Systematic investigation workflow for Support tickets |

### nl-living-docs

Detect documentation drift from code changes with severity-ranked reports and actionable diff suggestions.

```bash
/plugin install nl-living-docs@noel
```

- Systematic drift detection across API docs, READMEs, and code-level docs (JSDoc/docstring)
- Every finding includes before/after diff suggestions ready to apply
- Two modes: manual audit (`/living-docs`) and incremental post-commit detection
- Severity scoring: CRITICAL (causes failures) / WARNING (incomplete) / INFO (cosmetic)

### nl-pr-comment-resolve

Resolve PR review comments with structured workflow: fetch, evaluate, implement, commit, and reply with commit SHA links.

```bash
/plugin install nl-pr-comment-resolve@noel
```

- Batch confirmation — present all comments, ask once which to handle/skip
- Per-comment evaluation — assess correctness before blindly implementing
- Atomic commits per fix with comment ID reference
- Reply to specific comment with clickable commit SHA link

### nl-research-plan-execute

Structured feature development workflow combining codebase research, annotated planning with human review cycles, and subagent-driven execution with dual review gates.

```bash
/plugin install nl-research-plan-execute@noel
```

- Research phase: deep codebase exploration before planning
- Annotated plan with human review/approval cycle
- Subagent-driven execution with code review between tasks

### nl-resource-digest

Deep analysis of public resources (URLs, articles, GitHub repos, tweets, tech news) with structured summaries, critical opinions, and actionable insights.

```bash
/plugin install nl-resource-digest@noel
```

- Summarize → Opine → Advise (three-layer analysis)
- Supports articles, blog posts, GitHub repos, tweets, tech news
- Triggers on "幫我整理", "summarize this", "分析這篇"

### nl-terminal-diagrams

Render precise, perfectly-aligned diagrams in the terminal using `graph-easy`.

```bash
/plugin install nl-terminal-diagrams@noel
```

- Flowcharts and architecture diagrams via `graph-easy --as=boxart`
- Automatic method selection: graph-easy for graphs, hand-draw for sequence diagrams and trees
- Supports both Graph::Easy native syntax and DOT format input
- Requires: `brew install cpanminus && cpanm --local-lib=~/perl5 local::lib Graph::Easy`

## License

MIT
