---
slug: large-repository-runtime-target
title: No measured runtime target exists for a large repository, so no one can tell whether a scan is too slow or simply young
labels: enhancement, complexity: high, area: tests
roadmap: 7.7, 3.11
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The pipeline runs end to end and the per-pattern ReDoS harness already exists (`tests/unit/test_redos.py`), so a synthetic repository is the only missing input; the measurement needs no new production code and can be taken against the current build.

## Problem

`PRD.md` 7 sets a per-rule cost, and 2.12 and 3.11 measure against it line-by-line and pattern-by-pattern. Nothing measures a scan. 7.7 is the row that says so: "Large-repo performance test and measured runtime target", still unticked, with 4.4's dogfooding listed as its dependency only because the real repositories are where the shape comes from.

The absence has a product cost as well as an engineering one. A maintainer deciding whether to put this in a required status check is asking how long a pull request waits, and `README.md` cannot answer; the honest answer today is one measured case, `Tollcraft/soroban-budget-assert`, on a small Rust repository. A caller that finds a scan slow on a large monorepo has no number to compare against and no finding to point at, and a maintainer has no way to tell whether a change made it slower.

A synthetic tree, not a public clone, is the right input: the shape to measure is many tracked paths with realistic role distribution and realistic line lengths, and a repository taken from the internet is exactly the kind of content the project promises never to execute or depend on.

## What to build

1. **Build the generator.** A script under `scripts/` that writes a temporary git repository with a configurable path count, a role mix (tooling configs, workflows, `package.json` files, source, docs, a handful of binaries by magic), and content that produces no findings. Commit nothing; the tree is built in a temp directory at run time, the same discipline `tests/bypass/conftest.py` uses.
2. **Record the profile.** Wall time, per-stage time for collect, engine, detectors, suppression and report, and bytes read. GitHub's own limits (10 annotations per level, 1 MiB per step) belong in the same document as the numbers, because the interesting question is a large repository with many findings.
3. **State a target and hold it.** A runtime budget for a named tree size, written into `PRD.md` 7 and `ARCHITECTURE.md` 7, with the measurement that justified it and the machine that produced it. Where a CI check is involved, follow the project's rule that hosted CI decides a timing gate rather than a local run.
4. **Find the shape, not just the size.** Include one pathological input at the limit (many lines exactly at `line_cap`), because the cap is where a scanner's cost per byte changes.

**Out of scope:** Optimising anything the measurement finds (which becomes a separate issue per finding), and using a public repository's content as the fixture.

## Acceptance criteria

- [ ] A committed generator builds a synthetic repository of a stated shape and size.
- [ ] Measured per-stage timings for that repository are recorded in the change record with the hardware and interpreter named.
- [ ] `PRD.md` 7 and `ARCHITECTURE.md` 7 carry a runtime target for a named tree size, and the target is a measurement rather than an aspiration.
- [ ] A slow test or a scheduled job re-measures and fails outside the budget, with the budget defined so a busy runner does not fail spuriously.
- [ ] `README.md` quotes the number where a caller decides whether to gate on the scan.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`scripts/`](https://github.com/airlock-sec/airlock/blob/main/scripts) (a new harness beside `bypass_probe.py`)
- [`tests/bypass/conftest.py`](https://github.com/airlock-sec/airlock/blob/main/tests/bypass/conftest.py) (the temporary repository discipline to reuse)
- [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) (the existing cost harness, and the rule about timing gates)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
