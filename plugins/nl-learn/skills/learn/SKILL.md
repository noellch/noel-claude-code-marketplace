---
name: learn
description: Use when user provides an article, PDF, URL, or transcript and wants to learn from it — triggers on "幫我學", "教我", "整理學習筆記", "learn this", "/learn", or when user pastes content with clear study intent
---

# Learn

Structured learning companion for articles, PDFs, and transcripts.

## Step 0: Always Ask Mode First (Hard Gate)

Before doing anything, send exactly this message and wait for the answer:

> 快速掃（10 分鐘，掌握重點）還是深度學（30 分鐘，真正理解）？

**One exception:** If the user's trigger message explicitly states the mode (e.g. "快速掃一下", "深度學這篇"), use that mode directly — no need to ask again.

Do NOT infer mode from content length or complexity. Always ask unless the user already told you.

---

## Quick Mode Output Template

**TL;DR** — 3 sentences max. What is this, and why does it matter?

**關鍵重點**
1. ...
2. ...
3. ...
（Max 5 points. Each one actionable or testable.）

**帶走一句話** — One sentence the user can repeat to explain this to someone else.

---

## Deep Mode Output Template

**概念地圖** — How do the main ideas relate? A short paragraph or ASCII tree.

**逐點解說** — For each key concept:
- What it is (plain language)
- One concrete example or code snippet
- One common mistake (❌ wrong → ✅ right)
  - Code topics: show ❌/✅ code pair
  - Non-code topics: show ❌ misconception → ✅ correct understanding

**自測題** — Exactly 3 questions the user should be able to answer after reading:
1. ...
2. ...
3. ...

**下一步** — 2-3 specific things to explore next (topics, docs, hands-on exercises).

**Content too short for deep mode** (e.g. a single tweet or one-liner):
> "這段內容太短，Deep Mode 會擴展到『[topic]』這個概念本身，而不只是解讀這句話 — 這樣 OK 嗎？"
Wait for confirmation before proceeding.

---

## Common Mistakes

| Mistake | Correct Approach |
|---------|-----------------|
| Skip mode question | Always ask first — quick vs deep determines the whole template |
| Use quick template for complex topics | Ask the user; don't infer from content length |
| Write self-test questions that are answered in the output | Questions should require the user to synthesize, not look up |
| Omit ❌/✅ pair in deep mode | Code topic → code pair; non-code topic → conceptual misconception pair |
| "下一步" lists generic advice | Point to specific resources, concepts, or exercises |
