# Parity rubric: issue investigation reports

Score each item for each report: YES / PARTIAL / NO, with a short quote or line reference from the report as evidence. Judge what is in the report file, not what you would have done.

1. Root cause stated as one sentence naming the cause (not the symptom) with a file:line reference.
2. Evidence list: each entry is file:line or command output, with what it shows.
3. The report shows code was read before concluding (quotes or cites lines from app/reports.py and app/repo.py).
4. An explicit, single, testable hypothesis is written before the code verification (IF/THEN/BUT/THEREFORE or an equivalent explicit statement).
5. Regression check: git history consulted and the offending commit identified by hash or subject.
6. Similar tickets / prior occurrences considered, or explicitly noted as not checkable here.
7. Impact assessed on all four: scope (who/how many), severity (data loss / revenue / workaround), urgency (SLA / escalation), blast radius (what a fix could break).
8. Action items: each specific, with an owner and a why.
9. Decision needed: raises whether newest-first ordering is intended and where the fix belongs (report vs repo layer), or an equivalent bug-vs-intended question.
10. Measured facts and inferred conclusions are separated and labelled.
11. Ruled out: lists what was checked and excluded as the cause.
12. Confidence stated and tied to measured vs inferred.
13. Affected files listed with path:line for each change point.
14. Timeline reconciled: ticket says Oct 20 fine / Oct 27 wrong, only multi-order customers affected — the report connects these to the cause.
15. Reproduction: a script or test was actually run that shows the wrong first_order_date (command and output present).
