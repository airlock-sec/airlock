---
slug: scan-of-a-subdirectory-reports-as-the-whole-repo
title: A scan pointed at a subdirectory reports a narrow scope as if it were the repository
labels: bug, complexity: medium, area: engine
roadmap: 2.2, 2.3, 5.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The collector, the CLI and the startup checks are all shipped and green (2.2, 2.3, 2.10), so this is one behaviour decision plus one finding, and no other issue has to land first.

## Problem

`airlock scan PATH` takes one positional path ([`cli.py:116`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py)) and passes it to
`check_runtime` and `collect` unchanged. `check_runtime` runs `git rev-parse --verify HEAD` with
`-C` on that path, which resolves to the enclosing repository, while
[`collector.list_tracked_files`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) runs `git ls-files -z --stage`, and git scopes
that listing to the directory it is called from and returns paths relative to it.

Measured on a scratch repository holding a payload-bearing `sub/package.json`: scanning the root
reports `sub/package.json`, and scanning `sub` reports the same finding at `package.json` and prints
`1 file(s) scanned`. Both runs exit 1, and neither says that the second one looked at one file out
of two. The report is honest about its own count, but `ScanReport` has no field that distinguishes
"the repository" from "a subtree of it", and `repo_head` names a commit whose tree was not scanned.

The consequence is a verdict that reads wider than the work behind it. `docs/wave/settings.md` and
`README.md` both describe the required check as "the scan", and a caller that passes a path from a
`matrix:` entry, or a monorepo tool that scans each package directory, produces a green or red result
that a reviewer will read as covering the repository. A policy file is also read relative to the
subdirectory ([`policy._working_text`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py)), so the same run silently loses the `airlock.toml`
two levels up and reports `untrusted-policy-source` for a path that is not the repository's.

## What to build

1. **Decide what a non-root path means.** Two defensible answers: refuse it, or scan it and label it.
   Refusing is a few lines in `check_runtime` (`git rev-parse --show-toplevel` compared against the
   resolved path) and is the one that cannot mislead. Labelling is what a monorepo caller wants, and
   needs a name in the report. Say which you chose and why in the record.
2. **If you keep the subtree scan, make the scope visible.** Add a scanner-state finding carrying the
   path that was asked for, the repository root git resolved, and the ratio of tracked paths that were
   outside the scanned scope. It belongs in `model.STATE_RULE_IDS` next to the other state ids, which
   makes it non-suppressible by construction (2.15 settled that ordering).
3. **Fix the policy lookup in the same pass.** A policy file is a repository-level file, so resolve it
   against the top level rather than against the argument, and keep the existing `untrusted-policy-source`
   wording accurate for whichever root you end up using.
4. **State the answer where users meet it.** `README.md` limits, `SUPPORT.md`, and
   `ARCHITECTURE.md` 6.1 or 6.5, whichever owns the collector's input contract.

**Out of scope:** monorepo partial-scan semantics as a feature (which paths a package owns, dependency
graphs, per-package policies), and any change to how `pr` mode resolves its base.

## Acceptance criteria

- [ ] A scan pointed at a subdirectory either exits 2 with a message naming the repository root, or reports a non-suppressible state finding that says the scan did not cover the whole tree.
- [ ] The `airlock.toml` of the enclosing repository is found and applied when a subtree is scanned, or the refusal makes the question moot.
- [ ] `tests/unit/test_cli.py` or `tests/unit/test_collector.py` drives the case against a real temporary repository with files both inside and outside the argument path.
- [ ] The chosen behaviour is written into `README.md` and `ARCHITECTURE.md` where a caller would read it before wiring the check.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_scan_command`, `check_runtime` call), [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`list_tracked_files`, `_state`), [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`STATE_RULE_IDS`).
- Tests: [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py) already drives real temporary repositories through the CLI, which is the shape this needs.
- git semantics: `git -C <subdir> ls-files` scopes to the directory and prints paths relative to it; `git rev-parse --show-toplevel` is the reliable way to find the root.
- The severity choice for a state finding follows the existing pattern in the collector: sensitive roles raise a skip to HIGH, so decide whether scope is a WARN or a HIGH and write the reason down.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
