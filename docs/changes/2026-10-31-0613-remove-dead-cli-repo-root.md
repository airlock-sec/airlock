---
date: 2026-10-31 06:13 UTC
tasks: 7.16
summary: Close #63 (task 7.16): delete the dead `cli.REPO_ROOT` and record what reads every other module-level name in `cli.py`.
---

Close #63 (task 7.16). `cli.py` defined `REPO_ROOT = Path(__file__).resolve().parents[2]` with a
docstring tying it to `$GITHUB_ACTION_PATH`, but 5.7 replaced the resolution logic it came from
with `rules_root(package_dir)` and never deleted the constant. `git grep -n REPO_ROOT` across the
tracked tree found only its own definition at `src/airlock/cli.py:66` and four test files that
compute their own copy of the same expression for the repository holding the tests
(`tests/fixtures/__init__.py`, `tests/unit/test_build_site.py`, `tests/unit/test_builtin_patterns.py`,
`tests/unit/test_ci_surface.py`, `tests/unit/test_config_role.py`, `tests/unit/test_redos.py`,
`tests/unit/test_roadmap_gate.py`, `tests/unit/test_rule_data.py`, `tests/unit/test_rule_reference.py`,
`tests/unit/test_runner.py`, `tests/unit/test_site.py`, `tests/unit/test_wasm_manifest.py` and
`tests/unit/test_policy.py` all define their own module-level `REPO_ROOT`, independent of `cli.py`).
The one exception was `tests/unit/test_cli.py`, which imported `REPO_ROOT` from `airlock.cli` for a
single assertion (`test_the_built_distribution_carries_the_rule_data`, reading `pyproject.toml`).
That import is now gone; the test file defines its own `REPO_ROOT` the same way the others do.

Deleted the constant and its docstring from `src/airlock/cli.py`. Nothing else changed in `rules_root`
or its tests (`test_an_installed_package_resolves_its_own_copy_of_the_rule_data`,
`test_a_source_checkout_resolves_the_repository_root`,
`test_a_package_with_no_rule_data_anywhere_does_not_resolve_invisibly`): both install layouts keep
exactly the behavior 5.7 tested.

Per the issue, swept every other module-level name in `cli.py` the same way (`git grep -n` for each,
confirming at least one read outside its own definition):

- `RULES_ROOT` (`cli.py:80`): read at `cli.py:81-82` to build `DEFAULT_RULES_DIR` and
  `DEFAULT_ROLES_FILE`. Not imported elsewhere.
- `DEFAULT_RULES_DIR` (`cli.py:81`): read as the `--rules-dir` default on both the `scan` and
  `manifest check` subparsers (`cli.py:127,161`) and as the `rules_dir` default in the `scan()`
  pipeline function (`cli.py:216`); imported by `tests/unit/test_cli.py`.
- `DEFAULT_ROLES_FILE` (`cli.py:82`): read as the `--roles` default on the same two subparsers
  (`cli.py:128,162`) and as the `roles_file` default in `scan()` (`cli.py:217`); imported by
  `tests/unit/test_cli.py`.
- `EVENT_MODES` (`cli.py:86`): read in the `--event` help text (`cli.py:116`) and in the mode
  resolution that maps a github event name to a trust model (`cli.py:171,175`).
- `RENDERERS` (`cli.py:93`): read as the `--format` choices on both subparsers (`cli.py:129,163`)
  and to look up the renderer for the chosen format (`cli.py:356`).
- `STEP_SUMMARY_ENV` (`cli.py:99`): read once, to find the step-summary file path from the
  environment (`cli.py:376`).
- `WASM_RULE_PREFIX` (`cli.py:104`): read once, to filter `manifest check` findings down to the
  `wasm-*` family (`cli.py:349`).

All seven are read somewhere; `REPO_ROOT` was the only dead one.

`ARCHITECTURE.md` 10 already describes the Action's launch path through `cli.rules_root`
(`"cli.rules_root prefers that copy, falling back to rules/ two levels above the package directory,
which is the checkout layout $GITHUB_ACTION_PATH uses"`) and never mentions `REPO_ROOT`, so it needed
no wording fix. `AGENTS.md` describes the Action path in terms of `$GITHUB_ACTION_PATH` and does not
name `REPO_ROOT` either, so it is also unchanged.

Added `TestNoDeadModuleNames::test_repo_root_was_removed_as_dead_code` to `tests/unit/test_cli.py`,
asserting `not hasattr(cli, "REPO_ROOT")`. Confirmed it fails against the pre-fix module (with only
the `src/airlock/cli.py` change reverted) and passes with the fix.

Verified: `python -m pytest` 838 passed, 2 skipped; `ruff check .` and `ruff format --check .`
clean; `mypy src` clean; `airlock scan --mode full .` reports no HIGH findings.
