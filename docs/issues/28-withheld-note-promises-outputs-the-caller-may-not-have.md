---
slug: withheld-note-promises-outputs-the-caller-may-not-have
title: The annotation reporter's truncation note tells a reviewer to read a step summary and a JSON report that the run may not have produced
labels: bug, complexity: trivial, area: engine
roadmap: 2.9, 7.13
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The note is one f-string in `report/github.py:70-78`, the CLI already knows which reporter was asked for, and `_write_step_summary` in `cli.py:332-357` is the place that decides whether a summary exists, so the fix is a conditional and a test.

## Problem

When a cap bites, `github._withheld_note` writes: "the step summary and JSON output list them all" (`src/airlock/report/github.py:70-78`). The suppression note two paragraphs later makes the same promise.

Neither is necessarily true of the run the reviewer is reading. `--format` takes one renderer (`cli.py:133`, `RENDERERS` at line 97), so a workflow that runs `airlock scan --format github` produces annotations and nothing else; the step summary only exists if the caller separately wrote a `--format summary` render to `$GITHUB_STEP_SUMMARY`, which `_write_step_summary` does only when that environment variable is set. And the JSON output exists only if a run with `--format json` was asked for and its destination was kept.

So the note that exists to prevent a capped list from looking complete points at documents that may not be there, which is the one failure mode B8 was written against. A reviewer who cannot find the promised output concludes the scan found what the annotation said it found.

## What to build

1. **Make the note say what is true, or make it always true.** Two ways: pass the reporter the facts it is allowed to claim (which other outputs this run produced, and where), or change the wording to name the command that produces the full list (`airlock scan --format json`). The second needs no plumbing and is the recommendation; the first is better if the CLI grows multi-format output.
2. **Keep the count.** The number of withheld findings is the part that matters; do not let the rewrite lose it or round it.
3. **Say the same thing in both notes.** The suppression note promises the JSON output names each hidden finding and its reason. If that becomes a command rather than a document, both notes change together, and a test asserts they use the same sentence.
4. **Check the cap arithmetic still adds.** `INFO_ANNOTATIONS` is `ANNOTATIONS_PER_LEVEL - 2` precisely so that the withheld note and the suppression note both fit; a wording change must not turn one of them into two annotations.

**Out of scope:** Multi-format output (running two reporters from one command), the annotation cap values themselves, and the step summary's own budget, which 27 in this batch covers.

## Acceptance criteria

- [ ] Neither note claims a document exists unless the run produced it, or both name the command that lists what was withheld.
- [ ] A test renders a capped report both with and without a step summary and asserts the differing or matching wording.
- [ ] The withheld count survives in every variant of the note, and the INFO budget still leaves room for both notes.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/report/github.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/github.py) (`_withheld_note`, `render`, the three cap constants)
- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_emit`, `_write_step_summary`)
- [`tests/unit/test_report.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_report.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
