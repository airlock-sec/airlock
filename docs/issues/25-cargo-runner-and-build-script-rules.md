---
slug: cargo-runner-and-build-script-rules
title: `cargo_vectors` is a docstring, so a `.cargo/config.toml` that sets a shell runner is invisible and bypass case 6 stays skipped
labels: enhancement, complexity: medium, area: rules
roadmap: 6.4, 3.9
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The rule loader, the role resolver, the combination-detector framework and the `tests/fixtures/` builders all ship, and `tests/bypass/test_bypass_6_cargo_runner.py` already contains the exact assertion to keep, so the only missing pieces are the role, the rules and unskipping that module.

## Problem

Appendix B case 6 is the shape where `.cargo/config.toml` sets `[target.<triple>].runner = "/bin/sh"` (or a wrapper script), so every `cargo test` and `cargo run` in the repository executes something the reviewer did not read. `src/airlock/detectors/cargo_vectors.py` is 190 bytes of docstring, and the test for the case is marked skip with the reason written out at `tests/bypass/test_bypass_6_cargo_runner.py:17-19`: "`.cargo/config.toml` has no role and `cargo_vectors` is not written".

The role question is the whole blocker. `rules/roles.toml` names no Cargo path, so `.cargo/config.toml` resolves by suffix: `.toml` is in `SOURCE_SUFFIXES` (`src/airlock/roles.py:110`), which makes the file `source`, which is read by the six `pat-*` rules and by nothing that understands a Cargo config. `build.rs`, which has no suffix at all, resolves to `other`, and `rules/builtin/builtin_patterns.toml:126` records that the build-script network shape was deliberately left for this task.

There is a second vector beside the runner: `target.<triple>.rustflags` with `-C linker=`, which sends every link step through a chosen program, and a `[source]` or `[replace]` block that redirects crate fetches. `ARCHITECTURE.md` 9.3 and roadmap 6.4 describe the family; 0.12's Cargo documentation questions are answerable in the same reading session but this issue does not wait on them.

## What to build

1. **Add the roles.** `cargo-config` for `**/.cargo/config.toml` and `**/.cargo/config`, and `cargo-build-script` for `**/build.rs`, each with the reason in the comment, in the voice `install-hook` and `workflow` already use. A `[[bin]]`-adjacent `build.rs` in a workspace member has to resolve, so anchor on the filename rather than a directory depth.
2. **Write the rules as data with one pairing in code.** The runner and `rustflags -C linker=` forms are single-condition patterns and belong in `rules/builtin/cargo_vectors.toml`. A `build.rs` that opens a socket *and* spawns is the combination case, which belongs in a detector built the way `config_role.py` builds `cfg-network-exec`, including its discipline of taking the fetch pattern from rule data rather than restating it.
3. **Decide severity by what a runner is.** `runner = "echo"` is a normal thing a cross-compiling workspace does; `runner` naming a path inside the repository is not the same finding as `runner` naming `/bin/sh`. Say which is HIGH and which is WARN, and give the false-positive reasoning in the rationale, because this is the rule a Rust maintainer will contest first.
4. **Unskip the regression.** Delete the `pytest.mark.skip` from `test_bypass_6_cargo_runner.py` and keep its assertion, which already names the path and the severity. That test is the acceptance proof for this issue, and G2's claim that all seven cases fail closed becomes true when it runs.
5. **Fixtures** in a new `tests/fixtures/cargo_vectors.py`, positive and negative per rule, with the negative being a real embedded-targets config: a `runner` naming `qemu-arm`, and a `build.rs` that only sets `cargo:rerun-if-changed` directives.

**Out of scope:** Reading `Cargo.toml` or `Cargo.lock`, resolving a dependency graph, running any Cargo command, and the `soroban_profile` family (6.1), which is about a different question on a different file.

## Acceptance criteria

- [ ] `.cargo/config.toml` and `build.rs` resolve to named roles, and a rule claims each role in data.
- [ ] A `runner` set to a shell and a `-C linker=` flag pointing into the repository are each a named finding.
- [ ] `tests/bypass/test_bypass_6_cargo_runner.py` runs, is no longer skipped, and passes with its existing assertion.
- [ ] Every new rule has a positive and a negative fixture, and the timing harness covers each new pattern.
- [ ] `src/airlock/detectors/cargo_vectors.py` stops being a docstring, and `ARCHITECTURE.md` 9.3 records what the family now covers rather than what it plans.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml) and a new `rules/builtin/cargo_vectors.toml`
- [`src/airlock/detectors/cargo_vectors.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/cargo_vectors.py)
- [`tests/bypass/test_bypass_6_cargo_runner.py`](https://github.com/airlock-sec/airlock/blob/main/tests/bypass/test_bypass_6_cargo_runner.py)
- [`src/airlock/detectors/config_role.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/config_role.py) (`_combination`, the pairing shape to follow)
- The Cargo configuration reference, for `target.<triple>.runner`, `rustflags` and `[source]` replacement tables

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
