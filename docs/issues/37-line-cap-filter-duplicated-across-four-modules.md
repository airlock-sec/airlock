---
slug: line-cap-filter-duplicated-across-four-modules
title: Four modules each implement the `line_cap` filter and the line split, and one of them has to stay right for the ReDoS rule to hold
labels: enhancement, complexity: medium, area: engine
roadmap: 2.5, 3.11
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The filter is the same four lines everywhere it appears, and `rules.line_matches` already exists as the single place a rule's pattern is applied, so this is a consolidation that touches no matching behaviour.

## Problem

The rule that a regex never sees a line longer than `line_cap` is a security property, and it is currently enforced in four places that must agree. `rules.apply_patterns` skips an over-cap line (`src/airlock/rules.py:285-287`) and `rules.cap_findings` collects it (`rules.py:312-316`); `detectors/ci_surface.py:96-98` filters through `_searchable`; and `detectors/config_role.py:60-70` filters inline inside `_spawn_tier`, `_require_lines` and `_tail_finding`'s own line walk. Each of them also splits `entry.text` its own way: `ci_surface._text_lines` and `config_role._text_lines` are byte-identical functions in two modules, both different from the enumerate inside `apply_patterns`.

The failure mode is not slowness, it is a detector that forgets the filter. `ci_surface.py`'s docstring names exactly this: an over-cap line read by a second uncapped reader would be "a ReDoS hole in the one layer meant to close it", which is why that module's trigger and fetch halves call `rules.line_matches` rather than carrying their own pattern. The same reasoning has not been applied to the line source: a future detector that iterates `entry.text.splitlines()` directly gets no cap, no shared skip behaviour, and no failing test.

The consolidation is also what makes 36's once-per-entry line index land in one place rather than four.

## What to build

1. **One line source per entry.** A function in `rules.py` (or a small `lines.py`) that takes an entry and `line_cap` and yields `(number, line, over_cap)` in file order, with the `\r` removal in one place. Every engine and detector path uses it.
2. **Make forgetting the cap hard.** Either the accessor hands out only searchable lines plus a separate count of over-cap lines, or a lint-style test asserts that no module outside the allowed set calls `splitlines` or `split("\n")` on `entry.text`. Pick one and say which.
3. **Keep the cap finding single.** `cap_findings` is the only emitter of `cfg-long-line`; the shared accessor must report over-cap lines without emitting, so the engine's single finding per file stays single.
4. **Delete the two duplicate `_text_lines`.** `ci_surface.py:88-89` and `config_role.py:52-53` become calls.
5. **Byte-identical report, again.** Same acceptance test as 36: every fixture's JSON output unchanged, and the timing harness unchanged in budget.

**Out of scope:** Any change to `line_cap` itself, to how the cap finding's severity is chosen (20 in this batch), or to which lines a rule matches.

## Acceptance criteria

- [ ] One function produces per-entry line numbers, searchable lines and over-cap lines, and all engine and detector paths call it.
- [ ] A test or a check fails if a module outside the allowed set reads `entry.text` line by line.
- [ ] `ci_surface.py` and `config_role.py` no longer carry private copies of `_text_lines`.
- [ ] Every fixture's JSON report is byte-identical to the current output.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/rules.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) (`apply_patterns`, `cap_findings`, `line_matches`)
- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (`_text_lines`, `_searchable`)
- [`src/airlock/detectors/config_role.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/config_role.py) (`_text_lines`)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
