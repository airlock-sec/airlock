---
slug: composite-action-files-are-not-workflows
title: A composite action's `action.yml` runs in the caller's job with the caller's token and resolves to no workflow role
labels: bug, complexity: medium, area: rules
roadmap: 7.5, 3.6
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The workflow role, the three workflow rules and the pairing detector all ship and are green (3.6, 2.4), so this is one glob and the right first condition for a file that has no `on:` block.

## Problem

`workflow` resolves from `**/.github/workflows/*.yml` and `*.yaml` (`rules/roles.toml`), and its comment explains the deliberate breadth: a nested copy is matched anywhere in the tree so that a duplicated workflow is read rather than waved past.

`.github/actions/build/action.yml` is not under `workflows/`, so it resolves to `source` alone. Nothing in `rules/builtin/ci_surface.toml` reads it: `pat-privileged-trigger`, `pat-secret-dump` and `pat-ptr-head-checkout` all claim `roles = ["workflow"]` (lines 37, 48, 58).

That is the wrong conclusion about the file's authority. A composite action's `runs.steps[].run:` block executes in the *calling* workflow's job, with the calling repository's `GITHUB_TOKEN`, against inputs the caller passes. A repository that vendors a composite action under `.github/actions/` has put a shell script inside the trust boundary of every workflow that uses it, and this build says nothing about it.

The rule file's comment for `workflow` anticipates the shape without reaching it: these paths are named as roles "rather than left to the extension fallback so that `SENSITIVE_ROLES` can make an unreadable one of them a HIGH finding". Today an unreadable `.github/actions/foo/action.yml` is an ordinary skip.

## What to build

1. **Give the file a role.** Add `**/.github/actions/**/action.yml` and `.yaml` to `workflow`, or add a sibling role such as `composite-action` if you want the two treated differently; say which, and why.
2. **Fix the pairing that assumes `on:`.** `_head_checkout` in `ci_surface.py:143-166` requires a privileged trigger line, a checkout step and a head ref in one file. A composite has no `on:` block, so that HIGH can never fire in one, whatever roles it resolves to. Decide what the equivalent combination is for a composite, with the honest candidates being a `using: composite` file that itself runs `actions/checkout` with a ref derived from an input, and a caller passing `${{ github.event.pull_request.head.sha }}` as that input; note that the second is a cross-file pairing and say whether it belongs here or is recorded as a residual.
3. **`pat-secret-dump` needs no change** and should be checked rather than assumed: a `run:` that echoes `${{ inputs.token }}` is not `${{ secrets.* }}`, so decide whether an action input that is fed a secret is in scope for that rule.
4. **Fixtures.** A composite action positive and negative in `tests/fixtures/ci_surface.py`, where the negative is the common `action.yml` that only runs a pinned local script.

**Out of scope:** Reusable workflows called with `workflow_call` (they live under `workflows/` and are already read), JavaScript action code, and any Docker action internals.

## Acceptance criteria

- [ ] A shell step inside `.github/actions/<name>/action.yml` is read by at least one workflow rule, and by `pat-secret-dump`.
- [ ] The combination that cannot fire without an `on:` block is either re-expressed for composites or recorded as a named residual in the rule file and `ARCHITECTURE.md` 9.6.
- [ ] An unreadable composite action becomes a HIGH through `SENSITIVE_ROLES`, matching what the role comment promises.
- [ ] Positive and negative fixtures cover the composite shape and the ordinary case.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml) (`workflow` globs and their comment)
- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (`_head_checkout`'s three conditions)
- [`rules/builtin/ci_surface.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/ci_surface.toml)
- The GitHub Actions composite and reusable workflow references, for what a composite step can and cannot see

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
