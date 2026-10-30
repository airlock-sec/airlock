---
date: 2026-10-28 11:09 UTC
tasks: 2.14, 2.2, 8, 6.1
summary: The two collector gaps the audit recorded as 2.14 are closed. (a) An unmerged index path was dropped by `list_tracked_files`, which read only stage 0, so a file sitting in a merge conflict was scanned by nobody and reported by nothing.
---

The two collector gaps the audit recorded as 2.14 are closed. (a) An unmerged index path
was dropped by `list_tracked_files`, which read only stage 0, so a file sitting in a
merge conflict was scanned by nobody and reported by nothing. The listing now carries
the stage, folds a path's staged versions into one entry, and the collector returns it
before any read as `skipped-unmerged` (WARN, HIGH for `tooling-config` and
`editor-autorun`) with `SKIP_UNMERGED` counted in `files_skipped`. Adding it to
`STATE_RULE_IDS` is what makes it non-suppressible: `policy.py` refuses a suppression
aimed at a state id, which is the right rule for a finding whose whole content is
"nothing was looked at". (b) The same function was the module's second `subprocess.run`,
so a git timeout there escaped as `TimeoutExpired` rather than the `ValueError` the CLI
turns into exit 2. The call site is now `git_bytes`, one place that runs git and one
that converts `OSError` and `SubprocessError`; `git_text` is its text view, and the
listing needs bytes rather than stripped text to keep `-z` paths byte-exact through
`os.fsdecode`. Phase 2 is 14 of 14 and the readiness total moves to 28 of 89. Both
halves were tests first, run against a real conflicted repository built by two branches
editing the same lines, and the first run failed on the missing `SKIP_UNMERGED` name.
The old behavior is measured rather than remembered: `git ls-files -z --stage` over that
conflict prints records at stages 1, 2 and 3 with no stage 0, and `list_tracked_files`
continued past every non-zero stage, so the path reached no detector and no skip count.
`ARCHITECTURE.md` 6.1 and the section 8 table, and the `ARCHITECTURE_ESSENTIALS.md`
finding-id list, follow. That list had drifted in one more place: `policy-unknown-key`
shipped in 2.7 and was never added to it, so `test_model.py`'s documented set now names
it beside the new id. Verified: `pytest` 461 passed (6 new), `ruff check` and `ruff
format --check` clean on 43 files, `mypy src` clean on 24 files, self-scan exit 0 over
72 files with nothing skipped, plus one CLI run over a scratch repository left
mid-merge, which prints `skipped-unmerged` HIGH for `postcss.config.mjs` and WARN for
`app.py`, reports "2 file(s) scanned, 2 unmerged" and exits 1. Not verified: an
unresolved merge in a real workflow checkout, which is 4.1 territory because
`actions/checkout` for `pull_request` gives a merge commit rather than a conflicted
index, and the corpus gate, which is 0.10
