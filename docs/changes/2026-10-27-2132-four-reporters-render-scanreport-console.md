---
date: 2026-10-27 21:32 UTC
tasks: 2.9, 2.1, B8, B11
summary: The four P0 reporters render a `ScanReport`: console, github annotations escaped against a second decode and delivered HIGH-first under the caps, JSON, and the step summary, with no color so the same bytes reach a pipe.
---

The four P0 reporters render a `ScanReport`. console: one line per finding plus a
summary line carrying severity counts, the suppressed count and the skip accounting,
with no color so the same bytes reach a pipe, a log and a TTY. github: `::error`,
`::warning` and `::notice`, `%` escaped before CR, LF, `:` and `,` so nothing survives a
second decode, and properties and bodies escaped by their own separate rules; findings
arrive HIGH-first so the survivors of a cap are the HIGHs, and every capped severity
ends with one annotation naming what went unlisted, which is what stops a WARN flood
from making a HIGH look absent and a capped HIGH list from looking complete. json: the
whole model with keys sorted, severities as labels, and every suppressed finding kept
with its reason, so one run diffs against the next. summary: counts, the skip table,
every HIGH enumerated while WARNs are counted and never listed, and evidence only ever
inside a fence computed as one longer than the longest backtick run anywhere in the
block, flattened and cut to 200 characters. Escaping outside the fence covers only the
characters that can form markup mid-line, after an first draft escaped `-` too and
turned every rule id into `cfg\-dynamic\-code`. Caps live as reporter constants rather
than policy settings, because GitHub's annotation and summary limits are still
unverified (0.9) and a repository must not be able to raise them. Verified: `pytest` 366
passed (49 new), `ruff check` and `ruff format --check` clean on 37 files, `mypy src`
clean on 24 files. Not verified: how many annotations GitHub actually renders, and any
of this reaching a real run before the CLI (2.10)
