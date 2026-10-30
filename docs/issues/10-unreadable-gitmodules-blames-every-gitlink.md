---
slug: unreadable-gitmodules-blames-every-gitlink
title: When `.gitmodules` cannot be read, every gitlink is reported as unmapped with a message that says something else
labels: bug, good first issue, complexity: trivial, area: engine
roadmap: 2.2
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The code that produces the message is thirty lines of `_submodule_findings` shipped in 7.2, with a fixture class to extend.

## Problem

[`collector._submodule_findings`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) decides whether `.gitmodules` is usable with:

```python
gitmodules_text = (
    gitmodules_entry.text
    if (
        gitmodules_entry is not None
        and gitmodules_entry.skip_reason is None
        and not gitmodules_has_state_finding
    )
    else None
)
```

`gitmodules_has_state_finding` is set in `collect` from `bool(entry_findings)`, so *any* finding attached
to that entry disables the parse: an unreadable file, an oversize one, a symlink, an unmerged path, a
`nul-in-text` HIGH, a `non-utf8-text` finding, or a `submodule-orphan` WARN that the function itself
emits for a malformed section.

With the text suppressed, every gitlink takes the `len(matches) != 1` branch and reports
`submodule-unmapped` with `has no matching path and url in .gitmodules`. That is a statement about the
file's content which the scanner does not have. The reviewer's next action is to open a `.gitmodules`
that may be perfectly well-formed, and the actual cause (the file is 6 MB, or is a symlink, or has a
NUL) is in a different finding they may not have scrolled to.

The behavior is fail-closed and stays fail-closed: HIGH rather than WARN, and the subtree genuinely is
not scanned. This issue is only about the message and the distinction being accurate.

## What to build

1. **Tell the two cases apart.** When the mapping file is present but unusable, the gitlink finding
   should say so and name the reason id (`skipped-oversize`, `nul-in-text`, and so on) rather than
   claiming no entry matches.
2. **Keep the severity rule** the same way 7.2 set it: an unusable mapping is not a license to downgrade,
   so HIGH stays, and the record should say that explicitly.
3. **Preserve the malformed-section path.** A well-formed gitlink list with one sloppy `.gitmodules`
   section should still produce `submodule-orphan` for the section and a precise message for the gitlink
   it failed to map.
4. **Two tests**, one for an oversize `.gitmodules` and one for a `.gitmodules` whose only finding is a
   NUL, each asserting the reason appears in the gitlink message.

**Out of scope:** adding a new state rule id if one is not needed; if the fix genuinely wants one, the
id has to be added to `STATE_RULE_IDS`, `ARCHITECTURE_ESSENTIALS.md`'s id list and its test, which is a
larger change than this one.

## Acceptance criteria

- [ ] A gitlink whose `.gitmodules` exists but was skipped or flagged produces a finding that names the reason it could not be mapped.
- [ ] The severity for that case is HIGH, and the record states why it was not lowered.
- [ ] `submodule-orphan` behaviour for a malformed section is unchanged, with a test proving it.
- [ ] Both new cases run against real temporary repositories in `TestSubmodules`.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`_submodule_findings`, `collect`, `_state`).
- Tests: [`tests/unit/test_collector.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_collector.py) `TestSubmodules`.
- Keep the reason as a rule id in the message rather than a free-text sentence, so the two findings can be correlated by someone reading JSON.
- Do not pass the whole `Collection` into the function to get there; the existing signature is small on purpose.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
