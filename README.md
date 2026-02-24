# Claude Code Marketplace

Claude Code plugins by [noellch](https://github.com/noellch).

> All plugins in this marketplace use the `nl-` prefix (noellch).

## Installation

```bash
/plugin marketplace add noellch/noel-claude-code-marketplace
```

## Available Plugins

> Plugins are listed in alphabetical order.

### nl-pr-comment-resolve

Resolve PR review comments with structured workflow: fetch, evaluate, implement, commit, and reply with commit SHA links.

```bash
/plugin install nl-pr-comment-resolve@noel
```

Features:
- Batch confirmation — present all comments, ask once which to handle/skip
- Per-comment evaluation — assess correctness before blindly implementing
- Atomic commits per fix with comment ID reference
- Reply to specific comment with clickable commit SHA link
- Tracking table with status updates throughout the process

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

**asana-ticket features:**
- Automatic project routing (MAAC / QA Bug Tracking / Technical Debt)
- Correct custom field GIDs per project
- Consistent title prefixes and description templates

**analyze-issue features:**
- 5-phase investigation: gather context → form hypothesis → verify in code → assess impact → output action items
- Prevents vague conclusions with required code verification
- Structured output format with file:line references

## License

MIT
