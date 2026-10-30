---
date: 2026-10-28 10:51 UTC
tasks: 2.9, 2.10, 2.12, 2.13, 0.4, 3.5, 1.8, 1.10, 1.11, 2.14, 5.7
summary: The six tasks that merged into each other's branches instead of into the default branch land as one pull request: 0.4 bypass probe, 2.9 reporters, 2.10 CLI, 2.12 fixture and ReDoS harness, 2.13 model settle, 3.5 `manifest add`.
---

The six tasks that merged into each other's branches instead of into the default branch
land as one pull request: 0.4 bypass probe, 2.9 reporters, 2.10 CLI, 2.12 fixture and
ReDoS harness, 2.13 model settle, 3.5 `manifest add`. Verified on the branch being
merged: `pytest` 455 passed, `ruff check` clean, `ruff format --check` clean on 43
files, `mypy src` clean over 24 files, and a real end-to-end run, `python3 -m airlock
scan --mode full .`, reports 0 HIGH, 0 WARN and 2 INFO over 70 files scanned with
nothing skipped and exits 0. Corrections to this file rather than new claims: section 2
still called suppression, the reporters and the CLI stubs after their rows were ticked,
section 4 still named 2.2 and 0.4 as the next work, and 1.8, 1.10 and 1.11 stayed
unticked although the files they describe merged in PR #1 on 2026-10-27 (c4cffef and
8dc19bf). The two minimal issue templates 1.8 asked for are added. Two gaps found while
verifying this, recorded as tasks rather than prose: 2.14, an unmerged index path is
dropped with no finding and a git timeout leaves `list_tracked_files` as
`TimeoutExpired` instead of exit 2; 5.7, the built wheel carries no rule data, so an
installed `airlock scan` exits 2 on a missing `rules/roles.toml`. Not verified: any of
it running in CI, because 1.5 does not exist yet and every number above was produced on
the owner's machine
