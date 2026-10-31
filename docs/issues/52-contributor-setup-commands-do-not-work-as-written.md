---
slug: contributor-setup-commands-do-not-work-as-written
title: The documented way to install the dev tools and the documented command forms both fail on a current machine
labels: documentation, good first issue, complexity: medium, area: engine
roadmap: 5.1, G7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The tools are pinned in `pyproject.toml`'s dev extra and the gates are listed in `AGENTS.md` 5, so this is a documentation change verified by following it once on a clean machine rather than any code work.

## Problem

Two documented forms do not survive contact with a current Debian or Ubuntu python.

- **The tool install.** `CONTRIBUTING.md` and `SUPPORT.md` tell a contributor to have ruff and mypy available. `pip install --user` on that base is refused under PEP 668 (externally managed environment), and creating a venv needs `python3-venv` from apt rather than being present. The path that works is `uv tool install ruff` and `uv tool install mypy`, or one `pipx` equivalent, and no document says so. A contributor meets this in the first minute, which is the opposite of 5.1's `Done when`: a new user can install in under five minutes.
- **The command names.** Several documents write `python -m pytest`, `python roadmap_progress.py` and `python -m airlock scan`. On that same base, `python` does not exist; the interpreter is `python3`. Worse, `AGENTS.md:64` prescribes `python -m airlock scan --mode full` while `SUPPORT.md:49` and `ci.yml:53` run the installed `airlock scan --mode full .`, and the comment at `ci.yml:49-51` explains that the module form would miss a wheel that shipped without its rule data. Two documents give different required commands, and the one that is authoritative for CI is not the one in the contributor rules.

## What to build

1. **Write the setup that works.** Name `uv tool install` (or `pipx`) for ruff and mypy, or add a one-command bootstrap script under `scripts/` that the gates themselves run; state which and keep `pyproject.toml`'s dev extra as the source of the pins.
2. **Make `python3` the documented form everywhere**, including `AGENTS.md` 5, and settle the self-scan command to the one CI runs, with the wheel-and-rule-data reason attached to it so the choice does not read as a style preference.
3. **Prove it.** The acceptance test is a clean container, following only the documents, reaching green gates without improvising, and the record names the image and the interpreter versions used.
4. **Keep PATH honest.** The tools land in a directory a fresh shell may not have on its path; either document the export line or have the bootstrap script say what it did.

**Out of scope:** Adding a lockfile or a dependency manager to the project itself, which is a supply-chain decision rather than a documentation one, and any change to what the gates check.

## Acceptance criteria

- [ ] Every documented command runs on a machine where `python` does not exist.
- [ ] `AGENTS.md` 5, `SUPPORT.md`, `CONTRIBUTING.md` and `ci.yml` name the same self-scan command.
- [ ] The dev-tool install path is written down and works on a PEP 668 base.
- [ ] A clean-container run of the documented steps reaches green gates, with the image and versions recorded in the change record.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`CONTRIBUTING.md`](https://github.com/airlock-sec/airlock/blob/main/CONTRIBUTING.md), [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md) and [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) (sections 5 and the self-scan line)
- [`pyproject.toml`](https://github.com/airlock-sec/airlock/blob/main/pyproject.toml) (the dev extra)
- [`.github/workflows/ci.yml`](https://github.com/airlock-sec/airlock/blob/main/.github/workflows/ci.yml) (the authoritative command list)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
