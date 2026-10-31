---
slug: temporary-repositories-are-built-in-five-places
title: Each suite that needs a git repository re-implements how to build one, and the constraints only one of them gets right
labels: enhancement, complexity: medium, area: engine
roadmap: 2.12, G2
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The four builders already exist and can be read side by side (`tests/unit/test_collector.py:364`, `tests/bypass/conftest.py`, `scripts/bypass_probe.py:120` and the CLI tests), and the collector's requirements are all observable in `check_runtime` and `list_tracked_files`.

## Problem

A test repository for this scanner has to satisfy real conditions: `git rev-parse --verify HEAD` must resolve (`collector.check_runtime`), the worktree must be readable under `safe.directory`, index entries must be stage 0 (2.14's fix was exactly about entries that are not), and a file must be tracked and committed rather than merely written. `git init -q` plus `add` plus `commit` gets there by luck on a default branch name and fails on a machine whose `init.defaultBranch` differs or where `user.email` is unset.

The suite builds these repositories in several places, each with its own subset of the constraints: `tests/unit/test_collector.py:364` has `make_repo`, `tests/bypass/conftest.py` has the bypass fixture's own, `scripts/bypass_probe.py:120` builds one per Appendix B case in a temp directory, and the CLI tests build yet another. When a collector precondition changes (2.2, 2.14 and 7.2 each changed one), every builder that does not encode it starts testing a repository the scanner would refuse, and the failure reads as a scanner bug.

## What to build

1. **One builder in `tests/`.** A helper taking a path map and returning a committed repository, setting `user.name`, `user.email`, `init.defaultBranch` and `safe.directory` explicitly so the result does not depend on the machine's git configuration.
2. **Let the bypass harness share it.** `scripts/bypass_probe.py` runs outside pytest and must stay able to; the helper should live where both can import it, or the script keeps a deliberately identical copy with a test that asserts the two agree on the settings they each write.
3. **Encode the preconditions as names.** `stage0=True`, `detached=False`, `clean=True` style arguments, so a test that wants an unmerged index says so rather than discovering it by accident.
4. **Document the git configuration the suite assumes** in `CONTRIBUTING.md`, since a contributor with a global `init.defaultBranch=master` should get the same result as CI.

**Out of scope:** Any change to what the collector accepts, and the Windows path questions (7.8), which this helper makes testable but does not itself answer.

## Acceptance criteria

- [ ] One helper builds test repositories for the unit suite, the bypass regressions and the CLI tests.
- [ ] The helper sets branch name, identity and ownership explicitly, so a machine with an unusual global git config produces the same repository.
- [ ] Every call site that used a private builder is gone or is covered by a test proving it agrees with the helper.
- [ ] `CONTRIBUTING.md` states the git configuration the suite assumes.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`tests/unit/test_collector.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_collector.py) (`make_repo`)
- [`tests/bypass/conftest.py`](https://github.com/airlock-sec/airlock/blob/main/tests/bypass/conftest.py)
- [`scripts/bypass_probe.py`](https://github.com/airlock-sec/airlock/blob/main/scripts/bypass_probe.py)
- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`check_runtime`, `list_tracked_files`)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
