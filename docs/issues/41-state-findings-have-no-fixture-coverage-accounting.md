---
slug: state-findings-have-no-fixture-coverage-accounting
title: The fixture gate counts rules, so the 18 scanner-state ids can ship with no positive or negative case
labels: enhancement, complexity: medium, area: engine
roadmap: 2.12, 3.10
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `model.STATE_RULE_IDS` is a literal tuple of the ids, `Rule.tests` already carries the builder names the loader cross-checks against `tests/fixtures/`, and the coverage test in `tests/unit/test_fixtures.py` is the place where the second half of the check would live.

## Problem

2.12's property is that every rule has a positive and a negative fixture, enforced by `RuleTests` (`src/airlock/model.py:201-210`), which the loader validates and `tests/unit/test_fixtures.py` checks against the builder names in `tests/fixtures/`. That covers rules.

The other findings a report can carry come from code: `model.STATE_RULE_IDS` (`src/airlock/model.py:45-66`) lists 18 ids emitted through `collector._state` and `policy._state`, including `skipped-unreadable`, `history-rewritten`, `submodule-unmapped` and `detector-error`. None of them appears in any rule file, so none of them is in the fixture gate's denominator. A state id whose only test is the unit test that happened to be written when it was added can be deleted, reworded or never reached again without any check noticing, which is the class of gap that 2.14 and 2.15 were each found by audit rather than by the suite.

## What to build

1. **Make the denominator complete.** A test that every id in `STATE_RULE_IDS` appears in at least one fixture-driven positive case and is absent from a named negative case, with the mapping recorded in data rather than in a comment, so adding a state id without a fixture fails.
2. **Account for ids that cannot have a negative.** Some state findings are the absence of a condition (a base that is not an ancestor). Say which ids are exempt and why, in one place the test reads, rather than leaving exemptions as an ad hoc skip.
3. **Keep it out of the rule loader.** A state id is not a rule; the check belongs beside the existing coverage test, not in `rules.load_rules`, which would otherwise have to invent rule data for something no rule file declares.
4. **Report the list.** The check should print which ids are uncovered when it fails, so the failure is a to-do list rather than a count.

**Out of scope:** Any change to what a state finding means, and the runtime inventory command that would also list these ids (33 in this batch).

## Acceptance criteria

- [ ] A test fails when an id in `STATE_RULE_IDS` has no positive fixture case.
- [ ] The exempt ids and the reason for each are recorded in a structure the test reads.
- [ ] The failure output names the uncovered ids.
- [ ] No state finding's behaviour changes while the coverage is being added.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`STATE_RULE_IDS`, `RuleTests`)
- [`tests/unit/test_fixtures.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_fixtures.py) and [`tests/fixtures/`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures)
- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`_state`) and `src/airlock/policy.py` (`_state`)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
