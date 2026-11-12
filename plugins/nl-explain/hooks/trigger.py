#!/usr/bin/env python3
"""UserPromptSubmit hook: when the user's message ends in a short comprehension
complaint, tell the model to invoke the explain skill.

In long sessions the model answered 「簡單說」 directly, without the skill, in 2 of 5
replays — and repeated the failure the skill exists to prevent. A description
cannot force invocation; this hook does. Silent on every other prompt.
"""
import json
import re
import sys

TRIGGER = re.compile(
    r"簡單[說説講]|看不懂|聽不懂|沒看懂|沒聽懂|白話|講人話|什麼意思|啥意思"
    r"|說到我(理解|懂)|太複雜|ELI5|explain (it |this |that )?(simply|simpler|in plain)",
    re.IGNORECASE,
)
MAX_LINE = 30  # longer lines are requests about something else ("幫我寫一段白話的說明文件給客戶…")


def main() -> int:
    try:
        prompt = json.load(sys.stdin).get("prompt", "")
    except (ValueError, AttributeError):
        return 0
    lines = [line.strip() for line in str(prompt).splitlines() if line.strip()]
    if not lines:
        return 0
    last = lines[-1]
    if len(last) > MAX_LINE or not TRIGGER.search(last):
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "The user is saying they did not understand the previous output. "
                    "REQUIRED: your first action is to invoke the `nl-explain:explain` skill with the Skill tool, "
                    "then follow it. Do not answer directly — direct answers to this kind of message are what "
                    "the user has rejected before, however clear they feel to you."
                ),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
