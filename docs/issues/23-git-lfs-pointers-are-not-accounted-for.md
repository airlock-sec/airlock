---
slug: git-lfs-pointers-are-not-accounted-for
title: `.gitattributes` can move tracked content to LFS and the scan reports the pointer as the file
labels: enhancement, complexity: medium, area: engine
roadmap: 7.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The collector already reads `.gitattributes` as a tracked file and already distinguishes an LFS pointer from an artifact when the name ends in `.wasm` (`detectors/wasm_manifest.py:8-9`, `policy.py:866`), so the remaining half is accounting for the pointers that are not named that way.

## Problem

`FR-20` is recorded in `src/airlock/policy.py:866` inside the manifest check's message: a Wasm artifact entry expects the artifact and "a git LFS pointer is not the artifact". That case is genuinely covered, because `*.wasm` under LFS still resolves by name, its head bytes are `version https://git-lfs...` rather than `\0asm`, and `wasm-hash-mismatch` or `wasm-unlisted` says so.

The uncovered half is everything else. `.gitattributes` is a tracked file whose `filter=lfs` patterns decide, at checkout, which paths a scanner sees as bytes and which it sees as 130-character pointers. A repository that adds

```gitattributes
*.bin filter=lfs diff=lfs merge=lfs -text
vendor/** filter=lfs
```

has moved its real content off the scanned object, and the scan reports each pointer as an ordinary text file with its own sha256: the hash in the report, in a suppression entry's `file_sha256`, and in the Wasm manifest's expected value is the hash of the pointer. Nothing anywhere says that the bytes the CI job will materialize were never read.

This is a documented gap rather than a hidden one; 7.1 asks for exactly it, "Git LFS pointer handling and the Wasm-as-base64 gap documented".

## What to build

1. **Read the attributes file as input to the report, not as a scanned artifact.** Parse the `filter=lfs` patterns from tracked `.gitattributes` files in the collector, and resolve each tracked path against them with the same precedence git uses (last match wins, and a negation with `!`).
2. **Emit one state finding.** A non-suppressible scanner-state finding, or a WARN per affected glob, naming the pattern, the number of tracked paths under it, and the fact that the scanned content is the pointer rather than the object. Choose one and say why; a per-file finding on a repository with 900 LFS paths is a flood, and `rules.cap_findings` is the precedent for one finding per file naming a count.
3. **Detect the pointer regardless of the attributes.** The 128-character `version https://git-lfs.github.com/spec/v1` header plus `oid sha256:` is a shape; recognising it means a pointer cannot hide by the `.gitattributes` being deleted in the same commit. State which of the two signals the finding relies on, because they answer different questions.
4. **Say plainly what is not scanned.** The pointer's `oid` names the real bytes, and fetching them is a network call, which `AGENTS.md` 4 forbids during a scan. The finding must report the `oid` value so a reviewer can look it up, and the docs must say the scanner never did.
5. **Fixtures and docs.** A repository fixture with `.gitattributes` and a pointer, a negative with an attributes file that sets only `text eol=crlf`, and the limits paragraph in `README.md` plus `ARCHITECTURE.md` 6.1 updated.

**Out of scope:** Fetching, verifying or hashing LFS objects, and the Wasm-as-base64 half of 7.1, which 24 in this batch covers.

## Acceptance criteria

- [ ] A tracked path that `.gitattributes` routes through `filter=lfs` is reported as a pointer, naming the pattern and the count.
- [ ] A file whose first line is the LFS pointer header is recognised even with no `.gitattributes` entry naming it.
- [ ] The pointer's `oid` appears in the finding, and the report states that the referenced bytes were not scanned.
- [ ] One state finding or one WARN per pattern keeps a large LFS repository's report readable, and a test pins that count.
- [ ] `README.md` limits and `ARCHITECTURE.md` 7.1's residual note agree with what shipped.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`_parse_gitmodules` is the in-tree precedent for reading a config file for its own sake)
- [`src/airlock/detectors/wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`STATE_RULE_IDS`, if the finding is a state finding)
- The gitattributes and git-lfs specification, for pattern precedence and the pointer format

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
