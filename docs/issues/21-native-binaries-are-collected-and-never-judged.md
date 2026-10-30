---
slug: native-binaries-are-collected-and-never-judged
title: A committed ELF, Mach-O or PE file is hashed, role-tagged and reported by nothing
labels: enhancement, complexity: medium, area: rules
roadmap: 3.4, 6.4
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The magic detector, the collector's binary branch and the manifest rule that demonstrates the treatment all ship (`roles.py:129-139`, `collector.py:358-365`, `rules/builtin/wasm_manifest.toml`), so this is a decision about parity with the Wasm artifacts plus the rules to express it.

## Problem

`roles_from_magic` returns `native-binary` for ELF, the PE `MZ` prefix and ten Mach-O prefixes (`src/airlock/roles.py:35-45`). The collector then takes the binary branch: it hashes the file, records the role, and returns an entry with `text=None` and no finding at all (`src/airlock/collector.py:358-365`), with the comment saying text rules over a binary "would only produce noise".

No rule in `rules/builtin/` claims `native-binary`, and `rules/builtin/builtin_patterns.toml:8-10` records the omission as intentional: the role is absent "because a file that resolves to one of them carries no text for a line rule to read". That is true of the line rules and false of the question a reviewer actually asks, which is whether the artifact belongs in the repository.

Compare the sibling class. A `*.wasm` file with no manifest entry is `wasm-unlisted`, HIGH, and blocks the merge (`rules/builtin/wasm_manifest.toml`, `detectors/wasm_manifest.py`). A prebuilt `.node`, `.so` or `.dll` checked into the same repository, which is what a native dependency ships and what a compromised release cycle would replace, produces no finding of any severity. The scanner hashes it, so the bytes are known; nothing ever asks whether they should be there.

The same asymmetry is why an LFS pointer named `payload.wasm` is reported and one named `payload.bin` is not; 7.1 covers that half, and 23 in this batch is the issue for it.

## What to build

1. **Decide the contract.** Options, cheapest first: an INFO or WARN inventory finding naming every `native-binary` path and its sha256, so a reviewer sees the list even when nothing is wrong; or a HIGH over-list treatment mirroring `wasm-unlisted` with a manifest of allowed binaries. Inventory first is the honest start, because no allow file exists yet and a HIGH without a way to be correct is a false-positive machine.
2. **Name the second signal.** A native binary whose role came from magic but whose extension claims text (`payload.rs` that is an ELF, which `roles.py:204-208` calls out) is a different and stronger finding than an ordinary `.so`. Decide whether it is one rule with two severities or two rules, and keep the wording in the rationale exact.
3. **Add the allow path in the same change if you make it HIGH.** A list of permitted binary paths and hashes belongs beside the Wasm manifest, which is in policy and trusted from the base, not in the working tree. If that is where it goes, then the policy loader, the docs and a `manifest` verb question all become part of this issue, and an inventory finding is the smaller and better first step.
4. **Fixtures.** A real tiny ELF or PE built by the test at run time, never committed as bytes, in the style `tests/fixtures/wasm_manifest.py` already uses for Wasm magic.

**Out of scope:** Any attempt to inspect a binary's internals (symbol tables, section names, embedded scripts), the Wasm manifest's own behaviour, and archives, which 22 in this batch covers separately.

## Acceptance criteria

- [ ] A committed file whose magic resolves to `native-binary` yields a named finding carrying its path and sha256.
- [ ] A binary whose extension claims a source role yields a distinct or clearly stronger finding, with the reasoning in the rule's rationale.
- [ ] The finding's severity, suppressibility and the reason for both are stated in rule data and in `ARCHITECTURE.md` 9 where the artifact families are described.
- [ ] Positive and negative fixtures build the magic bytes at test time and the fixture-coverage check accepts them.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`_NATIVE_PREFIXES`, `roles_from_magic`)
- [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (the binary branch of `_collect_one`)
- [`src/airlock/detectors/wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py) (`wasm-unlisted`, the treatment to mirror or refuse)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
