---
date: 2026-10-28 11:15 UTC
tasks: 5.7, 10, 3
summary: An installed wheel can scan.
---

An installed wheel can scan. `pyproject.toml` put only `src/airlock` in the wheel and
`cli.py` resolved its rule paths from `parents[2]`, so the two disagreed the moment the
tool was installed rather than checked out: `airlock scan` from a clean virtualenv
printed `cannot read .../rules/roles.toml` and exited 2 (measured earlier the same day,
which is what opened this row). The fix is the packaging plus one function: the wheel
target force-includes `rules` at `airlock/rules`, and `cli.rules_root(package_dir)`
prefers that copy and falls back to `rules/` two levels above the package, which is the
source checkout and the `$GITHUB_ACTION_PATH` layout the Action snippet already uses.
Choosing the packaged copy first is the part with a reason behind it: an installed
scanner reading a `rules/` directory from whatever checkout shares the filesystem is a
policy source the operator did not pin, and the fallback only applies when there is no
copy inside the package at all. It fails closed either way, which is why this was a P1
packaging gap and not a silent one. Proven by building and installing rather than by
reading the config: `uv build`, a fresh `uv venv`, the wheel lists
`airlock/rules/roles.toml` and both files under `airlock/rules/builtin/`, and a scan of
a scratch repository with an `eval(Buffer.from(...))` build config reports
`cfg-dynamic-code` and `cfg-appended-tail` at HIGH and exits 1. The suite carries a test
that reads `pyproject.toml` and asserts the force-include mapping, because dropping the
data is a packaging fact the suite can check without a build, and two tests that put
`rules_root` against a packaged and a checkout-shaped temporary directory.
`ARCHITECTURE.md` 10, `ARCHITECTURE_ESSENTIALS.md` 3 and `project_structure.md` follow.
Phase 5 moves to 1 of 7 and the readiness total to 29 of 89. Verified: `pytest` 465
passed (4 new), `ruff check` and `ruff format --check` clean on 43 files, `mypy src`
clean on 24 files, self-scan exit 0. Not verified: `pip install airlock` from an index,
since nothing is published (5.3, 5.5), and the `python3 -I` Action snippet run against
an installed copy, which is 0.8 and 4.1
