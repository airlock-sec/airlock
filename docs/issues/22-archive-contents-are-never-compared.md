---
slug: archive-contents-are-never-compared
title: An archive gets one suppressible WARN naming the file, and nothing inside it is ever looked at
labels: enhancement, complexity: high, area: engine
roadmap: 3.4, 7.6
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The archive role resolves from magic, `wasm-archive-skipped` already ships, and the standard library's own `zipfile` and `tarfile` readers are available to a dependency-free scanner, so this needs no new input to the pipeline.

## Problem

`archive` resolves from nine magic prefixes plus the tar header offset (`src/airlock/roles.py:47-58`, `roles.py:135-138`). The only rule that claims the role is `wasm-archive-skipped` (`rules/builtin/wasm_manifest.toml`), emitted once per archive file by `detectors/wasm_manifest.py:124-131` with the message "nothing inside it was compared against the manifest". It is a WARN and it is suppressible.

So a `vendor.tgz` or `dist.zip` in a pull request yields one WARN that names the archive and stops. The obvious shapes go unexamined: an unlisted `.wasm` inside the archive, a `.cargo/config.toml` with a runner, or a payload-bearing `postcss.config.js` that a build step unpacks before it runs. The scan's own promise, recorded in `AGENTS.md` 4, is that no content is silently skipped, and today the honest version of that promise for an archive is a count of archives rather than a look inside one.

Nothing here asks for extraction to disk or for executing an unpacker. Reading entry names and the first bytes of an entry is what `zipfile.namelist()` and a bounded `open()` already do in the standard library, and a `tarfile` member's `extractfile()` is the same shape.

## What to build

1. **Inventory first.** Read the entry list of every archive under the size limits and report it: entry count, names that resolve to a sensitive role or to `wasm` by extension, and the aggregate uncompressed size, which is the zip-bomb question stated rather than avoided. That alone turns a WARN about an unknown file into a WARN naming what is unknown.
2. **Then decide about contents.** Two defensible levels: match entry names against the Wasm manifest's paths and hashes, or read the head bytes of entries below a per-entry cap, resolve roles for them, and run the pattern rules over the text. The second changes what a scan costs, so if you take it, bound it with a policy setting, state the budget in `ARCHITECTURE.md` 7, and add it to the timing harness. Refusing the second with a recorded reason is a complete answer.
3. **Nested archives are a decision, not an accident.** Say in one line whether an archive inside an archive is read, counted, or refused, and make the finding message agree.
4. **Never write anything to disk, and never trust a name.** Entry names are attacker input (`../` paths, absolute paths, symlinks inside a tar); the standard library's `datafilter` is not enough on its own, and the code must only ever read bytes from the open archive.
5. **Fixtures.** An archive containing an unlisted Wasm artifact, an archive whose aggregate size exceeds the limit, an archive with a `../` entry name, and a clean archive as the negative.

**Out of scope:** Extracting archives, running anything from them, and decompression formats outside what the standard library reads without a third-party package. `zstd` and `xz` members are a recorded non-goal unless `lzma` covers them.

## Acceptance criteria

- [ ] An archive yields a finding naming its entry count and any entry whose name resolves to a sensitive or Wasm role.
- [ ] An archive containing an unlisted `*.wasm` is reported at a severity that reflects the artifact being present, or the reason it is not is recorded.
- [ ] A zip bomb shape is accounted for by a bounded reading rule rather than by attempting to read everything.
- [ ] No code path writes, extracts or executes archive content, and a test asserts the handling of a `../` entry name.
- [ ] The measured per-file cost of the new reading is recorded in the timing harness or in the change record.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/detectors/wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py)
- [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`_ARCHIVE_PREFIXES`, `_TAR_MAGIC_AT_257`)
- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`HEAD_BYTES`, the size limits an archive is already subject to)
- The `zipfile` and `tarfile` standard library references, including what each refuses to do safely

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
