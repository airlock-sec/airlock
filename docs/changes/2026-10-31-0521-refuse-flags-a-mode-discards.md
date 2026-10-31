---
date: 2026-10-31 05:21 UTC
tasks: 2.16
summary: Refuse `--base`/`--before` in a mode that discards them (2.16): a flag the resolved trust model does not read is a usage error, the same rule `--event` follows, and the flag help names its mode.
---

A caller that passes a base to a full scan was telling the truth about a scan it did not run:
`run_scan` handed both values to `policy.resolve_policy`, and `full` mode returned the working-tree
policy before reading either. The contradiction argparse could see (`--event` against `--mode`) was
exit 2; the one hop further was silent.

`cli._MODE_FLAGS` now maps each `Mode` to the flags it reads (`pr` reads `--base`, `push` reads
`--before`, `full` reads neither) and `_refuse_ignored_flags` raises `UsageError` before `run_scan`
for any other combination, naming both the mode and the flag. This is the usage-error branch of the
issue's two options; the INFO-finding branch would have made a wrong command line produce a report
that looks like a normal scan, and the strictness argument in `AGENTS.md` 4 says a scan should never
quietly mean something other than what the caller asked for.

The `--base` and `--before` help text now says which mode reads each. Tests in
`tests/unit/test_cli.py` cover `--mode full --base` and `--mode pr --before` (both exit 2), the
existing `--event` contradiction still exits 2, and a plain full scan still reaches the scan.

Verified locally: `python -m pytest -q tests/unit/test_cli.py` → 55 passed, 1 skipped, 4 failed;
the four failures are `TestManifestCommands` and fail identically on the unmodified branch, on a
`tomllib` parse error in this Windows environment rather than on this change. `python -m ruff check .`
and `python -m ruff format --check .` are clean. `mypy` could not run in this environment (its
`pathspec` dependency is broken); CI runs it.
