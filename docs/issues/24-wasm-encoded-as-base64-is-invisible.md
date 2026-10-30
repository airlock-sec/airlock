---
slug: wasm-encoded-as-base64-is-invisible
title: A Wasm module carried as base64 inside a text file never resolves to the artifact role, so no manifest comparison applies
labels: enhancement, complexity: high, area: rules
roadmap: 7.1, 3.4
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The role resolver, the manifest comparison and the two-condition detector framework all ship (2.4, 3.4, 3.6), and the gap is written down as 7.1's second half, so this is one detection decision plus fixtures.

## Problem

`roles_from_magic` looks at the head of the file and nothing else (`src/airlock/roles.py:129-139`): `WASM_MAGIC` at offset 0 makes a `wasm` role, which is what puts a file in front of `wasm-unlisted` and `wasm-hash-mismatch`. A module whose bytes are carried inside a text file as base64 has no offset 0 anywhere.

The shape is common and it is what an artifact-smuggling commit looks like: a `const module = "AGFzbQEAAAA..."` in a JS file, a `data:application/wasm;base64,` URL in a manifest, or a `WebAssembly.instantiate(Uint8Array.from(atob(payload), c => c.charCodeAt(0)))` loader. None of it is compared to `wasm-manifest.toml`, and today the only signal available to the engine is incidental: `pat-decode-eval` fires on `atob` feeding an evaluator, and `instantiate` is not an evaluator in its alternation (`rules/builtin/builtin_patterns.toml`, the pattern on `pat-decode-eval`).

7.1 asks for this gap to be documented, and documenting it is the floor of this issue rather than the whole of it: the loader verb and the marker are cheap to detect, and detecting them is what makes a written-down residual a control with a finding id.

## What to build

1. **Anchor on a literal, then decode a bounded window.** The pattern that cannot blow up is a short literal marker (`AGFzbQ`, which is what `\0asm\1\0` encodes to, plus the `data:application/wasm` form) or a loader verb, followed by a base64 candidate of bounded length. Keep every matcher a literal or a bounded class: the reasoning in `detectors/ci_surface.py`'s module docstring for why a downloader-then-shell regex was split into two linear searches applies exactly here.
2. **Require the pair.** A marker alone in a data file is a false positive; a marker plus something that would turn it into bytes, or a marker long enough to be a module, is the finding. Write which pairing the rule claims, and what it cannot claim.
3. **Then decide the manifest question.** A detected embedded module has no path of its own, so `wasm-manifest.toml` cannot key it. The options are to report it as an unlisted artifact family with its own hash (the decoded bytes' sha256, which is computable and stable), or to report it and record that the manifest does not cover it. Whichever you pick, the message must not imply that a manifest entry would have made it safe.
4. **Respect the cap.** The candidate window has to be inside `line_cap`'s rule, and an over-cap line is `cfg-long-line`'s account, which 20 in this batch is about: a base64 blob is exactly the kind of line that gets long.
5. **Fixtures.** Positive for each marker family, a negative that is a legitimate long base64 value that is not a module (an image data URL, a font), and the near-miss line at the cap in the timing harness.

**Out of scope:** Decoding, validating or parsing a Wasm module's sections, which is 9.5's section parser, and any change to how a real `*.wasm` file is matched against the manifest.

## Acceptance criteria

- [ ] A base64 Wasm module inside a text file yields a named finding carrying the decoded bytes' sha256, or the reason it does not is recorded in the rule's rationale.
- [ ] A long base64 value that is not a module, and a `data:` URL naming an image, produce no finding, each with its own fixture.
- [ ] Every matcher added is a literal or a bounded class, and the harness measures the new pattern's cost on an adversarial near-miss line.
- [ ] `ARCHITECTURE.md` 7.1's residual list and `README.md` limits name the new detection instead of describing it as unmeasured.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`WASM_MAGIC`, `roles_from_magic`)
- [`rules/builtin/builtin_patterns.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/builtin_patterns.toml) and `rules/builtin/wasm_manifest.toml`
- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (the two-condition shape, and the ReDoS reasoning to follow)
- The Wasm binary format specification, for the 8-byte header the encoding has to match

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
