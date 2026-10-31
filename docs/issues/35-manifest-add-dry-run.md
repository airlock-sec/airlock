---
slug: manifest-add-dry-run
title: `manifest add` writes the trusted file before a reviewer can see the entry
labels: enhancement, complexity: trivial, area: engine
roadmap: 3.5, 5.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `_manifest_add` (`src/airlock/cli.py:270-320`) already builds the complete new text in memory before it writes it at line 297, so a dry run is the same computation with the write replaced by a print.

## Problem

`manifest add` is the recommended way to record a Wasm artifact: it resolves the path, hashes the bytes, takes `origin`, `source`, `build` and `note` as flags, and rewrites `wasm-manifest.toml` with the hand-written TOML writer. The entry lands in the file the moment the command runs, and the reviewer sees it in a diff rather than choosing it.

Three cases want the preview first. A CI job that tells a maintainer "this artifact is unlisted; add it" should print the entry rather than write a file that then needs a commit and a review. A maintainer adding a rebuilt artifact wants to see whether the hash actually changed before editing the record of what it should be. And a repository with several artifacts wants a batch preview: `manifest add a.wasm b.wasm` writes when the second path is wrong unless the whole operation is checked first.

3.5's own acceptance wording is that adding a fixture takes one command and round-trips, which is exactly the property a dry run preserves and a hand edit loses.

## What to build

1. **Add `--dry-run` to `manifest add`.** Print the entry text exactly as the writer would emit it, including its position in the file, and write nothing. Non-zero or zero exit is a decision worth stating: the recommendation is exit 0 with no write, so a CI job can use the flag as advice rather than as a gate.
2. **Validate the whole argument list before the first write.** With several targets, any failure (a path outside the repository, an unreadable file, an artifact whose magic is not `\0asm`, a duplicate sha256 that `model.Manifest.__post_init__` would refuse) must prevent every write, and the message must name which target failed.
3. **Make the dry run the contract test for `add`.** A test asserting that the same argument produces the printed text and the written bytes, so the preview cannot drift from the real operation.
4. **Say what `origin` and `source` mean when a machine fills them in.** A CI job printing a suggested entry is not attesting to its provenance; the dry-run output should carry the same comment the writer emits, so a maintainer reads the fields as a question rather than as an answer.

**Out of scope:** `manifest remove` (31 in this batch), any change to the entry fields, and the write-failure classification that 02 in this batch covers.

## Acceptance criteria

- [ ] `--dry-run` prints the exact entry text and leaves the manifest byte-identical.
- [ ] A multi-target add with one bad path writes nothing and names the failed target.
- [ ] A test proves the dry-run output and the written file are produced by one code path.
- [ ] `README.md` and the usage docs show the flag in the CI-advice position.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_manifest_add`, its argument validation)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (manifest writer and reader)
- [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
