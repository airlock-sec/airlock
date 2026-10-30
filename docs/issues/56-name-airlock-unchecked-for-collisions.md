---
slug: name-airlock-unchecked-for-collisions
title: The distribution name has never been checked against PyPI, existing projects or trademarks, and two roadmap rows wait on the answer
labels: documentation, complexity: trivial, area: docs
roadmap: 0.15, 9.9
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The checks are all lookups against public registries and a read of the risk register this repository already carries, so no build step or code change is involved.

## Problem

`ARCHITECTURE.md` 8 rates R-8 as the name-collision risk and 0.15 asks for it to be rated with evidence: check the PyPI package `airlock`, existing GitHub projects, and security vendors with a similar name. 9.9 asks for a PyPI distribution with trusted publishing and notes in its own row that the name may be taken. Neither row can be closed without the lookup, and G9 (no risk item rated High without a mitigation or an accepted decision) stays open because R-8 has no evidence attached.

The cost of not knowing is concrete rather than hypothetical: a published wheel under a name another project already uses is a supply-chain incident about this tool, which is the one thing the tool exists to prevent. The decision also shapes 5.3's release workflow and whatever the documentation site calls the project.

## What to build

1. **Do the lookups and record them**: the PyPI name, the GitHub search for security tooling with the name, package indexes other than PyPI if the project will ever publish there, and a trademark search stated as "checked, no professional opinion sought" rather than as clearance.
2. **Rate R-8 with the evidence**, in `ARCHITECTURE.md` 8, and state the mitigation the rating implies: a qualified distribution name, a different package name than the CLI, or an accepted risk with the reason.
3. **Decide about 9.9.** If the PyPI name is taken, the row needs its replacement (for instance a scoped distribution name) recorded in the same place, not an open question in a roadmap.
4. **Say what was not checked.** A name search on one day is a snapshot; the note belongs next to the rating so a later reader does not treat it as clearance.

**Out of scope:** Publishing anything, renaming the repository, and any legal opinion; this issue produces a recorded lookup and a rating, not a decision requiring counsel.

## Acceptance criteria

- [ ] The PyPI name, GitHub projects and security-vendor names are checked, with what was searched and when written down.
- [ ] `ARCHITECTURE.md` 8 rates R-8 with the evidence attached, and G9's status reflects it.
- [ ] `ROADMAP.md` 0.15 is ticked with the findings, and 9.9 either names the distribution strategy or records that it is blocked on the lookup's outcome.
- [ ] The note states that a snapshot search is not clearance.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`ARCHITECTURE.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE.md) (section 8, R-8)
- [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) (0.15, 9.9, G9)
- [`pyproject.toml`](https://github.com/airlock-sec/airlock/blob/main/pyproject.toml) (the distribution name the decision lands on)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
