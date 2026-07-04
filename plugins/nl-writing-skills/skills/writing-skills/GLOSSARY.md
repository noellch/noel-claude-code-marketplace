# Glossary — Writing Skills

The domain model for what makes a skill great, merged from two sources: Matt Pocock's `writing-great-skills` (the design vocabulary) and superpowers `writing-skills` (the TDD validation loop). This is the disclosed reference for [`SKILL.md`](SKILL.md).

A skill exists to wrangle determinism out of a stochastic system. The root virtue is **Predictability**; every design term is a lever on it, and every validation term is a way to prove the lever worked. **Bold terms** in any definition are themselves defined here.

Grouped by axis: **Predictability**, **Invocation**, **Information Hierarchy**, **Steering**, **Pruning**, and **Validation (TDD)**. Each *failure mode* lives beside the lever that cures it.

## Predictability

The degree to which a skill makes the agent behave the same *way* on every run — the same process, not the same output. The root virtue every other term serves; cost and maintainability are symptoms of it, not rivals.

*Avoid:* consistency, reliability, robustness, output-determinism

## Invocation

### Model-Invoked
A skill that keeps its **description**, so the agent can fire it autonomously — and the human can still type its name (model-invocation always *includes* user reach). Pays a permanent **context load** every turn for that discoverability. Reachable by other skills. Pick it only when the agent (or another skill) must reach the skill on its own.

*Avoid:* ability, tool, capability

### User-Invoked
A skill with its **description** stripped (`disable-model-invocation: true`) — invisible to the agent, reachable only by the human typing its name. Trades agent-discoverability for zero **context load**. Nothing but the human can reach it; no other skill can fire it.

*Avoid:* procedure, workflow, command

### Description
The skill's trigger and the one **context pointer** a **model-invoked** skill must keep loaded at all times. Its presence *is* the invocation axis: keep it → model-invoked; delete it → **user-invoked**. For model-invoked skills it states *when to use*, never the workflow — a workflow summary becomes a shortcut the agent follows instead of reading the body.

*Avoid:* frontmatter, summary

### Context Pointer
A reference held in context that names out-of-context material and encodes the condition for reaching it. The **description** is the top-level pointer; pointers to disclosed files are the same object one level down. Its *wording*, not its target, decides when and how reliably the agent reaches. A must-have behind a weak pointer is a variance bug — fix the wording first, inline only if that fails.

*Avoid:* link, reference, import

### Context Load
The cost a **model-invoked** skill imposes on the agent's context window — its description, always loaded, spending tokens and attention. The brake on splitting into more model-invoked skills.

*Avoid:* token cost, context bloat

### Cognitive Load
The cost a **user-invoked** skill imposes on the human — remembering which skills exist and when to reach for each (the human is the index). Not a cost to minimise blindly: it is the price of human agency. The brake on splitting into more user-invoked skills.

*Avoid:* human index, burden, overhead

### Router Skill
A **user-invoked** skill whose job is to name your other user-invoked skills and when to reach for each — one skill to remember instead of many. It can only hint, never fire them (they have no description). The cure for **cognitive load** when user-invoked skills multiply.

*Avoid:* dispatcher, menu, registry

### Granularity
How finely you divide skills. Each cut spends one of the two loads: more model-invoked skills spend **context load**; more user-invoked skills spend **cognitive load**. Split by **invocation** (a distinct **leading word** should trigger it, or another skill needs it) or by **sequence** (hide a step's **post-completion steps**). Split only when the cut earns it.

*Avoid:* chunking, modularity

## Information Hierarchy

A skill's content ranked by how immediately the agent needs it. Three rungs:

1. **Steps** — in-file, primary.
2. **Reference**, in-file — secondary.
3. **Reference**, disclosed — behind a **context pointer**.

Independent of invocation (a skill can be all steps, all reference, or both). Push down whatever you can; keep the top legible.

*Avoid:* structure, organization, layout

### Steps
The ordered actions the agent performs — when present, the primary tier. Not every skill has steps (a review is all **reference**). Every step ends on a **completion criterion**.

*Avoid:* workflow, instructions, choreography

### Reference
Material the agent refers to on demand — definitions, facts, parameters, examples. Secondary to **steps** when both exist; the entire content when there are none. The prime candidate for **progressive disclosure**.

*Avoid:* supporting material, docs, background

### Progressive Disclosure
Moving **reference** out of SKILL.md behind a **context pointer** so the top stays legible. Not primarily a token optimisation — it is how the **information hierarchy** is protected. Licensed by **branching**: disclose what only some branches need, inline what every path needs.

*Avoid:* lazy loading, chunking

### Co-location
Keeping the material an agent needs at once in one place — a concept's definition, rules, and caveats under one heading, not scattered. The within-file companion to the hierarchy: the hierarchy ranks *how far down* a piece sits, co-location decides *what sits beside it*. A skill should read like documentation written for the agent.

*Avoid:* grouping, clustering, cohesion

### Sprawl
*Failure mode.* A skill simply too long, even when every line is live and unique. Costs readability, maintainability, and tokens. Cure: the hierarchy — disclose reference behind pointers, split by **branch** or sequence. Distinct from **sediment** (stale length) and **duplication** (repeated length).

*Avoid:* bloat, length, verbosity

## Steering

### Branch
A distinct way a skill can be invoked — a case it handles — so different runs take different paths. A skill with many steps may carry many branches; a linear one has none.

*Avoid:* path, case, fork

### Leading Word
A compact concept (a *Leitwort*) already living in the model's pretraining that the agent thinks with while running the skill (*lesson*, *fog of war*, *tracer bullets*, *red/green*). Repeated as a token, never as a sentence, it accumulates a distributed definition and anchors a region of behaviour in the fewest tokens. Serves **predictability** twice: in the body it anchors *execution*; in the **description** it anchors *invocation* (when the same word lives in your prompts, docs, and code). A coined word recruits no priors — reach for a pretrained one first.

*Avoid:* keyword, term, motif

### Completion Criterion
The condition that tells the agent a unit of work is done. Two properties make it a lever: *clarity* (can the agent tell done from not-done?) resists **premature completion**; *demand* (how much it requires) sets **legwork**. The strongest criteria are both checkable and exhaustive ("every modified model accounted for", not "produce a change list").

*Avoid:* done condition, exit condition, stopping rule

### Legwork
The work an agent does behind the scenes within a single step — reading files, exploring, digging up what it needs rather than offloading to the user. Latent in the wording, not written as its own step. Raised by a **leading word** (*comprehensive*, *relentless*) or a demanding **completion criterion**; goes thin when demand is missing or **premature completion** cuts the step short.

*Avoid:* scope, effort, diligence, coverage

### Post-Completion Steps
The **steps** that follow the current one. Visible, they pull the agent forward into **premature completion**; the defence is to hide them by splitting the sequence.

*Avoid:* horizon, lookahead

### Premature Completion
*Failure mode.* Ending the current step before it is genuinely done, because attention slips to *being done*. A between-steps failure. Defence in order: **sharpen the completion criterion first** (local, cheap); only if it is irreducibly fuzzy *and* you observe the rush, **hide the later steps** by splitting — and hiding only works across a real context boundary (a user-invoked hand-off or subagent dispatch).

*Avoid:* premature closure, the rush, shortcutting

## Pruning

### Single Source of Truth
Each meaning lives in exactly one authoritative place, so changing behaviour is a one-place edit. **Duplication** is its violation.

*Avoid:* home, canonical location

### Duplication
*Failure mode.* The same meaning in more than one place. Costs maintenance and tokens, and inflates a meaning's prominence past its real rank. The accidental inverse of a **leading word** (which repeats a *token* on purpose, never the meaning).

*Avoid:* repetition, redundancy

### Relevance
Whether a line still bears on what the skill does. A line loses it by never bearing on the task, or by going stale. Shorter skills are easier to keep relevant. Distinct from **no-op**: relevance asks whether a line bears on the task, not whether it changes behaviour.

*Avoid:* load-bearing, staleness

### Sediment
*Failure mode.* Stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.

*Avoid:* accretion, cruft, rot

### No-Op
*Failure mode.* An instruction that changes nothing because the model already does it by default — you pay load to say nothing. The test: does the line change behaviour versus the default? A line can be **relevant** and still a no-op. A **leading word** too weak to beat the default (*be thorough*) is a no-op; the fix is a stronger word (*relentless*), not a different technique.

*Avoid:* redundant instruction, restating the obvious

## Validation (TDD)

The loop that proves a design lever actually worked — from superpowers `writing-skills`.

### Iron Law
No skill without a failing test first — new skills and edits alike. If you did not watch an agent fail without the skill, you do not know it teaches the right thing. Violating the letter is violating the spirit.

*Avoid:* guideline, best practice

### Baseline Test (RED)
Running a realistic scenario through a subagent WITHOUT the skill, to observe how it naturally fails and to capture its **rationalizations** verbatim. The "watch the test fail" of skill-writing. For discipline skills, stack 3+ pressures (time, sunk cost, authority, exhaustion).

*Avoid:* smoke test, sanity check

### RED-GREEN-REFACTOR
The cycle: RED (baseline failure documented) → GREEN (minimal skill that addresses those specific failures, agent now complies) → REFACTOR (close new loopholes, prune, re-test until bulletproof). Add no content for hypothetical cases in GREEN.

*Avoid:* iterate, cycle

### Rationalization Table
A running table of every excuse an agent makes to skip or bend a rule, each paired with its rebuttal. Seeded from **baseline test** observations and grown at every REFACTOR pass. Paired with a **red flags** list for fast self-check.

*Avoid:* FAQ, objections list

### CSO (Claude Search Optimization)
Making a **model-invoked** skill discoverable: a **description** that states *when to use* (not the workflow), keyword coverage (errors, symptoms, tools), and verb-first naming. Irrelevant to **user-invoked** skills, whose description is human-facing.

*Avoid:* SEO, discoverability tuning

---

*Sources: Matt Pocock, `mattpocock/skills` → `productivity/writing-great-skills`; superpowers marketplace → `writing-skills`.*
