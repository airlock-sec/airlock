---
date: 2026-10-31 07:24 UTC
tasks: 7.13
summary: Close #78 (task 7.13), budget the step summary to SUMMARY_BYTE_BUDGET and degrade evidence before rows.
---

`report/summary.py` had no bound on the whole document, only on each finding's evidence
(`SUMMARY_EVIDENCE_CHARS`). A HIGH count large enough to pass GitHub's 1 MiB per-step ceiling
lost the summary silently: the runner aborts the upload, creates an error annotation, and
leaves the step and the job green, so a repository could choose to grow its HIGH count past the
point a reviewer's summary survives.

`render` now tracks the exact byte size of the document as it builds it and stops adding content
against `SUMMARY_BYTE_BUDGET`, 524,288 bytes. That is half of the documented 1 MiB step-summary
ceiling (`ARCHITECTURE.md` 6.6), and the margin is set from 0.9's probe rather than invented: a
1,048,577-byte summary was rejected outright, and a 1,048,000-byte summary, closer to the
ceiling but still under it, hung past a 10-minute timeout and had to be cancelled, which 6.6
calls the worse of the two failures. Halving the ceiling clears both observed failure points by
a wide margin instead of skimming just under one of them.

The degrade order is written down rather than left to whichever content happens to render last:
every HIGH's row (severity, rule, path and line) is kept first; evidence blocks are added from
whatever budget is left after every row is kept and are the first thing dropped when the budget
runs out; only a row count that alone exceeds the budget caps the list itself. Each loss is
named in a note rather than left silent, pointing at `airlock scan --format json` for the
complete list, following the same honesty pattern `github._withheld_note` already uses.
Evidence blocks are added whole or not at all, so a truncated document still closes every fence
it opens; nothing partial is ever appended mid-block.

`tests/unit/test_report.py::TestSummaryBudget` adds six tests: a 3,000-HIGH flood with evidence
renders within the budget, every row survives, earlier findings' evidence stays intact, the
note names the withheld-evidence count, and the fence count stays even; a 60,000-HIGH
evidence-free flood forces the row cap itself and the document still fits the budget with a
withheld-row count. Three fail against the pre-fix module (`AttributeError:
SUMMARY_BYTE_BUDGET` on the whole-document-fits assertion for each flood, and the
withheld-evidence note never appearing since the old render never drops anything): the
budget-fits test, the row-cap test and the withheld-evidence-note test. The other three pass
unchanged against the pre-fix module because the old render already kept every row and every
earlier finding's evidence and already closed every fence it opened; they stayed in the suite as
regression guards on those properties rather than as evidence the fix was needed. All six pass
after. `ARCHITECTURE.md` 6.6 records the budget and its margin in the reporter table row and the
narrative paragraph for `summary.py`.

Verified: `python3 -m pytest` (844 passed, 2 skipped), `ruff check .`, `ruff format --check .`
and `mypy src` clean, `airlock scan --mode full .` reports 0 HIGH (2 INFO, 241 files, nothing
skipped).
