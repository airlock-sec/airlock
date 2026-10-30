---
slug: wasm-manifest-accepts-two-entries-for-one-path
title: `wasm-manifest.toml` can list one path twice under two hashes and the scan picks one silently
labels: bug, complexity: trivial, area: engine
roadmap: 3.4, 3.5
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The manifest model and the detector are shipped and tested (3.4, 3.5), and `manifest add` already round-trips through the same loader, so this is one validation rule in `model.py` and a fixture.

## Problem

[`Manifest.__post_init__`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) refuses two entries carrying the same `sha256`. Nothing
refuses two entries carrying the same *path*, and a manifest with both is easy to produce by accident:
someone rebuilds an artifact, runs `airlock manifest add` with a different `--source`, and the writer
appends a second entry because the hash is new, while the first entry is still in the file.

Reproduced against `main` with two entries claiming `contract.wasm` under different hashes: the model
constructs cleanly and no finding is raised about the file itself.

What the detector then does is decided by [`wasm_manifest._index`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py),
which folds the entries into `by_path` with a plain dict assignment, so the entry that wins is whichever
the loader left last. That determines whether a given artifact reads as `wasm-hash-mismatch` (HIGH),
`wasm-path-moved` (WARN) or clean, and it is decided by the order of two blocks in a file nobody
reviewed for order. A maintainer looking at a green `manifest check` has no signal that the manifest
contradicts itself about what the file at that path is supposed to be.

The same collision has a second face: `[[suppress]]` entries in `airlock.toml` are matched on
rule plus path plus fingerprint, so nothing here leaks into suppression behaviour, but the manifest is
the file whose whole job is to say what an artifact *is*. One path, one meaning, or the file says two.

## What to build

1. **Refuse the duplicate at load time** in `Manifest.__post_init__`, the way the duplicate hash is
   refused today. The error must name the path and both hashes, and it must reach the operator as exit 2
   with a plain message, which is what `policy.py` already does for a manifest that will not parse.
2. **Decide the `pr` and `push` shape deliberately.** A base manifest that fails to load has to produce
   a fallback rather than a traceback; follow whatever `_manifest_at_base` does for a version mismatch
   today and keep that behaviour consistent, with the finding naming the reason the manifest was not used.
3. **Check the writer too.** `manifest add` should refuse to create the collision, or repair it, and say
   which in its output. A canonical writer that sorts entries is not the same as a writer that merges
   them.
4. **Fixtures**: one manifest that would have been accepted before and is now refused, and one clean
   manifest with two paths on one hash that must keep working.

**Out of scope:** manifest `version` handling, the two-step FR-06 flow, and anything about how
`wasm-path-moved` is decided for a single unambiguous entry.

## Acceptance criteria

- [ ] A manifest with two entries claiming one path is refused with a message naming the path and both hashes, and the refusal is visible in `manifest check` and in a scan, not only in a unit test.
- [ ] `manifest add` cannot produce the collision, or reports and repairs it.
- [ ] Both fallback paths (`pr` mode with a colliding base manifest, `full` mode with a colliding working-tree manifest) are tested and produce the documented exit code.
- [ ] `ARCHITECTURE.md` 7.6 or 7.7 states the invariant: one tracked path is described by one manifest entry.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`Manifest`, `WasmEntry`), [`src/airlock/detectors/wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py) (`_index`).
- Code: [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`manifest_from_toml`, `manifest_to_toml`, `manifest_add`, `_manifest_at_base`).
- Tests: [`tests/unit/test_wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_wasm_manifest.py) and the CLI cases in [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py).
- The writer is hand-written because the standard library has no TOML writer (3.5), so a rule the loader enforces has to be enforced by the writer separately.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
