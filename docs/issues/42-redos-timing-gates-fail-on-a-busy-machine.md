---
slug: redos-timing-gates-fail-on-a-busy-machine
title: Three millisecond budgets in the ReDoS harness are measured on whatever the runner is doing
labels: bug, complexity: medium, area: engine
roadmap: 3.11, 2.12
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The harness already runs a canary that is asserted to breach its budget (`tests/unit/test_redos.py:12,201`), which is the property a robust measurement needs as its baseline, and the budgets are three constants at lines 47-49.

## Problem

`tests/unit/test_redos.py` holds `PER_LINE_BUDGET_MS = 60.0`, `ADVERSARIAL_SCAN_BUDGET_MS = 1_200.0` and `OVERSIZED_BUDGET_MS = 500.0` (lines 47-49) and asserts elapsed time against them (lines 196, 213, 227). Those are wall-clock measurements of a Python loop on a shared machine. Two of them fail reliably on a busy local run while passing on hosted CI, including on commits that touch no pattern at all, which is the record this project keeps: the hosted 3.11 run decides a timing gate.

A gate that fails for reasons unrelated to the change teaches contributors to re-run CI. The project's own rule is the opposite direction: never weaken a check to make it pass, which is why the fix has to be in how the measurement is taken rather than in the numbers.

## What to build

1. **Measure relative to the canary, with an absolute ceiling.** The harness already runs a catastrophically backtracking pattern in the same process; if a candidate pattern costs a small multiple of nothing and the canary costs the same multiple of its expected time, the ratio is stable across machines while the absolute milliseconds are not. Keep the absolute ceiling as the hard limit and add the ratio as the sensitive one, so a regression is caught earlier and a loaded runner is not.
2. **Or isolate the timing job.** A separate CI job, not parallelised against the rest of the suite, with the runner and interpreter recorded in the artifact. Say which of the two mechanisms you used; both are acceptable, a widened budget is not.
3. **Publish the numbers either way.** The measured per-pattern times are what 3.11 needs to decide whether to cut a cost, and today they exist only as a passed assertion. Emit them into the job log or an artifact so a reviewer can read the trend.
4. **Keep the canary's guarantee.** The assertion that the slow pattern breaches the budget is what proves the harness can detect a hole; any change to the measurement must leave it detecting.

**Out of scope:** Optimising any pattern (which is 3.11's own work once the numbers are trustworthy), and any change to what the harness feeds each pattern.

## Acceptance criteria

- [ ] The suite passes on a loaded local machine and on hosted CI, with no budget raised.
- [ ] A deliberately quadratic pattern added to the harness fails the check on both.
- [ ] The measured times per pattern are recorded somewhere a reviewer can read in the run.
- [ ] `AGENTS.md` or the test's own docstring states which runner decides a timing gate.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py)
- [`.github/workflows/ci.yml`](https://github.com/airlock-sec/airlock/blob/main/.github/workflows/ci.yml)
- [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) (3.11's measured costs)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
