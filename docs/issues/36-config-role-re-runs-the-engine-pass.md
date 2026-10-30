---
slug: config-role-re-runs-the-engine-pass
title: `config_role` re-runs every pattern rule over the tooling configs the engine has already matched
labels: enhancement, complexity: medium, area: engine
roadmap: 3.1, 3.11
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The engine pass and the detector are both shipped, and `runner.engine_findings` already collects every pattern hit before any detector runs, so passing the relevant lines to the detector is a plumbing change with no new matching.

## Problem

`runner.engine_findings` loops the entries and calls `apply_patterns` for each (`src/airlock/runner.py:29-35`). `detectors/config_role.py:185` then calls `apply_patterns(ctx.rules, entry, ctx.policy.line_cap)` again, per tooling-config entry, and filters the result for `cfg-network` and `cfg-dynamic-code` lines because the combination rule needs them.

So a repository's build configs are matched twice by every pattern rule: `cfg-long-line`, `cfg-chain-endpoint`, and all six `pat-*` rules, which claim `source`, `tooling-config`, `editor-autorun` and `other`, run over a `next.config.js` once in the engine and once in the detector. 3.11's measured costs are per pattern over adversarial text, which means this doubles the measured cost of every rule on exactly the role the family exists to police.

The second split is also the third: `config_role._text_lines` splits `entry.text` again to get its own line map, and `cap_findings` (`rules.py:312-316`) splits it a second time in the engine. The engine and the detector also cannot share the intermediate today, because `ScanContext` carries only rules, entries, policy and the four fields 2.13 settled (`model.py:391-404`), which is the honest place to say where the fix belongs.

## What to build

1. **Give the detector the lines it needs.** Either pass the engine's per-entry pattern findings into the detector's context, or have the combination rule take the network and dynamic-code lines from a value the engine already computed. The first keeps `config_role` free of matching logic; the second is a smaller diff.
2. **Split each text once.** One line index per entry, built by the collector or lazily and cached on the entry, used by `apply_patterns`, `cap_findings` and each detector's `_text_lines`. `FileEntry` is a frozen dataclass, so a cached view is a design question, not a one-liner: state which you chose.
3. **Prove it changed the cost.** Add a measurement to `tests/unit/test_redos.py` or a benchmark script that runs the same corpus through both builds and records the ratio, with no timing budget weakened.
4. **Refuse the finding-visible changes.** Fingerprints, occurrence numbering and report ordering must be identical before and after, because 2.6 and 2.12 make the report a stable contract. A test that compares full JSON output before and after the refactor is the acceptance proof.

**Out of scope:** Any change to which rules match, to `line_cap` semantics, or to the combination rule's logic. This is about running the same matching once instead of twice.

## Acceptance criteria

- [ ] A tooling-config file's text is split at most once per scan, and each pattern rule runs over each line once.
- [ ] The JSON report for every fixture is byte-identical before and after, with a test asserting it.
- [ ] A measured before-and-after cost for a corpus of build configs is in the change record.
- [ ] `config_role.py`'s module docstring says where the pattern lines come from.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/runner.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/runner.py) (`engine_findings`)
- [`src/airlock/detectors/config_role.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/config_role.py) (`run`, `_text_lines`)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`FileEntry`, `ScanContext`)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
