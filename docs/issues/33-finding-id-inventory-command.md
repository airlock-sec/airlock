---
slug: finding-id-inventory-command
title: Nothing in the repository can list the ids a scan is capable of reporting
labels: enhancement, complexity: medium, area: engine
roadmap: 5.2, 2.12
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `rules.load_rules` gives the rule half, `model.STATE_RULE_IDS` gives the other 18, and `scripts/build_site.py` already demonstrates deriving counts from data rather than from a hand list, so the inventory is a reader over three existing sources.

## Problem

A scan's report can carry ids from three places: the loaded rule files, `model.STATE_RULE_IDS` (`src/airlock/model.py:45-66`, 18 ids the collector and the policy loader emit through `_state`), and `runner.DETECTOR_ERROR_RULE_ID`. `README.md` keeps four hand-written tables totalling 24 rules, the site generates its own counts (`scripts/build_site.py:218-234`), and nothing prints the union.

Two failures follow. The first is drift: a state id that no document lists is invisible to a reviewer, and `docs/wave/settings.md:190` already miscounts the shipped rules, which is the same class of error. The second is the coverage question the project asks itself in 2.12: every *rule* must have a positive and a negative fixture, and the check reads the rule files, so a state id can ship with no fixture at all and nothing reports the gap. An inventory that names which ids have fixtures answers that in one command.

The action and the docs generator both need this list, and the open issue #29 covers the rule reference; this issue is the runtime-side inventory that a test and a generator can share.

## What to build

1. **Add `airlock rules list`.** One line per id the scanner can report, with kind (`pattern`, `builtin:<detector>`, `state`), severity, suppressibility and roles, and `--format json` for scripts. Sorted and deterministic, so the output is diffable.
2. **Mark the fixture state.** A column or field saying whether each id has a positive and a negative fixture, read from the same source `tests/unit/test_fixtures.py` uses so the two cannot disagree.
3. **Refuse the impossible combinations.** An id with no severity, a `builtin:` pointer with no registered detector (already cross-checked in `rules.load_rules`, and this is the place a human sees it), and a state id that is suppressible (2.15's ordering) should each be an error rather than a row.
4. **Make it the generator's source.** `scripts/build_site.py` and the `README.md` table builder should consume this inventory rather than reading rule files themselves, so there is one reader of the id set. Land the change in the site builder here only if the generated rule reference (#29) has not already moved that code, and say which in the record.
5. **Document the contract.** The command's output is what `docs/wave/settings.md` and the counts in `README.md` should be generated from, so state that where the counts live.

**Out of scope:** Rendering prose for humans (which is `explain`, 30 in this batch), the rule reference generator in the open issue #29, and any change to which ids exist.

## Acceptance criteria

- [ ] `airlock rules list` prints every rule id and every scanner-state id, with kind, severity, suppressibility and fixture coverage.
- [ ] A test asserts the printed set equals the union of the three sources, so an id added to `STATE_RULE_IDS` without a fixture is a failing test rather than a gap.
- [ ] `--format json` output is stable and diffable, with keys matching the JSON report's spelling.
- [ ] `scripts/build_site.py` either consumes the inventory or the record says why the generated rule reference owns that instead.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/rules.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) (`load_rules`) and [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`STATE_RULE_IDS`)
- [`tests/unit/test_fixtures.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_fixtures.py) (the fixture coverage source)
- [`scripts/build_site.py`](https://github.com/airlock-sec/airlock/blob/main/scripts/build_site.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
