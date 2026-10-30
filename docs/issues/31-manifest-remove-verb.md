---
slug: manifest-remove-verb
title: `airlock manifest` can add an artifact and cannot remove one
labels: enhancement, complexity: medium, area: engine
roadmap: 3.5, 5.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `_manifest_add` in `cli.py:270-320` already round-trips the manifest through the hand-written TOML writer and refuses a duplicate sha256 through `model.Manifest`, so the removal path is the same reader and writer with the opposite operation.

## Problem

The manifest verbs are `add` and `check` (`cli.build_parser`, lines 143-167). A repository that deletes or renames a Wasm artifact has to hand-edit `wasm-manifest.toml`, which is the file whose entries the scanner trusts: each carries `origin`, `source`, optional `build` and `note`, and the writer in `policy.py` emits them in a fixed order with its own comment handling.

Hand-editing has two failure modes this project should not ship. A maintainer deleting a path leaves the stale entry behind, and `wasm-manifest-stale` (WARN) then reports a manifest naming an artifact that no longer exists, which reads as a scanner complaint rather than as a deleted file. The more dangerous one is deleting the wrong block by hand, in a file that is the review surface for every binary artifact in the repository.

The asymmetry also makes `add` awkward in the documented workflow: `README.md` and the usage docs tell a maintainer to add an entry when an artifact lands, and say nothing about what to do when it goes, because there is no verb.

## What to build

1. **Add `manifest remove PATH` (and accept several paths).** Resolve by path, report `manifest-entry-missing` style plain errors for a path with no entry, and name the entry it removed before writing, so a wrong argument is visible rather than a no-op.
2. **Resolve the duplicate-path question here.** `model.Manifest.__post_init__` (`src/airlock/model.py:354-361`) refuses two entries with one sha256 and says nothing about two entries with one path, and `detectors/wasm_manifest.py`'s index keeps the last one silently. Removal cannot be written honestly without deciding what one path with two entries means, so this issue owns that decision together with 06 in this batch, which is the load side.
3. **Keep the writer's guarantees.** The hand-written TOML writer exists because the standard library has no TOML writer (`policy.py`, 3.5). Removal must preserve comments and ordering exactly as `add` does, and a test must show a round trip: add, then remove, then compare against the original bytes.
4. **Refuse to write an unparseable manifest.** `add` reads through the same loader that raises `policy-unknown-key` style findings; removal must refuse a manifest the scanner would not accept rather than rewriting it.
5. **Document both verbs together** in `README.md` and the usage docs, including what a caller should do about a renamed artifact (remove plus add, with the note field carried over by hand).

**Out of scope:** Any new manifest field, the `manifest check` comparison behaviour, and the trust question of where a manifest is read from, which 2.7 settled.

## Acceptance criteria

- [ ] `airlock manifest remove <path>` deletes exactly one entry, names it, and leaves the file's comments and ordering intact.
- [ ] Removing a path with no entry and removing twice in one argument list both fail with a plain message rather than silently.
- [ ] A test round-trips add then remove against the original file bytes.
- [ ] One path with two entries is either refused on load and on removal, or the choice is documented and tested, together with issue 06's resolution.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_manifest_add`, `build_parser`)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (the TOML reader and writer behind the manifest)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`Manifest.__post_init__`)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
