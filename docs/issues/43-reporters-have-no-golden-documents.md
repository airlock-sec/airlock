---
slug: reporters-have-no-golden-documents
title: Every reporter is tested by parsing its own output in the test, and `tests/golden/` is empty
labels: enhancement, complexity: medium, area: engine
roadmap: 2.9, 7.6
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `tests/golden/` exists and is empty, `tests/fixtures/` already assembles findings and reports, and `tests/unit/test_report.py` already builds the fixed report shapes a golden file needs, so this is committing output that already exists rather than writing new machinery.

## Problem

The four shipped reporters are checked by string logic inside the test module: `tests/unit/test_report.py` carries `_outside` and `_fence_states`, a hand-written fence-state parser used to ask which lines of a rendered summary sit inside a fenced block (lines 30-45 of a 483-line file). It is a second implementation of the thing under test, so a bug in both places can agree, and a reviewer cannot see what the output looks like without running the code.

7.6 asks for golden tests for SARIF specifically, and the reason generalises: the reporters' job is to render untrusted text safely (B11), and the safest-looking artifact is the one nobody can eyeball. A golden document is also the only place a reader can see the whole contract at once, which is what issue 29 in this batch needs for the JSON output and what `README.md`'s screenshots would want.

## What to build

1. **Commit one document per reporter**, rendered from a single fixed report built by the existing fixture assemblers, named for the reporter and stored under `tests/golden/`.
2. **Include the adversarial cases in the golden set.** The fixed report should carry a path with markup characters, evidence containing a backtick run, a CRLF line, and enough findings of each severity to bite the annotation caps and the suppression note, so the escaping and the cap arithmetic are visible rather than asserted.
3. **Give the update path.** An `--update-goldens` flag or an documented environment variable, plus a test that fails when a golden is stale, so an intentional change is a reviewed diff rather than a deleted assertion.
4. **Keep the behavioural tests.** Golden files prove the shape; the existing assertions prove the properties. Deleting the fence-state parser would mean the properties are no longer checked, only the text.

**Out of scope:** The SARIF reporter's own implementation (26 in this batch) and any change to what a reporter prints.

## Acceptance criteria

- [ ] `tests/golden/` holds one committed document per shipped reporter.
- [ ] The fixtures behind them include attacker-shaped paths and evidence, plus a report that exceeds the annotation caps.
- [ ] A test fails when rendered output no longer matches its golden, and a documented command regenerates them.
- [ ] Every existing property assertion in `tests/unit/test_report.py` still runs.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`tests/unit/test_report.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_report.py)
- [`tests/fixtures/__init__.py`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures/__init__.py) (`assemble`, the report builder)
- [`src/airlock/report/`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
