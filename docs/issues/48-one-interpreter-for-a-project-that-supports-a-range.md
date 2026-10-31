---
slug: one-interpreter-for-a-project-that-supports-a-range
title: `requires-python` says 3.11 and later, and CI proves 3.11 only
labels: type: test, complexity: medium, area: engine
roadmap: 2.3, G1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The workflow already pins `python-version: "3.11"` with a full-SHA action pin (`.github/workflows/ci.yml:29-31`), so adding a matrix is an edit to that one key plus the checks that must not run twice.

## Problem

`pyproject.toml` declares Python 3.11 as the floor and the code uses language features from that range (`datetime.UTC`, `slots=True` dataclasses, PEP 604 unions in annotations). `check_runtime` refuses to run below the floor (2.3), which is a promise about 3.12 and 3.13 behaviour that no test keeps: CI installs 3.11 (`ci.yml:31`) and nothing else.

The concrete drift risk is not syntax, it is the standard library the scanner depends on for its fail-closed behaviour: `tomllib` (the policy and rule loader is written against it, `policy._document`), `hashlib.sha256`, `zipfile` and `tarfile` if archive reading lands, and `unicodedata` if the invisible-character class grows. A change in any of them across a minor version shows up as a scan that reports something different on a newer runner than the CI that gated the pull request, which is the failure mode a supply-chain scanner cannot afford to be wrong about.

## What to build

1. **Add the matrix** over every version `requires-python` admits, keeping the full-SHA action pins and the pinned tool installs from `ci.yml:33-37`.
2. **Run the timing gate on one interpreter only**, and say which, because 43 in this batch is about measurement noise and a matrix multiplies it. Record the choice in the test's docstring so the reason survives.
3. **Decide what a single-version failure means.** Either every version is required for a merge, or the range is wrong in `pyproject.toml`. Both are honest answers; a matrix whose jobs are not required checks is neither.
4. **Cover the loader on each version explicitly.** The TOML parsing path is the one where a standard-library behaviour change would silently alter what a policy file means, so it should be named in the matrix result rather than assumed.

**Out of scope:** Raising or lowering `requires-python`, and any performance claim per interpreter, which 39 in this batch owns.

## Acceptance criteria

- [ ] CI runs the suite on every Python version `requires-python` allows.
- [ ] The matrix job's checks are required for merge, or the supported range shrinks to match what is.
- [ ] Exactly one interpreter carries the timing gate, with the reason recorded.
- [ ] `README.md` and `SUPPORT.md` state the tested versions rather than only the floor.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`.github/workflows/ci.yml`](https://github.com/airlock-sec/airlock/blob/main/.github/workflows/ci.yml)
- [`pyproject.toml`](https://github.com/airlock-sec/airlock/blob/main/pyproject.toml) (`requires-python`, the dev extra's tool pins)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_document`, the `tomllib` dependency)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
