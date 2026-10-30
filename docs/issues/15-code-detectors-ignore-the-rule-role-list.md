---
slug: code-detectors-ignore-the-rule-role-list
title: Code detectors dispatch on a hardcoded role, so a rule's declared coverage is a claim the engine does not honour
labels: bug, complexity: medium, area: engine
roadmap: 2.5, 3.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `ci_surface.py` already ships the correct mechanism (`_shares_a_role`, lines 76-83) and the rule loader validates role names against `roles.known_roles`, so the fix is the same six lines in the two detectors that do not use it.

## Problem

A rule's `roles` list is its coverage claim, stated in data so that a reviewer and the generated rule reference can read it. That is the reason issue #30's work put the claim in `rules/builtin/builtin_patterns.toml` instead of in code, and the file's header comment says so in as many words.

`config_role.py:183` decides coverage from a constant:

```python
if TOOLING_CONFIG_ROLE not in entry.roles or entry.text is None:
continue
```

so editing `cfg-network-exec`, `cfg-process-spawn` or `cfg-appended-tail` to claim a second role changes nothing: the detector keeps reading exactly the files whose role list contains `tooling-config`. `wasm_manifest.py` does the same thing through `_require_rule` and its role constants rather than through the entry's roles.

`ci_surface.py:76-83` is the counter-example. `_shares_a_role` intersects `rule.roles` with `entry.roles` and its module docstring gives the reason: a rename in the rule data moves the dispatch with it instead of leaving a detector that quietly finds nothing. The two other detectors have no such guard, and nothing in the suite notices the drift: `tests/unit/test_rule_data.py` checks that a declared role *can* resolve, not that the detector that claims to honour it does.

## What to build

1. **Route both detectors through their rule data.** Use the `_shares_a_role` shape in `config_role.py` and `wasm_manifest.py`, and make each of the family's rules the source of the roles it reads. If a combination rule needs the union of two rules' roles, take the union of the two lists rather than a constant.
2. **Say what a rule with no matching role means.** If `roles` is empty for a code rule, the loader should refuse it rather than let it silently match nothing; check whether `rules.py` already rejects an empty list and add the case if it does not.
3. **Make the drift fail a test.** Add a check that for every `builtin:<name>` rule, the detector's effective file set equals the set implied by `rule.roles` and `rules/roles.toml`. The mechanical way is to build one entry per role and assert the rule fires, which is the same trick `tests/unit/test_builtin_patterns.py` plays.
4. **Keep the constant where it belongs.** The rule id constants (`SPAWN_RULE_ID` and friends) stay: they identify a rule. It is the role gate that has to come from data.

**Out of scope:** Any change to which roles `rules/roles.toml` assigns to filenames, and any new rule. This issue is only the dispatch mechanism, and it must land without changing a single finding on the existing fixtures.

## Acceptance criteria

- [ ] Adding a role to `cfg-network-exec`, `cfg-process-spawn`, `cfg-appended-tail` or a `wasm-*` rule changes which files that rule reads, with no code edit.
- [ ] A test asserts, per code rule, that its declared roles are the roles it dispatches on, so the drift is caught rather than reviewed.
- [ ] Every fixture expectation in `tests/unit/test_config_role.py` and `tests/unit/test_wasm_manifest.py` still holds unchanged.
- [ ] Both detectors' module docstrings say that coverage comes from rule data.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/detectors/config_role.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/config_role.py) (`run`'s role gate)
- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (`_shares_a_role`, the shape to copy)
- [`src/airlock/detectors/wasm_manifest.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/wasm_manifest.py)
- [`tests/unit/test_rule_data.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_rule_data.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
