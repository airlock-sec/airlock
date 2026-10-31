---
date: 2026-10-31 05:46 UTC
tasks: 1.6
summary: Accept Dependabot's grouped bump of pytest, ruff and mypy in the dev dependency group, with the CI suite unchanged.
---

Dependabot opened the first grouped `pip` pull request, `pytest>=9.2.0`, `ruff>=0.17.3` and
`mypy>=2.4.0`, all inside the `dev` group in `pyproject.toml`. The runtime dependency list is
still empty and no package is added, so AGENTS.md 4 is unaffected.

`ci.yml` installs `pytest`, `ruff` and `mypy` by name at the latest versions, so this bump changes
the declared floor rather than the version CI runs. The pull request's own `checks` job passed the
suite with those tools and failed only the roadmap gate, which a bot cannot satisfy on its own;
this record is the part it was missing. `python scripts/roadmap_progress.py` regenerated the
changelog and `Last updated` from it.

Task 1.6 is already done. It is cited here because it is the task that configures this bot, and
the changelog row records the first update it produced.
