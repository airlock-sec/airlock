---
date: 2026-10-27 21:04 UTC
tasks: 2.7, 2.1, 2.6, 7.3
summary: `policy.py` resolves the trusted base and loads the two protected files. `pr` mode takes the PR base SHA and exits 2 when it is missing, malformed or unreachable, because the alternative is judging a change by the policy the change wrote.
---

`policy.py` resolves the trusted base and loads the two protected files. `pr` mode takes
the PR base SHA and exits 2 when it is missing, malformed or unreachable, because the
alternative is judging a change by the policy the change wrote. `push` mode takes
`github.event.before`: all-zeros is a new branch, and anything that is not an ancestor
of HEAD is a rewrite; both scan against `BOOTSTRAP_POLICY` and an empty manifest, which
carry no suppressions. `full` mode reads the working tree and says so with
`untrusted-policy-source` (INFO). Both files are compared with their HEAD copies, so a
policy edit inside the change yields `policy-changed` (WARN) with a line-count summary
and no diff text, and the base copy is what the scan runs. Unknown keys in either file
come back as `policy-unknown-key` (WARN) naming the dotted key, because a misspelled
setting otherwise vanishes into its default; a missing or unsupported `version`, bad
TOML and a malformed suppression stay exit 2. Suppression application is 2.8, so
`Policy.suppressions` is parsed and not yet used. Two defects found by writing this: the
dogfood `airlock.toml` did not parse at all (an inline table across two lines is not
valid TOML, and `ARCHITECTURE.md` 7.6 showed the same shape, so both are corrected), and
a scanner-state finding with no evidence raised inside `number_occurrences`, which would
have crashed the first scan of any repository containing a submodule, a symlink or an
oversized file; state findings now key on their message, which is scanner-written and
non-suppressible. 7.3 records that rule. Verified: `pytest` 284 passed (55 new, all four
named trusted-base cases against real temporary git repositories), `ruff check` and
`ruff format --check` clean on 35 files, `mypy src` clean on 24 files. Not verified: an
end-to-end scan, and the `pr` base SHA as GitHub actually supplies it, which needs the
Action (4.1)
