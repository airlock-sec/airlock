---
date: 2026-10-31 07:07 UTC
tasks: 7.17
summary: Close #79 (task 7.17); the GitHub annotation reporter's withheld and suppression notes name a command that this run can always satisfy, instead of a step summary or JSON file it may not have produced.
---

Close #79 (task 7.17). `github._withheld_note` told a reviewer that "the step summary and JSON
output list them all," and the suppression notice two paragraphs later made the same promise.
Neither is necessarily true of the run the reviewer is reading: `--format` selects one renderer
(`cli.py` `RENDERERS`), so a workflow that runs `airlock scan --format github` produces annotations
and nothing else, and `_write_step_summary` only writes a summary when `GITHUB_STEP_SUMMARY` is
set by a separate `--format summary` invocation. A reviewer who cannot find the promised document
could conclude the scan found what the annotation said it found, which is the B8 failure mode the
note exists to prevent.

The recommended fix from the issue needed no plumbing: both notes now end in the same
`github.FULL_LIST_HINT` sentence, telling the reader to rerun the scan with `--format json` and the same `--mode`, `--base` and
`--before`, which always lists everything, rather than a document whose existence depends on how this run was invoked. The
withheld count is unchanged, and `INFO_ANNOTATIONS` still reserves two of the ten `::notice` slots
for the withheld note and the suppression note.

`tests/unit/test_report.py::TestGithubAnnotations::test_the_withheld_note_names_the_command_that_lists_everything`
checks the new wording and that it no longer mentions a step summary.
`test_the_withheld_and_suppression_notes_share_the_same_sentence` checks both notes end in the
identical `FULL_LIST_HINT` text. `test_suppressions_are_announced_without_naming_a_finding` was
updated to the new exact-match text rather than the old one. All three failed against the
unmodified `src/airlock/report/github.py` (verified by stashing the source change and re-running
the suite) and pass after it.

The hint names the run's flags on purpose: a bare `airlock scan --format json` defaults to
`--mode full`, which trusts the working tree's `airlock.toml` instead of the trusted base, so it
could report a different set than a `--mode pr` or `--mode push` run did.
