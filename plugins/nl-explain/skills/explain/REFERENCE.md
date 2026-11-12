# Evidence behind `explain`

For maintainers. The agent running the skill does not need this file.

## Field data (2026-11-12)

371 Claude Code transcripts were scanned for user replies such as 看不懂, 簡單說, 白話 and 什麼意思. That gave 69 genuine comprehension complaints. One complaint can carry more than one tag.

| Failure | Count |
|---|---|
| Undefined term or internal code | 57 |
| Too long or dense | 42 |
| No positioning: what the whole thing is, what it was before | 22 |
| Conclusion or next step buried | 16 |
| No example, timeline or analogy | 15 |
| Measured and inferred mixed | 7 |
| Over-compressed, mechanism dropped | 6 |

Fixes that failed:
- Shortening while keeping the terms.
- Lengthening to explain more.
- Defining only the term the user named, while the definition used other undefined words.

Fixes the user accepted:
- One mental model first.
- A step-by-step timeline.
- A frontend analogy.
- A conclusion sentence plus an explicit "not verified" label.

## RED baseline

Setup: fresh Opus, with memory loaded but without this skill, on 3 real cases. It passed 2 of 3. On the Django drift case it kept the task codes, and it said "model and migration don't match" without first saying what those two are. The user had rejected exactly that version.

## GREEN iterations (blind-graded against the accepted rewrites)

- v1 (fixed 6-section template): fixed codes and mental model, but every reply came out 1.2–5x the accepted length with the same facts said three times. One reply drifted into Simplified Chinese.
- v2: shape by message type, certainty tagged inline, no opener/apology, script rule. Replies got shorter.
- v3: the budgets were set from `wc -m`, which counts bytes under the C locale (3x CJK), so they were about 2x too generous. Models treat a budget as a target, and replies grew. Fix: real character counts, "ceiling, not a target", plus an accepted exemplar.
- v4/v5: held-out PR-review case showed the status shape skipping positioning for an unfamiliar subject. Fix: position first unless the reader owns the thing.
- Final blind grade: the skill version beat baseline on all 5 paired cases (17–13, 17–12, 17–14, 16–16 tie-break, 16–15), and the held-out case scored 16/18. Remaining weaknesses: still 1.6–3.8x the accepted length, and added reassurance or upgraded confidence. The confidence-fidelity rule was added for the second one.

## Length gate and trigger hook (added after the first blind grade)

- **Length gate** (`scripts/count.py`). Prose budgets did not hold: models cannot count CJK characters. With the gate, 4 of 4 retests landed inside the ceiling (463 / 147 / 565 / 407 characters, against accepted versions of 488 / 137 / 604).
- **Long-conversation replays.** Resuming a truncated copy of a real session was refused by the permission classifier as transcript tampering. The substitute: render the real conversation up to the complaint (180k–300k characters, read-only) into one prompt and run it headless in a scratch directory with the plugin loaded. The agent reads the history rather than having lived it, so this is weaker than a true resume.
- **Finding: invocation, not content, fails in long context.** Without the hook the skill was invoked in 3 of 5 replays. In the other 2 the model answered 「簡單說」 directly and repeated the old failure (task codes kept, header-heavy). When the skill ran, output matched the accepted versions closely (stacked-PR status: 166 characters).
- **Trigger hook** (`hooks/trigger.py`, UserPromptSubmit). Fires only when the last line of the prompt is ≤ 30 characters and contains a complaint phrase. Verified in headless runs with `--debug hooks`: the hook's additionalContext was delivered. A hook can only advise. With the first, polite wording the model invoked the skill in 3 of 4 long replays and answered directly once. The wording was then made a hard requirement ("REQUIRED: your first action…"), and the one rerun after that invoked the skill. Counts are small.
- **Long-replay blind grade** (against what the user accepted and rejected in the same conversations). Skill versions: 15, 15, 17, 17 out of 18, each judged "would be accepted". The no-skill Django reply scored 13, "borderline, closer to the rejected one". The skill lost one case, 12 to 14: a 230-character PR-review rewrite cut the state line the user acted on next ("nobody has picked up the backend part") and skipped positioning, where the accepted version ran 780 characters. Fixes: mechanism ceiling raised to 800, "never cut a state line the reader acts on", "add nothing the original doesn't support", and a positioning question in the teach-back. The rerun kept the state line and the positioning. That last round was checked by reading the output, not blind-graded.

## Sources

- **Miller 2019**, *Explanation in Artificial Intelligence: Insights from the Social Sciences*, https://arxiv.org/abs/1706.07269. Good explanations are contrastive ("why P rather than Q"), give a selected 1–2 causes, put causes before probabilities, and follow the Grice Quality maxim (do not assert without evidence).
- **Sweller et al. 2019**, cognitive load theory. Difficulty is relative to the reader's prior knowledge (element interactivity). Undefined terms add extraneous load.
- **ISO 24495-1:2023**, plain language. Relevant, findable, understandable, usable, and builds on what the reader already knows. Only the sample text was read.
- **Gentner structure mapping**, Gentner & Smith 2012. An analogy helps when it maps relations, not surface features, and it must state where it breaks.
- **BLUF / Minto pyramid**: answer first, no background preamble. Second-hand summaries only.
- **AHRQ teach-back**: understanding is checked by having the reader restate the content. Search snippets only.
- **Anthropic** multi-agent research post and prompting guidance: a report must stand alone for a reader who lacks the writer's context.

The full research notes and the per-case transcript excerpts live outside this repo, in Noel's `co/docs/plans/explain-skill/`.
