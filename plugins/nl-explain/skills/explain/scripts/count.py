#!/usr/bin/env python3
"""Length gate for the explain skill.

Usage: count.py status|mechanism [file]     (reads stdin when no file is given)

Counts non-whitespace characters, because models cannot count CJK characters
reliably and `wc -m` counts bytes under the C locale. Exits 1 when the draft is
over the ceiling for its shape.
"""
import re
import sys

CEILINGS = {"status": 200, "mechanism": 800}

# Letter+digit tokens the reader already knows (Markdown headings, quarters).
# Internal codes such as review-principle numbers (P5) stay flagged on purpose.
EVERYDAY_CODES = {f"H{n}" for n in range(1, 7)} | {f"Q{n}" for n in range(1, 5)}

LEFTOVERS = [
    (
        r"(?<![A-Za-z0-9])[A-Z]\d{1,2}(?![A-Za-z0-9])|(?i:\btask\s*\d+)",
        "task code",
        EVERYDAY_CODES,
    ),
    (r"#\d{3,}", "PR / issue number", set()),
    # A short SHA mixes digits and a-f letters; requiring both skips plain
    # counts (1234567 rows) and all-letter words (defaced).
    (
        r"(?<![0-9A-Za-z])(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![0-9A-Za-z])",
        "commit SHA",
        set(),
    ),
    (r"[\w.-]+/[\w./-]+\.\w{1,4}\b", "file path", set()),
]


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in CEILINGS:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    shape = sys.argv[1]
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    count = len(re.sub(r"\s", "", text))
    ceiling = CEILINGS[shape]

    for pattern, label, everyday in LEFTOVERS:
        hits = sorted(set(re.findall(pattern, text)) - everyday)
        if hits:
            print(f"leftover {label}: {', '.join(hits[:8])} — drop unless the reader needs it to act")

    if count > ceiling:
        print(f"OVER: {count} chars, ceiling {ceiling} for {shape}. Cut {count - ceiling} and recount.")
        return 1
    print(f"OK: {count} chars, ceiling {ceiling} for {shape}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
