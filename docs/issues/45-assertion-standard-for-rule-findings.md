---
slug: assertion-standard-for-rule-findings
title: Several detector tests assert that something was found rather than that the right rule found it
labels: type: test, complexity: medium, area: tests
roadmap: 3.7, 2.12
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The three suites this touches are self-contained and green (`tests/unit/test_ci_surface.py`, `tests/unit/test_config_role.py`, `tests/unit/test_wasm_manifest.py`), and every finding already carries `rule_id`, `severity` and `line`, so tightening an assertion needs no production change.

## Problem

A rule's identity is its id, its severity and the line it names. A test that asserts `len(findings) > 0`, or that only checks an exit code, passes when a completely different rule fires, which is how a coverage claim can rot while its suite stays green. It is the test-side version of what issue #30 fixed on the data side: coverage stated in a place nothing checks.

The standard already exists in the better modules: `tests/unit/test_redos.py:214` names the rule id it expects (`[finding.rule_id ...] == ["cfg-long-line"]`) rather than a count, and `tests/bypass/test_bypass_6_cargo_runner.py` names both the path and the severity in its assertion. The middle of the suite is uneven, and `AGENTS.md` 4's positive-and-negative rule says what a negative must prove (the absence of that rule id, specifically) without any check enforcing the wording of the assertion.

## What to build

1. **State the standard in one paragraph** in `CONTRIBUTING.md` or `AGENTS.md`: a positive test asserts rule id, severity and line; a negative test asserts that the named rule id is absent from the findings, not that the list is empty.
2. **Sweep the existing suites** against it and fix the assertions that fall short. Report the count you changed, since a reviewer cannot otherwise tell a sweep from a rewrite.
3. **Make the weakest shape unwriteable.** A small test helper (`assert_finds(report, "cfg-network-exec", Severity.HIGH, line=4)` and `assert_absent(...)`) gives the standard a form that is shorter than the loose assertion it replaces, which is the only way a convention survives review.
4. **Check the negative fixtures specifically.** A negative fixture that asserts nothing about which rule stayed quiet is a test that the fixture builder ran, not that the rule distinguished the two cases.

**Out of scope:** Any change to a rule's severity or pattern to satisfy an assertion (that would be a weakening), and the fixture-coverage accounting, which 41 in this batch owns.

## Acceptance criteria

- [ ] The stated standard exists in a contributor-facing document.
- [ ] Every detector and rules test asserts rule id and severity for its positive cases, and names the rule id in its negative cases.
- [ ] A shared helper provides the assertions, and the sweep's changed count is recorded in the change record.
- [ ] No rule's severity, pattern or role changed to make a tightened test pass.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`tests/unit/test_ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_ci_surface.py), [`tests/unit/test_config_role.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_config_role.py) and [`tests/unit/test_wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_wasm_manifest.py)
- [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) (`:214`, the shape to follow)
- [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) (the fixture rule)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
