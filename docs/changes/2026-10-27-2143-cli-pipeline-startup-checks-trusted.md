---
date: 2026-10-27 21:43 UTC
tasks: 2.10, 2.7, 2.8, 2.9, B1
summary: `cli.py` is the pipeline: startup checks, trusted base, rule data, collection, engine pass and detectors, one numbering pass, suppression, reporters.
---

`cli.py` is the pipeline: startup checks, trusted base, rule data, collection, engine
pass and detectors, one numbering pass, suppression, reporters. `airlock scan` runs, and
the repository scanning itself clean (64 files, nothing skipped, two INFO
`untrusted-policy-source` for reading policy out of the working tree in `full` mode,
exit 0) is the first end-to-end proof of the design. Exit codes are as documented: 0 for
nothing at or above `fail_on`, 1 for something, 2 for configuration and usage, 3 for
internal error, and an unborn repository or an absent directory is 2 rather than a quiet
0. `--event` maps `pull_request`, `push`, `workflow_dispatch` and `schedule` onto a
trust model; an unmapped event, or an event contradicting `--mode`, is a usage error,
because choosing a trust model silently is the bypass B1 is about. All three trust
models are now exercised through the CLI and not only against `resolve_policy`: a pull
request whose change weakens the policy, suppresses a HIGH rule and adds the payload
still exits 1 and still names the payload; a force push yields `history-rewritten`; a
new branch yields `no-trusted-base` and inherits nothing. Suppression is reachable for
real, which is the sequence 2.8 was written for: a `full` scan prints the fingerprint in
JSON, the entry written from that digest silences exactly that finding, the JSON still
lists it under `suppressed` with its reason, and an entry aimed at `cfg-dynamic-code`
(which the shipped rule data marks non-suppressible) returns `suppression-invalid` with
the payload still reported. The step summary goes to `$GITHUB_STEP_SUMMARY` alongside
whatever `--format` chose, because annotations are for the commit author and the summary
is for the reviewer who has to see every HIGH. README status and quickstart, PRD 6.3 and
the runner note are corrected to match shipped behavior. Verified: `pytest` 395 passed
(29 new CLI tests), `ruff check` and `ruff format --check` clean on 37 files, `mypy src`
clean on 24 files, plus a manual self-scan in each of the four formats. Not verified:
`pr` mode with a base SHA as GitHub supplies it, and any of this inside a workflow,
which is 4.1
