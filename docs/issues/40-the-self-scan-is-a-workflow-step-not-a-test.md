---
slug: the-self-scan-is-a-workflow-step-not-a-test
title: The repository scans itself in CI, and no test knows whether that step still runs or still passes
labels: enhancement, complexity: medium, area: tests
roadmap: 3.10, G5
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** CI already installs the package and runs `airlock scan --mode full .` as the last step of the job (`.github/workflows/ci.yml:52-53`), and `tests/unit/test_cli.py` already drives real temporary repositories through the CLI, so the missing piece is one test that points the same code at this repository.

## Problem

G5 asks that `airlock` scan itself with zero HIGH findings, and the workflow does that today. The guarantee lives in one `run:` line: nothing in the suite asserts it, so a commit that adds a finding does not fail a test, it fails a step, and a step that is renamed, reordered or given `continue-on-error` fails nothing at all. 0.4 recorded exactly that shape in the reverse direction: the old scan's step had no `continue-on-error` and every bypass case exited 0, so the job went green on the weakest possible signal.

3.10 is the row that asks for this: a self-scan test with no `SELF` skip. The distinction matters, because the collector has no directory exception list to hide behind (`AGENTS.md` 4: no default skips) and this repository carries rule data that quotes payload shapes. A test that runs the pipeline over `.` and asserts the HIGH count is zero is therefore also the test that proves the rule files do not match themselves, which `rules/builtin/builtin_patterns.toml:33-50` claims by construction and nothing verifies.

## What to build

1. **Add the test.** Run the scan over this repository through the same entry point CI uses, in a test marked so a developer can see it, and assert zero HIGH findings plus `files_skipped` empty of anything the collector would only produce on itself.
2. **Assert counts, not a hash of the report.** Pinning the exact finding list makes the test a third copy of the rule data; asserting HIGH count zero and naming any unexpected finding in the failure message keeps it useful.
3. **Keep the installed-path distinction honest.** `ci.yml:49-51` explains why the step runs the console script rather than `python -m airlock`: the module form would not catch a wheel missing its rule data. Say which form the test uses and why, and if it uses the source tree, keep the CI step as the wheel check rather than replacing it.
4. **Fix what it finds.** If the self-scan is not currently clean, the finding is the point of the issue; record it rather than suppressing it, since 2.15 and `AGENTS.md` 4 make silent suppression of a state finding impossible anyway.

**Out of scope:** Any change to the rule data or the collector to make the test pass without a finding being real, and the corpus gate (4.6), which is a different repository set.

## Acceptance criteria

- [ ] A test runs the full pipeline over this repository and asserts zero HIGH findings.
- [ ] Renaming or removing the CI self-scan step does not make the suite lose coverage silently, and the relationship between the two is stated in `AGENTS.md` 5.
- [ ] The test names every unexpected finding in its failure output rather than only a count.
- [ ] `AGENTS.md` 5, `SUPPORT.md` and `ci.yml` agree on one command form for the self-scan.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`.github/workflows/ci.yml`](https://github.com/airlock-sec/airlock/blob/main/.github/workflows/ci.yml) (the step and the comment above it)
- [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py)
- [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) (3.10, G5)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
