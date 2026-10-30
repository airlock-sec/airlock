---
slug: step-summary-has-no-byte-budget
title: The step summary lists every HIGH with evidence and has no size limit, while GitHub truncates a step at 1 MiB
labels: bug, complexity: medium, area: engine
roadmap: 7.13, 2.9
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `report/summary.py` already shortens evidence to `SUMMARY_EVIDENCE_CHARS` for exactly this reason and its docstring names the ceiling, and `report/github.py` already ships the pattern of capping with a note that says what was cut, so both halves of the answer exist in the tree.

## Problem

`summary.render()` emits the counts, the skip accounting, and then every HIGH finding with its evidence under it (`src/airlock/report/summary.py:1-13`). The only bound is `SUMMARY_EVIDENCE_CHARS = 200` per finding; nothing bounds the number of findings, and `report/github.py:26-32` was written around the opposite assumption for annotations.

7.13 names the failure: GitHub keeps 1 MiB per step, and a summary that runs past it is cut from the end. The reporter's ordering means the end of the document is the last HIGHs, so a repository with a four-figure HIGH count gets a summary whose counts table says `4127 HIGH` and whose list stops at a few hundred, with nothing on the page saying that the rest were withheld or how to reach them. 0.9 measured the annotation ceiling and wrote it into the design (`ARCHITECTURE.md` 6.6); the summary ceiling is the same class of limit and is not yet respected.

The task's own wording is the acceptance test: a report with enough HIGHs to pass the ceiling still reaches a reviewer and names what it could not show.

## What to build

1. **Budget the document, not the row.** Count bytes as the reporter renders, keep a named ceiling with margin below 1 MiB, and stop adding evidence rows when the budget is gone. A per-finding ceiling is the wrong unit because a fence, a heading and a table row all cost.
2. **Degrade in a stated order.** When the budget runs out, the honest sequence is: drop evidence blocks first, keep every HIGH's path and line, then cap the list itself. Which one you choose has to be written down, because a reviewer who sees 300 of 4127 rows and a note is in a better position than one who sees 4127 paths and no evidence.
3. **Name the rest.** A truncation note in the same document, in the voice of `github._withheld_note`: how many HIGHs are not shown, and where the complete list actually is (which is issue 28's subject, so keep the wording conditional).
4. **Keep the fence discipline.** The fence-length rule in `summary.py`'s docstring is what stops attacker evidence from escaping the block; a budget that cuts mid-fence must close the fence it opened, and a test must prove that a truncated document still has an even fence count.
5. **Test past the budget.** Build a report with enough findings to exceed the ceiling and assert the rendered size, the note, and that every earlier finding's evidence is intact.

**Out of scope:** Changing what the summary shows when there is room, the annotation caps in `report/github.py`, and any attempt to write the summary from outside `$GITHUB_STEP_SUMMARY`.

## Acceptance criteria

- [ ] `summary.render()` has a named byte budget and a test that renders past it.
- [ ] A document truncated at the budget closes every fence it opens and escapes markup outside them.
- [ ] The rendered output names how many HIGHs it could not show.
- [ ] The budget's margin below GitHub's ceiling is recorded with the measurement it came from, in `ARCHITECTURE.md` 6.6.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/report/summary.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/summary.py) (`render`, `SUMMARY_EVIDENCE_CHARS`, the fence logic)
- [`src/airlock/report/github.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/github.py) (`_withheld_note`, the honesty pattern to copy)
- [`scripts/bypass_probe.py`](https://github.com/airlock-sec/airlock/blob/main/scripts/bypass_probe.py) is not the harness for this; the fixture builders in `tests/fixtures/` are

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
