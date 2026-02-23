# Claude Code Marketplace - Project Guidelines

## Plugin Naming Convention

All plugins in this marketplace use the `nl-` prefix (noellch).

Example: `nl-pr-comment-resolve`

## Project Structure

```
noel-claude-code-marketplace/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace registry (lists all plugins)
├── plugins/
│   └── nl-<plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json    # Plugin metadata
│       └── skills/
│           └── <skill-name>/
│               ├── SKILL.md   # Skill definition
│               └── references/ # Optional reference docs
├── templates/                 # Templates for new plugins/skills
└── CLAUDE.md                  # This file
```

## Shared Metadata (Copy for New Plugins)

```json
{
  "author": {
    "name": "noellch",
    "url": "https://github.com/noellch"
  },
  "homepage": "https://github.com/noellch/noel-claude-code-marketplace",
  "repository": "https://github.com/noellch/noel-claude-code-marketplace",
  "license": "MIT"
}
```

## Creating a New Plugin

### 1. Create Plugin Directory

```bash
mkdir -p plugins/nl-<plugin-name>/.claude-plugin
mkdir -p plugins/nl-<plugin-name>/skills/<skill-name>
```

### 2. Copy and Edit Templates

```bash
cp templates/plugin.json plugins/nl-<plugin-name>/.claude-plugin/plugin.json
cp templates/SKILL.md plugins/nl-<plugin-name>/skills/<skill-name>/SKILL.md
```

### 3. Register in Marketplace

Add entry to `.claude-plugin/marketplace.json`:

```json
{
  "name": "nl-<plugin-name>",
  "source": "./plugins/nl-<plugin-name>",
  "description": "<brief description>",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

## Quality Standards

### Plugin Ordering

All plugin lists MUST be sorted alphabetically by name in:
- `marketplace.json` plugins array
- `README.md` Available Plugins section

### SKILL.md Requirements

1. **Frontmatter** (required):
   ```yaml
   ---
   name: skill-name
   description: One-line description for when to use this skill
   ---
   ```

2. **Sections** (recommended): Title, When to Use, Usage, Notes

### plugin.json Requirements

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Must match directory name (with `nl-` prefix) |
| `version` | Yes | Semantic versioning (x.y.z) |
| `description` | Yes | One sentence, no period |
| `author` | Yes | Use shared metadata |
| `license` | Yes | MIT |

## Checklist Before Commit

- [ ] Plugin name has `nl-` prefix
- [ ] `plugin.json` has all required fields
- [ ] SKILL.md has valid frontmatter
- [ ] Plugin registered in `marketplace.json`
- [ ] Plugins sorted alphabetically in `marketplace.json` and `README.md`
- [ ] Version updated if modifying existing plugin
- [ ] README.md updated

## Git Conventions

### Commit Messages

```
<type>: <description>

Types: feat, fix, docs, refactor, chore
```
