# Ticket template

One filled template = one vertical-slice ticket. Fill the sections, then hand the
whole thing to `nl-asana-ticket` — it renders the **Asana `html_notes`** (plain
`notes` collapses all formatting) and publishes. Per-repo PRs attach to the ticket
later via the Asana GitHub widget (nl-asana-pr) — do NOT list them in the body.

## The rule the template enforces

The **title is a capability a user/PM could see demoed** — a verb + object
("Redirect a popup click to any URL"), never a layer ("Add link_type enum",
"Widget list endpoint"). If your filled title names a layer, the slice is wrong —
re-slice before publishing.

| ✗ layer title (reject) | ✓ capability title (ship) |
|---|---|
| "Add EXTERNAL_LINK to the model" | "Redirect a popup click to an arbitrary URL (tracked)" |
| "Widget list metrics endpoint" | "Show Awareness widgets in the list (impression-only, no report)" |
| "SDK render branch" | "Expose a no-click image popup (Awareness), end-to-end" |

## Fill-in skeleton (Markdown — author here, then convert)

```markdown
# <Capability title: verb + object, demoable>

**Goal (user-visible):** <what a marketer/PM sees after this ships — one sentence.>

**Scope (layers/repos this slice crosses):**
- <repo/layer>: <the ONE thing this slice needs there — not "all of X">
- <repo/layer>: <…>

**Acceptance (how you'd demo it):**
1. <concrete step a reviewer runs / clicks>
2. <observable end-to-end result — the demo>

**Out of scope:** <what this slice deliberately defers, to keep it thin>

**Dependencies:** <ticket ids that MUST land first — true deps only, else "none">
```

## Field rules

- **Goal** — outcome, not implementation. "A marketer's popup redirects to their
  campaign URL and the click is counted." Not "add a redirect endpoint."
- **Scope** — the slice's *portion* of each layer, never the whole layer. "Rubato:
  the one endpoint this click needs" not "Rubato: the redirect module."
- **Acceptance** — must be demoable end-to-end. If you can't write a demo step, the
  ticket is a layer, not a slice.
- **Dependencies** — only the walking-skeleton or a genuine data/contract prereq.
  Do NOT chain siblings that can run in parallel.
- **Per-repo PRs** — NOT a body section. They attach to the ticket via the Asana
  GitHub widget (nl-asana-pr) as they open; the ticket stays one capability.

## Asana `html_notes` rendering (what nl-asana-ticket publishes)

Asana rich text supports only: `<body> <h1> <h2> <ol> <ul> <li> <strong> <em> <u>
<s> <code> <a> <blockquote>`. No `<h3>`, no tables, no `<p>` — separate blocks with
`<h2>` + lists.

```html
<body><h1>Redirect a popup click to an arbitrary URL (tracked)</h1>
<h2>Goal</h2>
<ul><li>A marketer's image popup redirects to their campaign URL, and the click is counted so CTR shows in the report.</li></ul>
<h2>Scope</h2>
<ul>
<li><strong>Rubato</strong>: the redirect-click endpoint this capability needs (emit click + resolve target).</li>
<li><strong>Dolce</strong>: thin JWT proxy route to it.</li>
<li><strong>Vivace</strong>: on click, call it and open the target in a new tab.</li>
</ul>
<h2>Acceptance (demo)</h2>
<ol>
<li>Build an EXTERNAL_LINK popup pointing at a test URL; trigger it on a page.</li>
<li>Click the image → a new tab opens the URL.</li>
<li>The click appears in the widget report's CTR.</li>
</ol>
<h2>Out of scope</h2>
<ul><li>Configurable new-tab/same-tab target (fast-follow).</li></ul>
<h2>Dependencies</h2>
<ul><li>Walking-skeleton ticket (the new link_type + config).</li></ul>
</body>
```
