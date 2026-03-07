---
name: terminal-diagrams
description: Use when you need to show a diagram, flowchart, architecture diagram, sequence diagram, or any visual graph in the terminal. Triggers on requests to "draw", "show me a diagram", "visualize the flow", or when explaining systems, processes, or architectures where a diagram would help.
---

# Terminal Diagrams

## Overview

Render precise, perfectly-aligned diagrams in the terminal using `graph-easy`. Never hand-draw ASCII flowcharts or architecture diagrams — they misalign. Use the tool.

## When to Use

- Drawing flowcharts, decision trees, process flows
- Showing architecture diagrams, component relationships
- Visualizing sequence/interaction flows
- Any directed graph with boxes and arrows

## When NOT to Use

- **Tree structures** (file trees, hierarchies): Hand-draw with `├── └──` — already reliable
- **Tables**: Use markdown tables or box-drawing characters — already reliable
- **Sequence diagrams with lifelines**: Hand-draw the traditional `│` lifeline style — Claude does these well and `graph-easy` converts them into graph layouts which loses the lifeline format
- **Inline simple arrows**: `A → B → C` in running text is fine

## Prerequisites

`graph-easy` must be installed:

```bash
# Install once
brew install cpanminus && cpanm --local-lib=~/perl5 local::lib Graph::Easy

# Required in PATH (add to ~/.zshrc)
export PATH="$HOME/perl5/bin:$PATH"
export PERL5LIB="$HOME/perl5/lib/perl5:$PERL5LIB"
```

## How to Render

**Always use `--as=boxart` for Unicode output.** It produces cleaner results than `--as=ascii`.

### Method 1: Graph::Easy native syntax (simpler)

```bash
echo '[ Start ] --> [ Process ] --> [ End ]
[ Process ] -- error --> [ Error Handler ] --> [ Start ]' | graph-easy --as=boxart
```

### Method 2: DOT format input (more control)

```bash
cat <<'DOT' | graph-easy --from=dot --as=boxart
digraph {
  rankdir=LR;
  "Client" -> "Server" [label="request"];
  "Server" -> "DB" [label="query"];
  "DB" -> "Server" [label="result"];
  "Server" -> "Client" [label="response"];
}
DOT
```

## Syntax Quick Reference

### Graph::Easy native format

| Pattern | Meaning |
|---------|---------|
| `[ A ] --> [ B ]` | A points to B |
| `[ A ] -- label --> [ B ]` | Labeled edge |
| `[ A ] --> [ B ], [ C ]` | A points to B and C |
| `[ A ] --> [ B ] --> [ C ]` | Chain |
| `[ A ] <-> [ B ]` | Bidirectional |
| `[ A ] ..> [ B ]` | Dotted edge |

### DOT format tips

| Pattern | Effect |
|---------|--------|
| `rankdir=LR` | Left-to-right layout |
| `rankdir=TB` | Top-to-bottom layout (default) |
| `[label="text"]` | Edge label |

## Diagram Patterns

### Flowchart with decisions

```bash
echo '[ Input ] --> [ Validate ]
[ Validate ] --> [ Valid? ]
[ Valid? ] -- yes --> [ Process ] --> [ Done ]
[ Valid? ] -- no --> [ Error ] --> [ Input ]' | graph-easy --as=boxart
```

### Microservice architecture

```bash
echo '[ Client ] -- HTTP --> [ API Gateway ]
[ API Gateway ] -- gRPC --> [ Auth Service ]
[ API Gateway ] -- gRPC --> [ User Service ]
[ API Gateway ] -- gRPC --> [ Order Service ]
[ Auth Service ] --> [ Redis ]
[ User Service ] --> [ PostgreSQL ]
[ Order Service ] --> [ PostgreSQL ]' | graph-easy --as=boxart
```

### Sequence diagrams — hand-draw these

`graph-easy` turns sequence flows into graph layouts, losing the lifeline format. Hand-draw instead:

```
 Browser          Server           Cache            DB
    |                |                |               |
    | GET /resource  |                |               |
    |--------------->| check cache    |               |
    |                |--------------->|               |
    |                | cache miss     |               |
    |                |<---------------|               |
    |                | query          |               |
    |                |------------------------------>|
    |                | data           |               |
    |                |<------------------------------|
    | 200 OK         |                |               |
    |<---------------|                |               |
```

## Rules

1. **Always pipe through `graph-easy`** for flowcharts and architecture diagrams. Do NOT hand-draw them.
2. **Always use `--as=boxart`** for Unicode box-drawing output.
3. **Use native syntax** for simple graphs (fewer than 8 nodes).
4. **Use DOT format** for complex graphs or when you need layout control (`rankdir`).
5. **Run the command via Bash tool** and show the output to the user.
6. **Keep node labels short** (2-3 words max) for clean layout.
7. **Add a brief text explanation** before or after the diagram for context.
