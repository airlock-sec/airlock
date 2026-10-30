---
slug: airlock-init-for-a-target-repository
title: Adopting the scanner means copying three files by hand, and a wrong copy fails closed in a way that reads as the scanner being wrong
labels: enhancement, complexity: medium, area: engine
roadmap: 5.1, 4.2
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The policy loader, the manifest format and the workflow shape are all settled and shipped, and `docs/wave/settings.md` already documents every field a generated `airlock.toml` would carry, so this is a writer over documented defaults.

## Problem

A maintainer adopting `airlock` today writes, from prose: a workflow file with the checkout at full depth, the read-only permissions and the pinned action SHA; an `airlock.toml` with a `version` field the loader requires (`policy._require_version`) and a `[policy]` table whose key names must match `model.POLICY_SETTINGS_KEYS` exactly, because an unrecognised key is a `policy-unknown-key` finding rather than a warning; and a `wasm-manifest.toml` if the repository ships a binary artifact.

Two of those three have a fail-closed trap in them. A policy key spelled wrongly produces a finding on every scan of the repository until someone reads it. A `version` that is absent stops the run. Both are correct behaviour (the policy file is trusted input, and a loader that ignored unknown keys would let a typo silently disable a control), and both are the kind of first-run failure that a generator removes rather than a document explains.

4.2 is the caller workflow snippet and usage docs, and it is written as prose. A command that emits the same three files, validated through the loader that will read them, is the version of 4.2 a maintainer can run.

## What to build

1. **Add `airlock init`.** Write `airlock.toml` with the current required version and every shipped policy setting at its default, each commented with one line saying what changing it would do; write `wasm-manifest.toml` only if the repository has a tracked `.wasm`; and print, never write, the workflow snippet with a placeholder for the pinned SHA and the instruction to fill it.
2. **Generate from the loader's own vocabulary.** The key names, defaults and version string come from `model.POLICY_SETTINGS_KEYS`, `BOOTSTRAP_POLICY` and the manifest constants, not from literals in the command, so the generated file parses by construction. Add a test that round-trips the generated file through `resolve_policy` and asserts no `policy-unknown-key`.
3. **Refuse to clobber.** A repository that already has a policy gets a plain error naming the path, never an overwrite: the policy file is the review surface for what the scanner is allowed to ignore.
4. **Say what init does not do.** It must not commit, must not add a remote, must not enable the scan in CI, and must not write a suppression. Help text plus the docs carry that sentence.
5. **Keep the docs as the explanation.** `README.md`'s install section keeps the manual path, because a maintainer has to understand what they are agreeing to; the command is the shortcut, not the documentation.

**Out of scope:** `action.yml` (the open issue #34), any automatic commit or push, and configuration beyond the two trusted files.

## Acceptance criteria

- [ ] `airlock init` writes a policy file that the loader accepts with no `policy-unknown-key` and no `policy-version-*` finding.
- [ ] Every setting in the generated file is a default carried from `BOOTSTRAP_POLICY` rather than a literal in the command.
- [ ] An existing `airlock.toml` is never overwritten, with a test that proves it.
- [ ] The printed workflow snippet matches the documented one in `docs/wave/settings.md`, and a test asserts the permission block it emits is read-only.
- [ ] `README.md` and `SUPPORT.md` name the command next to the manual path.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (the command surface, `_manifest_add` as the writer pattern)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`BOOTSTRAP_POLICY`, the TOML writer, `_require_version`)
- [`docs/wave/settings.md`](https://github.com/airlock-sec/airlock/blob/main/docs/wave/settings.md) (the field-by-field reference the generator has to match)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
