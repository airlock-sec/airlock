---
slug: the-published-issue-bodies-describe-work-that-has-since-landed
title: The `docs/wave/issues/` set still states fixed conditions as present, and the files are the record of what was asked
labels: documentation, complexity: medium, area: docs
roadmap: G7, 1.14
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The fifteen files are checked in and every one was published and closed as an issue (#20 to #34), so each body can be compared against the current tree and corrected in the same commit that records what changed.

## Problem

1.14 made `docs/wave/issues/` the source of the published batch, and the batch was the repository's claim about what was broken. Twelve of those claims are now false in the present tense, because the work landed:

- `02:18-19` describes annotation caps of 50, 25 and 10 as "deliberately conservative guesses". 0.9 measured ten per level and `report/github.py:26-32` implements 9, 9 and 8.
- `08:14-21` says a gitlink "yields one `submodule-present` finding at INFO" with no URL cross-check. 7.2 added the `.gitmodules` cross-check both ways plus `policy.submodules`, and `collector._submodule_findings` emits HIGH and WARN.
- `13:14-17` says nothing in the shipped rule set reads a GitHub workflow file. `rules/roles.toml` declares `workflow`, `ci_surface` is registered, and six rules read it.
- `14:18-19` says `tests/bypass/` is an empty directory with a `.gitkeep`. It holds seven modules and a `conftest.py`.
- `15:15` describes a suite of 475 tests; collection reports 796.
- `12` still calls the state-rule suppression defect live, and 2.15 closed it with `STATE_RULE_IDS` now holding 18 ids rather than the sixteen the file counts.
- `06:32` says phase 7 reads 0 of 12; the generated table reads 5 of 13.

The published issues are closed and read as history. The files are read as current: a contributor who greps `docs/wave/issues/` for what to work on gets a list of defects that no longer exist, and a reviewer checking a claim against `main` finds the opposite. 1.14's `Done when` required that every issue cite a file that exists; the files still exist and now say different things.

## What to build

1. **Annotate rather than rewrite.** Each file's Problem section describes a state of `main` at 2026-10-28. Add a short closing note per file naming the task or issue that landed the change, keeping the original text intact, so the directory remains the record of what was asked. Do not renumber, delete or reorder.
2. **Say which bodies need a correction comment** on the GitHub issue. Several closed issues were merged from pull requests whose descriptions are the corrected text; list which issue numbers carry a false present-tense claim so the owner can decide, and do not post anything as part of this change.
3. **Point the batch forward.** Each note should link the roadmap row that closed it, so the directory becomes a way to read what the phase did rather than a list of open work.
4. **Check the remaining files** for the same class: `docs/wave/settings.md` and `docs/wave/application.md` carry counts and percentages with the same staleness problem, which the hand-maintained-counts issue owns; leave those to it and say so.

**Out of scope:** Re-opening or editing the published GitHub issues, the counts in `README.md` and the wave documents, and any change to what the batch was originally asking for.

## Acceptance criteria

- [ ] Every file under `docs/wave/issues/` whose Problem section describes a since-fixed condition carries a note naming what fixed it.
- [ ] The original text of each file survives the change, with the note added rather than substituted.
- [ ] A list of the published issue numbers whose GitHub body still asserts a false present tense exists in the change record, without anything being posted.
- [ ] `ROADMAP.md` 1.14's row and the notes agree on which batch items were closed by which tasks.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`docs/wave/issues/`](https://github.com/airlock-sec/airlock/blob/main/docs/wave/issues) (all fifteen files)
- [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) (1.14, and the rows the notes cite)
- [`scripts/create_wave_issues.sh`](https://github.com/airlock-sec/airlock/blob/main/scripts/create_wave_issues.sh) (how the batch was published, and the cross-reference resolution it performed)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
