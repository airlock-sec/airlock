---
slug: json-report-has-no-published-contract
title: The JSON report is a consumer-facing artifact with no schema, no version field and no compatibility promise
labels: enhancement, complexity: medium, area: engine
roadmap: 2.9, 5.2
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `report/jsonout.py` is 50 lines and its key set is already stable in practice: `finding_to_dict` and `to_dict` are the whole contract, so documenting and versioning it needs no other change.

## Problem

The JSON reporter is described in its own docstring as the output "a consumer can diff one run against the next without reading a log" (`src/airlock/report/jsonout.py:1-9`), and two other reporters point at it as the complete record: the annotation reporter's withheld note and its suppression note both tell a reviewer that the JSON lists what they could not (issue 28 in this batch is about that promise). `README.md` and `SUPPORT.md` name it as the machine output.

It has no version of its own. `to_dict` emits `tool_version` from the report, so a consumer can tell which build produced a file but not whether the keys mean the same thing as last release: `severity` is written as `finding.severity.label`, a string whose spelling is a `model.Severity` choice, and `roles` is a list whose vocabulary is whatever `rules/roles.toml` declares. A rename of a role or a label is a silent breaking change for anything parsing the file, and there is no test that would notice one being made.

5.2 is the usage-docs task, and a machine output used by callers needs the same treatment the rule reference gets.

## What to build

1. **Add a schema version.** A `schema_version` field with its own constant, separate from `tool_version`, incremented only on a change that breaks a reader, and a note in `ARCHITECTURE.md` 6.6 saying which field a consumer should key on.
2. **Publish the key set.** A documented table of every key, its type, whether it can be null, and where its value space is defined (`Severity.label`, `Mode.value`, the skip reason constants in `collector.py`, the rule ids and `STATE_RULE_IDS`). The generated site already has a place for this and `scripts/build_site.py` is the generator to extend.
3. **Freeze it in a test.** A test asserting the exact top-level key set and the exact finding key set, so an accidental addition or rename fails rather than shipping; and a test that severities and modes are written as their published strings rather than as `label` happening to be stable.
4. **State the nullability rules.** `evidence` is documented as "string or null" in the docstring; `line`, `sha256` and `base` are other nullable fields a reader has to guess about today. Say which keys can be absent, not just null.
5. **Decide the compatibility promise.** Either the schema is stable within a major version, or the file says it is not. Both are honest; an undeclared contract is not.

**Out of scope:** SARIF (26 in this batch), any change to what the JSON contains, and golden-file tests for the reporters as a general practice.

## Acceptance criteria

- [ ] The JSON document carries a `schema_version` distinct from `tool_version`, and the rule for bumping it is written down.
- [ ] Every key is documented with its type, nullability and value space, generated or hand-checked against `to_dict`.
- [ ] A test fails if a key is added, renamed or removed without the schema version and the documentation moving with it.
- [ ] `README.md`, `SUPPORT.md` and the site name the versioned contract rather than the format informally.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/report/jsonout.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/jsonout.py)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`Severity.label`, `Mode`, `STATE_RULE_IDS`, the `Finding` fields)
- [`scripts/build_site.py`](https://github.com/airlock-sec/airlock/blob/main/scripts/build_site.py) (the generator that already derives counts from data)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
