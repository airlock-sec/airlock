---
slug: load-rules-skips-its-cross-checks-when-called-with-defaults
title: `load_rules` quietly skips both of its cross-checks when the caller does not pass the known sets
labels: bug, complexity: trivial, area: engine
roadmap: 2.5, 3.6
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** 2.5 shipped the loader and both cross-checks; this only changes how the function behaves when a caller forgets the arguments, and the tests already build rule sets from temporary directories.

## Problem

[`rules.load_rules`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) takes `known_detectors` and `known_roles`, and both guards are
truthiness tests on those arguments:

```python
if detector_names and rule.detector != "pattern":
    ...
if role_names:
    ...
```

The defaults are `()`. The CLI passes both sets, so production is covered. Any other caller gets a
loader that parses, validates keys, and then skips the two checks that exist to catch the failure mode
the module's own docstring calls out: a rule naming a detector the runner cannot dispatch to, or a typo
in a role name, each of which silences a rule forever while every gate stays green.

Two callers already sit on that path. `scripts/rule_reference.py` does not exist yet on `main`, but the
generated-reference pull request in review calls the loader twice, once with the full registry and once
with `load_rule_file` directly. The test helpers in
[`tests/fixtures/__init__.py`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures/__init__.py) and several unit tests load rule data
for a single file. A fixture-coverage test that loads with defaults would pass a rule whose detector is
a typo, because the check that would catch it was switched off by an empty argument.

Optional validation with an off-by-default setting is the wrong default for a security tool. The two
sets are cheap to require.

## What to build

1. **Make the two sets required**, or make their absence an error rather than a pass. A keyword-only
   argument with no default is the cleanest version, since the loader's own cross-checks are the reason
   it exists.
2. **Do not leave the caller with a silent gap**: if some call site genuinely cannot know the detector
   registry, say which that is in the signature docstring, and give it a name that admits what it
   skips (a separate function, not a defaulted argument).
3. **Audit the call sites** and record each one and what it passes; that list is the evidence the fix is
   complete.
4. **Two tests**: a rule naming `builtin:no_such_detector` and a rule naming a role nothing resolves to,
   each refused when loaded the way a caller would load it.

**Out of scope:** rule-file schema changes, and the generated rule reference, which is its own open
issue.

## Acceptance criteria

- [ ] A caller cannot reach `load_rules` without deciding what the cross-checks compare against, and there is no code path where forgetting the argument disables a check.
- [ ] Every existing call site in `src/`, `scripts/` and `tests/` is listed in the record with what it passes.
- [ ] Tests prove both refusals fire, including one through a path that previously passed.
- [ ] `ARCHITECTURE.md` 6.4 keeps its claim that a typo in a role name is a config error rather than a silenced rule.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/rules.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) (`load_rules`), [`src/airlock/detectors/__init__.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/__init__.py) (`DETECTOR_NAMES`), [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`known_roles`).
- Tests: [`tests/unit/test_rules.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_rules.py) and [`tests/unit/test_fixtures.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_fixtures.py).
- The hard rule behind this is `AGENTS.md` section 4: a rule that cannot fire must not look like a clean scan.
- No new dependency and no runtime introspection of the registry from rule data; the sets stay passed in, which is what keeps the loader testable.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
