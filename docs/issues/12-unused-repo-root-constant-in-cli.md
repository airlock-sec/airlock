---
slug: unused-repo-root-constant-in-cli
title: `cli.REPO_ROOT` is dead code next to the path resolution that replaced it
labels: bug, good first issue, complexity: trivial, area: engine
roadmap: 2.10
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** 5.7 introduced `rules_root` as the function that resolves the two install layouts, which is what made the module constant redundant; nothing else reads it.

## Problem

[`cli.py:66`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) defines:

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
```

with a docstring tying it to `$GITHUB_ACTION_PATH`. `git grep REPO_ROOT` across the tracked tree finds
this definition and nothing that reads it: the callers in the same module use `RULES_ROOT`,
`DEFAULT_RULES_DIR` and `DEFAULT_ROLES_FILE`, and the four test files that define their own `REPO_ROOT`
compute it themselves for the repository holding the tests.

It survived because 5.7 replaced the resolution logic it came from rather than deleting it, and because
`parents[2]` is exactly the kind of expression that reads as meaningful to a reviewer who knows the
checkout layout. A future reader has to work out whether it is a fallback, a documented constant, or an
input to the Action contract, and the answer is none of those.

`ARCHITECTURE.md` 10 keeps the `python3 -I -c` launch sketch and `AGENTS.md` describes the Action path,
so the one place a dead constant is worst is the module that explains how the tool finds its own rule
data.

## What to build

1. **Delete it**, or **use it** if the right reading is that `rules_root` should take the checkout root
   as an argument for the Action case. Pick one; do not leave a constant with a docstring that describes
   a role no code plays.
2. **Check the other module-level names in `cli.py`** the same way (`RULES_ROOT`, `STEP_SUMMARY_ENV`,
   `WASM_RULE_PREFIX`, `EVENT_MODES`, `RENDERERS`) and list in the record what each is read by, so the
   next reader does not repeat this sweep.
3. **Keep `rules_root`'s two-layout behaviour exactly as 5.7 tested it**; the wheel case and the checkout
   case each have tests and this issue must not disturb either.

**Out of scope:** moving default resolution out of `cli.py`, changing the Action's launch path, and any
touch to `pyproject.toml` packaging.

## Acceptance criteria

- [ ] `cli.py` contains no module-level name that nothing reads, verified by a grep recorded in the change record rather than by eye.
- [ ] The rule-data resolution tests for the wheel layout and the checkout layout still pass, unchanged.
- [ ] `ARCHITECTURE.md` 10 and `AGENTS.md` still describe the Action path correctly, and the record says whether either needed a wording fix.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`REPO_ROOT`, `rules_root`, `RULES_ROOT`).
- Tests: [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py) covers both install layouts.
- The suite already fails on a rule id or state id that docs and code disagree about, so a same-shaped sweep for constants is in keeping with how this repo checks itself.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
