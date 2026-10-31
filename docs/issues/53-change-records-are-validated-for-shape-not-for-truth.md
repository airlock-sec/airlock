---
slug: change-records-are-validated-for-shape-not-for-truth
title: `roadmap_progress.py` refuses a badly formed record and accepts one naming a task that does not exist
labels: enhancement, complexity: medium, area: engine
roadmap: 1.15, 1.9
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The generator already validates twelve shape conditions and already reads the task lines to build the progress table (`scripts/roadmap_progress.py`), so checking a record's `tasks:` field against the set it already parses is a few lines in the validator that exists.

## Problem

1.15 made the changelog generated: one record per change under `docs/changes/`, with `date:`, `tasks:` and `summary:` front matter, and the generator refuses a record whose name disagrees with its date, whose summary is empty, over-long or carries a bare pipe, whose task cell is empty, whose front matter key is unknown or duplicated, or whose markers are out of order. That is shape.

Nothing checks truth against the roadmap. A record whose `tasks:` names an id that is not a row in `ROADMAP.md` renders a row linking to a task that does not exist, which is the same class of drift 1.14 caught by hand for the issue batch: "every roadmap row it claims to cover is real, checked by grepping this file rather than by trusting the front matter". The generator parses the task lines for the progress table already, so the information needed to check is in the same run.

There is a second, softer question in the same directory: a record is the repository's statement of what changed, and 1.15's gate refuses *deleting* one that was on the base, but nothing refuses *editing* a merged record's `summary:` or `tasks:`. Whether history is meant to be immutable in this directory is a decision the documents should state, not one left to whoever edits a file next.

## What to build

1. **Validate the ids.** A record naming an unknown task id fails the generator with the id and the file named, using the task set the progress table already parses. Decide whether gate ids (`G1` to `G10`) are acceptable values, and say so in the error message.
2. **Decide about edits to a merged record**, and implement whichever answer you choose: compare against the merge base in the roadmap gate, or state in `CONTRIBUTING.md` that a record is a living document and make the summary's truth the property that matters.
3. **Extend the existing tests**, which cover shape refusal in 33 cases (`tests/unit/test_roadmap_gate.py`), with the new refusals; a validator that is not tested is a validator that will be removed the first time it annoys someone.
4. **Run it against the 38 existing records** and fix or annotate whatever it flags, because a check that fails on the repository's own history is a check that gets loosened.

**Out of scope:** Any change to what a record's fields mean or how section 9 renders, and the roadmap progress percentages, which the generator already derives.

## Acceptance criteria

- [ ] A record naming a task id that is not a row in `ROADMAP.md` makes the generator fail with the id and the file named.
- [ ] The answer to whether a merged record may be edited is stated in a document and enforced or deliberately not enforced.
- [ ] The new refusals have tests alongside the existing shape cases.
- [ ] Every record currently under `docs/changes/` passes the widened check, with whatever it needed fixing recorded.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`scripts/roadmap_progress.py`](https://github.com/airlock-sec/airlock/blob/main/scripts/roadmap_progress.py)
- [`tests/unit/test_roadmap_gate.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_roadmap_gate.py)
- [`scripts/check_roadmap_touched.sh`](https://github.com/airlock-sec/airlock/blob/main/scripts/check_roadmap_touched.sh)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
