---
date: 2026-10-31 08:00 UTC
tasks: 1.20, 1.3
summary: Close #100 (task 1.20) by naming fingerprint.py, model.py, roles.py, report/ and cli.py in CODEOWNERS, deciding tests/bypass/ belongs under the same review, and noting which half of 1.3 this settles.
---

Close #100 (task 1.20). `.github/CODEOWNERS` named the rules, the detectors, `policy.py`,
`collector.py`, `runner.py`, the workflows, `pyproject.toml` and itself, with a header comment
giving the rule: these paths carry the trust model, the detection logic and the gates, so a small
edit there can disable a check. Four modules carry the same property and were not listed:

- `src/airlock/fingerprint.py`: `truncate_evidence` runs before the evidence is hashed, so a
  fingerprint is a prefix comparison over its output; a one-constant edit there changes what
  every existing suppression matches.
- `src/airlock/model.py`: `STATE_RULE_IDS` is the set that makes a finding non-suppressible, and
  `Severity`, `Mode` and the `EXIT_*` constants are the exit-code contract the CLI maps to.
- `src/airlock/roles.py`: `SENSITIVE_ROLES` decides when an unreadable file is HIGH rather than
  WARN, and `resolve_roles` is the coverage claim every rule depends on.
- `src/airlock/report/` and `src/airlock/cli.py`: the reporters are the escaping boundary over
  attacker-controlled evidence, and the CLI is where `run_scan` decides which policy was trusted.

All five now have a line in `.github/CODEOWNERS`, each with its own one-sentence comment naming
the property it protects, in the voice the existing lines use. Each sits in its own group
directly after the existing `policy.py` / `collector.py` / `runner.py` block and shares no prefix
with an existing pattern, so none of the five existing lines lose their owner through the file's
own "later rules win" ordering; `tests/unit/test_codeowners.py` asserts this for both the five new
lines and every previously owned path.

The issue also asked for a decision on `tests/`, reasoned either way, because a bypass regression
is a security assertion in the same sense as a rule. Decided yes for `/tests/bypass/`: weakening
or deleting one of the seven Appendix B regressions (`tests/bypass/test_bypass_*.py`) would
silently reopen a confirmed bypass, which is the same failure mode owner review on `rules/` exists
to catch. Decided no for the rest of `tests/` (`unit/`, `fixtures/`, `corpus/`, `golden/`):
`AGENTS.md` 7 describes adding one positive and one negative fixture per rule as the routine way
to add a rule, and that PR already triggers owner review through the `rules/` line it touches;
requiring it again on every ordinary fixture or unit test would slow the common case without
covering a gap the `rules/` line leaves open.

Task 1.3 is amended rather than reopened, because its ruleset half is unchanged: approvals stay
at 0 for the one-member org (recorded there and in 1.7's Scorecard checklist), so this PR settles
only the file half, naming every module that carries the trust model, the exit-code contract, the
coverage claim or the escaping boundary. The enforcement half, a ruleset rule that requires code
owner review before a merge, needs a second maintainer and is unchanged by this PR.

`tests/unit/test_codeowners.py` parses `.github/CODEOWNERS` into `(pattern, owners)` pairs and
resolves a path's owner the same way GitHub does, the last matching line wins. Ten cases: the
five new paths resolve to `@Gabbydunkk`, twelve previously owned specific paths still resolve to
`@Gabbydunkk` after the new lines were added, a bare `/src/airlock/` line is absent (the issue
rules it out because `policy.py` and `detectors/` are already owned at finer granularity), a
bypass regression resolves to `@Gabbydunkk`, and an ordinary unit test and an ordinary fixture
resolve to no owner. Confirmed failing for the right reason against the pre-edit file by stashing
the `.github/CODEOWNERS` change: 6 of 10 cases failed with `None` where `@Gabbydunkk` was
expected (the five new paths and the bypass regression), and passing after restoring it.

Verified: `python3 -m pytest` 848 passed, 2 skipped (the same known load-sensitive ReDoS timing
case that passes in isolation); `ruff check .` and `ruff format --check .` clean; `mypy src`
clean; `python3 scripts/build_site.py --check` clean; `scripts/check_roadmap_touched.sh
origin/main` passes; `airlock scan --mode full .` reports 0 HIGH findings. Not verified: the
hosted `roadmap` and `checks` workflow runs, since this branch is not pushed.
