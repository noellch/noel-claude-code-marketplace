---
name: handoff
description: Compact the current session into a durable, structured handoff doc a fresh agent can resume from. Type /nl-handoff when ending a session mid-task or passing work to another agent.
disable-model-invocation: true
---

# Handoff

## Overview

Turn a session into a **resumable artifact** a fresh agent can pick up cold — not a chat summary. A good handoff is structured, **saved to a durable place**, has **secrets redacted**, and points at a **concrete entry point**. Those four are where handoffs usually fail; hold them.

## Steps

1. **Resolve the concrete entry point.** Grep for the exact file (and line/function) the next agent should open first. Finding it is your job now, while you hold the context — don't hand off "go search for the endpoint".
   *Done when:* the doc names an exact `file:location` to start from, verified to exist.
2. **Write the handoff** with these sections: **Goal · Current state** (done / in-progress / not-started) **· Next steps** (ordered) **· Key decisions + WHY · Open questions** (blocking, with their consequences) **· Gotchas/env · Suggested skills/tools · Entry point**.
   *Done when:* a fresh agent could continue without asking you anything.
3. **Redact secrets — MANDATORY.** Never copy a credential, token, or password verbatim. Name it, say where it lives (env var / file), flag it sensitive, and recommend rotation if it was exposed. Scan the whole doc before saving.
   *Done when:* no secret value appears anywhere in the doc; each is referenced by name + location only.
4. **Save to a durable, discoverable location.** Write the doc into the repo's plan tree (e.g. `docs/plans/<topic>/YYYY-MM-DD-handoff.md`), not scratch or temp, so the next session loads it as context. Then give the path.
   *Done when:* the file is written where the next agent will find it, and you've stated that path.

## Red flags — STOP

- Emitted the handoff as chat only — no saved file, no path given
- Copied a secret value verbatim instead of referencing it by name + location
- Entry point is "search for it" instead of an exact file
- It's a loose summary — missing ordered next-steps, or decisions with no WHY

## Rationalization table

| Excuse | Reality |
|---|---|
| "I'll just paste the summary in chat" | Chat evaporates; the next session starts cold. Save it to a file and give the path. |
| "The password is needed to run it, I'll include it" | Never. Name it + its location; the next agent reads it from env. Recommend rotation if it was exposed. |
| "They can find the entry file themselves" | Finding it is your job now, while you hold the context. Grep it, name the exact location. |
| "A quick summary is enough" | A summary is not a handoff. No ordered next-steps or decision rationale = the next agent re-derives everything. |
