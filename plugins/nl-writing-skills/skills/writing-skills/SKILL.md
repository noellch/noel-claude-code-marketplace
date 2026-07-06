---
name: writing-skills
description: Reference and process for writing or editing a Claude Code skill well — fuses a TDD validation loop with a design vocabulary for predictability. Type /nl-writing-skills when authoring, refactoring, or reviewing a skill.
disable-model-invocation: true
---

# Writing Skills

## Overview

A skill exists to **wrangle determinism out of a stochastic system**. Its root virtue is **predictability**: the agent takes the same *process* every run, not that it produces the same output (a brainstorming skill should predictably diverge).

This skill fuses two disciplines:

- **DESIGN for predictability** — the vocabulary and levers that make a skill predictable (invocation, information hierarchy, leading words, pruning). Full definitions live in [`GLOSSARY.md`](GLOSSARY.md); **bold terms** below are defined there.
- **VALIDATE with TDD** — you do not know a skill teaches the right thing until you watch an agent *fail* without it. Writing a skill IS test-driven development applied to process documentation.

## First: is a skill the right tool?

A skill guides *judgment*, and it is advisory — nothing forces the agent to read it at the right moment. If the rule is mechanically enforceable (a branch name, a file pattern, a required flag), build the mechanism instead — a hook, lint rule, or validation — and skip the skill. Example: "never commit to main" belongs in a `PreToolUse` hook that blocks the commit, not a skill the agent can forget to consult. Write a skill only for the judgment a mechanism cannot capture.

## Porting / replacing an existing skill

When the job is to **replace or port** an existing skill (re-implementing another
framework's skill as your own), the RED baseline flips — do not use a naive agent.

- **Reference = the source skill, not a naive agent.** The bar: an agent running
  *your* skill behaves at least as well as one running the *source* skill, on the
  same hard cases. Run the source-equipped agent as the reference and diff yours
  against it.
- **Parity is the floor; beating it is the goal.** Carry every capability the
  source carries — dropping any is a regression, *even if the current model does it
  by default*. Then add value (better integration, missing structure, model-agnostic
  phrasing) to exceed it.
- **The no-op test does not apply to parity content.** "The model already does
  this" is irrelevant when the source ships it: a weaker model, or the same model in
  a long/post-compaction session, still needs it. Keep it.
- *Done when:* a differential check shows your skill ≥ source on every rubric item,
  plus your additions.

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

Applies to **new skills AND edits**. Wrote the skill before the baseline test? Delete it, start over. **Violating the letter of this rule is violating its spirit** — no "just a small section", no "keep it as reference".

## Process (the spine)

Each step ends on a **completion criterion** — make it *checkable* (can you tell done from not-done?) and, where it matters, *exhaustive*. A vague criterion invites **premature completion**.

1. **RED — baseline test.** Dispatch a subagent through a realistic scenario for this skill's job, WITHOUT the skill. For discipline skills, stack 3+ pressures (time, sunk cost, authority). Record the exact choices and **rationalizations** verbatim.
   - **Don't tell the subject it's a test.** "This is a baseline, act naturally, be honest" primes the very behaviour you're measuring — the result is contaminated. Give it only the scenario and the pressures, never the thing you're grading.
   - **A clean single-turn dispatch is the easy case.** Discipline failures are long-horizon — they surface under context degradation, post-compaction, and real (not announced) stakes, which one fresh dispatch cannot reproduce. A baseline that stays green in one shot is *weak evidence*, not proof the skill is a no-op.
   - **Porting/replacing a skill? The reference is that skill, not a naive agent** — see *Porting / replacing an existing skill* below. A naive agent passing does NOT license dropping content the source carries.
   *Done when:* you have written down how the agent fails and every excuse it makes.
2. **DESIGN.** Decide the levers before writing prose (see Quick Reference below + `GLOSSARY.md`): pick **invocation**; place each piece on the **information hierarchy** (steps vs reference, what to **disclose**); hunt a **leading word**; write **completion criteria** that are checkable and exhaustive.
   *Done when:* every rationalization from RED maps to a lever that will counter it.
3. **GREEN — write minimal skill.** Write the smallest SKILL.md that addresses the RED failures — nothing for hypothetical cases. Frontmatter per the Description rules. Seed keywords the agent would search for (errors, symptoms, tools).
   *Done when:* rerunning the RED scenarios WITH the skill, the agent complies.
4. **REFACTOR — close loopholes + prune.** New rationalization surfaced? Add an explicit counter to the table. Then prune: run the **no-op** test per sentence, enforce **single source of truth**, disclose heavy **reference** behind a **context pointer**. Re-test until bulletproof.
   *Done when:* no new rationalization survives, and every remaining line changes behaviour.
5. **DEPLOY.** Run the checklist, commit to the marketplace, register in `marketplace.json`.

## Invocation choice

| | Model-invoked | User-invoked |
|---|---|---|
| Reached by | agent (auto) **and** human | human only, by typing its name |
| Reachable by other skills | yes | no |
| Cost paid | **context load** (description in window every turn) | **cognitive load** (you must remember it exists) |
| Mechanics | omit `disable-model-invocation`; rich trigger description | `disable-model-invocation: true`; human-facing one-liner |

Pick model-invocation **only** when the agent (or another skill) must reach it on its own. When user-invoked skills multiply past memory, cure the piled-up cognitive load with a **router skill**.

## Description rules (CSO — Claude Search Optimization)

For **model-invoked** skills the description is the trigger, so:
- **Describe WHEN to use, not WHAT it does.** A workflow summary in the description becomes a shortcut the agent follows *instead of reading the skill body*.
- Start with "Use when…", third person, one trigger per **branch** (collapse synonyms — that's **duplication**), keep under ~500 chars.

For **user-invoked** skills (this one), the description is human-facing: a one-line summary, trigger lists stripped.

## Design levers — quick reference

Full definitions in [`GLOSSARY.md`](GLOSSARY.md). Reach for these in step 2.

- **Predictability** — the root virtue; every lever serves it.
- **Information hierarchy** — rank content by how immediately it's needed: in-skill **steps** (primary) → in-skill **reference** → **disclosed reference** (a linked file behind a **context pointer**). Push down whatever you can; keep the top legible.
- **Progressive disclosure** — move reference out of SKILL.md so the top stays readable; licensed by **branching** (inline what every branch needs, disclose what only some reach). A pointer's *wording* decides how reliably it fires.
- **Co-location** — keep a concept's definition, rules, and caveats under one heading.
- **Leading word** — a compact concept already in the model's pretraining (*lesson*, *fog of war*, *tracer bullets*, *red/green*). Repeated as a token, it anchors a region of behaviour in the fewest tokens. Prefer a pretrained word over a coined one.
- **Completion criterion** — clarity resists premature completion; demand drives **legwork**. Strongest criteria are both checkable and exhaustive.
- **Pruning** — **single source of truth** (one authoritative place per meaning); **relevance** (does the line still bear on the job?); **no-op** test (does it change behaviour vs. the default? weak *be thorough* → stronger *relentless*). **Whose default matters:** the no-op test assumes one target model at full context. For a portable or replacement skill the bar is the *source's capability* and the *weakest target model* — content a frontier model does by default is not a no-op if a weaker model or a degraded session needs it.

## Failure modes (diagnostic)

| Symptom | Name | First fix |
|---|---|---|
| Agent ends a step before it's truly done | **premature completion** | Sharpen the completion criterion (cheap, local); only then hide post-completion steps by splitting |
| A line the model already obeys by default | **no-op** | Delete it, or replace a weak leading word with a stronger one — *unless* the skill is a port/replacement or targets weaker models (then keep; see Porting) |
| Same meaning in two places | **duplication** | Collapse to a single source of truth |
| Stale layers never cleared | **sediment** | Prune by relevance |
| Simply too long, though every line is live | **sprawl** | Disclose reference behind pointers; split by branch/sequence |
| Agent rationalizes past a rule under pressure | (discipline gap) | Add the excuse to the rationalization table + red flags |

## Rationalization table

Seed from RED; grow every time a new excuse appears in testing.

| Excuse | Reality |
|---|---|
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference, no need to test" | References have gaps. Test retrieval. |
| "I'll test if problems emerge" | Problems = agents can't use it. Test BEFORE deploying. |
| "I'm confident, testing is overkill" | Overconfidence guarantees issues. 15 min saves hours. |
| "I'm reasonably sure from experience" | Reasonably sure ≠ tested. Ship-on-confidence is the exact failure; run the baseline. |
| "Invocation? I already wrote a good description" | Invocation is a choice (context load vs cognitive load), not a byproduct of wording. Decide it in step 2. |
| "The naive agent already does it, so skip/drop the skill" | Only valid for net-new skills. For a port/replacement the reference is the *source* skill — a naive agent passing means you'd regress vs the thing you're replacing. |
| "The model does it by default, so the line is a no-op" | Whose default? Frontier model, fresh context. Weaker models and long/post-compaction sessions still need it. Not a no-op for a portable skill. |
| "I told the baseline it was a test and it behaved well" | You primed it — a contaminated baseline proves nothing. Re-run giving only the scenario, never what you're grading. |

## Red flags — STOP and restart the loop

- Wrote SKILL.md before running a baseline
- "I already know what it should say"
- Description summarizes the workflow, or says what the skill *does* / *covers* instead of only *when* to use it (the agent follows it and skips the body)
- The description got written but model-vs-user invocation was never explicitly decided
- Started writing before asking whether a hook/lint would enforce the rule better than a skill
- Editing an existing skill without a fresh failing test
- Tested a port/replacement skill against a naive agent instead of the skill it replaces
- Told the baseline subagent it was being tested (primed the result)
- Deleted parity content as a "no-op" because the current frontier model does it by default

## Deployment checklist

- [ ] RED baseline captured (behaviour + rationalizations verbatim)
- [ ] Invocation chosen; frontmatter matches (`disable-model-invocation` set iff user-invoked)
- [ ] `name`: letters/numbers/hyphens only; frontmatter ≤ 1024 chars
- [ ] Description follows the rules for its invocation type
- [ ] Heavy reference disclosed to a sibling file; pointer wording checked
- [ ] Every line passes the no-op test; single source of truth holds
- [ ] Re-tested WITH skill; no rationalization survives
- [ ] `plugin.json` created; entry added to `marketplace.json`; committed

---

*Synthesizes superpowers `writing-skills` (the TDD loop, CSO, rationalization discipline) and Matt Pocock's `writing-great-skills` (the predictability vocabulary). See `GLOSSARY.md` for the merged domain model.*
