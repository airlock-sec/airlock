---
slug: three-fail-closed-paths-have-no-end-to-end-test
title: An unknown policy key, a raising detector and an unreadable file are each correct in a unit test and unproven through the CLI
labels: type: test, complexity: medium, area: engine
roadmap: 2.1, 2.11, 2.2
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** All three behaviours ship and are unit-tested, and `cli.run_scan` is the single function a test can call to get from a policy file on disk to an exit code, so what is missing is one level of testing rather than a feature.

## Problem

Three paths decide whether a scan fails closed, and each is currently proven one layer below the thing a user runs:

- **An unrecognised key in `airlock.toml`.** `policy.py` produces a `policy-unknown-key` finding (the `_unknown_keys` walk, reported around lines 554-565) rather than ignoring the key, which is 2.1's whole point. The unit tests check the loader's output; nothing checks that a repository whose policy has a typo produces the exit code a caller would notice.
- **A detector that raises.** `runner._run_one` turns the exception into one HIGH `detector-error` and keeps the findings emitted before the failure (`src/airlock/runner.py:59-72`), and 2.11's acceptance wording is that a raising detector yields HIGH and exit 1. No test drives that through `run_scan` with a policy file, where the suppression pass has to leave a non-suppressible `detector-error` alone (2.15's ordering).
- **A file that cannot be read.** `collector._collect_one` returns a skip with `skipped-unreadable` at HIGH inside a sensitive role and WARN outside it. The unit coverage exists in `tests/unit/test_collector.py`; the end-to-end question, whether the runners report the file as scanned or as skipped and what `files_skipped` says in the JSON output, is unchecked.

Each of the three crosses a layer boundary (loader into scan, runner into suppression, collector into report), and the two ordering fixes this project has already had to make (2.14, 2.15) were both at a layer boundary.

## What to build

1. **Three CLI-level tests**, each building a real temporary repository (the helper 46 in this batch provides), driving `cli.run_scan`, and asserting the exit code, the finding's rule id and severity, and the reporter-visible field (`files_skipped` for the unreadable case).
2. **Inject the detector failure without editing the registry.** `detectors.DETECTORS` is a literal tuple by design and `DETECTOR_NAMES` is what the rule loader validates against, so a test should monkeypatch one registered function's body rather than construct a rule pointing at a nonexistent detector, which would be a loader test instead.
3. **Assert the suppression interaction.** For each of the three, run with a policy that carries a suppression entry that must not cover it, so the ordering properties from 2.15 are exercised on the way.
4. **Name the existing unit coverage in the record**, so the change reads as adding the missing layer rather than as the first test of the behaviour.

**Out of scope:** Changing any of the three behaviours, and the mode-selection refusals in `cli._mode_for`, which already has its own tests.

## Acceptance criteria

- [ ] A policy file with an unknown key produces the documented exit code and a named finding when driven through `run_scan`.
- [ ] A detector that raises produces one HIGH `detector-error`, keeps earlier findings, and cannot be suppressed.
- [ ] An unreadable tracked file in a sensitive role is a HIGH through the CLI and is counted in the JSON `files_skipped`.
- [ ] The three tests use real temporary repositories rather than a mocked collector.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`run_scan`, `main`)
- [`src/airlock/runner.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/runner.py) (`_run_one`, `_detector_error`)
- [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py) and `tests/unit/test_runner.py`

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
