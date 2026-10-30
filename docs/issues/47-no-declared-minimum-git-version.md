---
slug: no-declared-minimum-git-version
title: The collector parses `git ls-files --stage` output and nothing states which git versions that output is valid for
labels: enhancement, complexity: medium, area: engine
roadmap: 2.3, G1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `check_runtime` already performs the runtime version and capability checks the project promises to fail closed on (2.3), and `list_tracked_files` parses one documented output format, so the missing piece is a stated floor plus the finding that enforces it.

## Problem

`collector.git_bytes` shells out with a 120 second timeout (line 109) and `list_tracked_files` parses `git ls-files -z --stage` (line 153) into `IndexEntry` objects, expecting the `<mode> <sha> <stage>\t<path>` shape; `_GITLINK_MODE` and `_SYMLINK_MODE` are matched as literal strings. `check_runtime` verifies that git exists, that `HEAD` resolves and that the repository is readable, and says nothing about which version produced the listing. `policy._blob_at` reads through `git_text`, and the submodule path parses `.gitmodules` itself.

`AGENTS.md` 4 forbids silently skipping content, so a git old enough to print a shape the parser mis-reads must not produce a quiet partial scan: the honest outcome is a refusal naming the version. Today an unexpected output shape is either an exception in `IndexEntry.is_well_formed`'s caller or a path list with something missing from it, and neither answer is stated anywhere in the documents that name requirements.

2.3 is the row for the startup checks and already carries the same design decision for the Python version and `safe.directory`.

## What to build

1. **Pick the floor from the format, not from convenience.** Name the oldest git whose `ls-files --stage -z`, `cat-file`, `rev-parse` and NUL-separated output the parser accepts, and record where each behaviour came from. A version obtained from a container, not a guess, with the number in the change record.
2. **Fail closed with a finding, not a traceback.** Below the floor the run should exit 2 with the plain message `check_runtime` already uses for a missing `HEAD`, naming the version found and the version required.
3. **Test it.** A test that runs the parser against captured output samples, plus a test of the refusal path with the version check stubbed at the seam `check_runtime` already provides.
4. **Say it in the documents that state requirements** (`README.md`, `SUPPORT.md`, and the workflow usage docs), because a caller on an older runner needs the version, not the issue.

**Out of scope:** Supporting output shapes from older git versions, and any change to what the collector parses.

## Acceptance criteria

- [ ] A named minimum git version exists, is checked in `check_runtime`, and is stated with the format behaviours that motivated it.
- [ ] A repository whose git is below the floor exits 2 with a message naming both versions.
- [ ] A test covers the refusal path and a test covers parsing at the floor.
- [ ] `README.md`, `SUPPORT.md` and the usage docs state the floor.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`git_bytes`, `check_runtime`, `list_tracked_files`, `IndexEntry`)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_blob_at`)
- [`tests/unit/test_collector.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_collector.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
