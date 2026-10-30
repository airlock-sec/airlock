---
slug: sarif-reporter
title: `--format sarif` does not exist, so the one output code-scanning toolchains already speak is missing
labels: enhancement, complexity: high, area: engine
roadmap: 7.6, 5.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The fingerprint that SARIF's partial fingerprints want is settled and locked by a test (2.6, and the settled key `partialFingerprints["airlock/v1"]` is recorded in `src/airlock/report/sarif.py:1`), and the other four reporters show the shape a fifth takes, so nothing has to land before this.

## Problem

`src/airlock/report/sarif.py` is one line: a docstring naming the task and the settled key. `cli.RENDERERS` (line 97) has four entries, so `--format sarif` is an argparse error rather than a stub that lies.

The cost is adoption. A repository that already gates on code scanning results, or an organisation that aggregates them, has to parse either GitHub annotations, which are capped at ten per level per step (`report/github.py:24`), or the JSON report, which is this project's own key set. SARIF 2.1.0 is the format those tools speak, and the fields `airlock` already produces map onto it without invention: `rule_id` to a `reportingDescriptor` id, `severity.label` to `result.level`, `path` and `line` to a `region`, `fingerprint` to `partialFingerprints`, and each rule's rationale and suppressibility to `rules[].fullDescription`.

7.6 also asks for a result cap and golden tests, and 0.9's measurements are the reason the cap is not optional: a SARIF file with tens of thousands of results is refused by the upload action rather than truncated, which is a silent loss of the whole run. The lesson 2.9 learned for annotations (B8: choose the survivors rather than leaving it to the runner) applies here with a different number.

## What to build

1. **Write the reporter against the specification, not against another tool's output.** Emit `runs[].tool.driver` with `name`, `version` from `__version__`, `informationUri`, and a `rules` array built from `ctx`-free rule data, plus `results[]` with one `region` per finding and `partialFingerprints` keyed as settled.
2. **Map severity explicitly.** HIGH to `error`, WARN to `warning`, INFO to `note`, and say in a comment that the mapping is why the exit code is not derived from SARIF consumers.
3. **Cap and account.** Pick a result ceiling, name it beside the annotation caps in `report/github.py`'s style rather than in policy, and when it bites emit the same honesty the annotation reporter does: a `toolNotification` or a `configurationLike` result naming how many results were withheld and where the full list is.
4. **Escape nothing that the format escapes.** Evidence is attacker text (`AGENTS.md` 4, ADR-013); it must survive JSON string encoding, and any `message.text` must not be able to forge a rule id or a URI.
5. **Register it.** Add `sarif` to `RENDERERS`, to `--format` choices for both `scan` and `manifest check`, and to the reporter list in `README.md` and `SUPPORT.md`.
6. **Golden test.** One committed SARIF document rendered from a fixed report, plus a test that the file validates against the SARIF schema the project names, and a truncation case that proves the cap's honesty.

**Out of scope:** Uploading results to GitHub code scanning, which is a caller's workflow and needs permissions this project's usage docs forbid, and any change to the fingerprint algorithm that feeds `partialFingerprints`.

## Acceptance criteria

- [ ] `--format sarif` writes a SARIF 2.1.0 document with one rule per rule id and one result per finding.
- [ ] Severity mapping, the result cap and the withheld-count mechanism are each named in a test.
- [ ] Evidence and paths in the document cannot break out of their JSON string or forge a descriptor, with a fixture that tries.
- [ ] `partialFingerprints` uses the settled `airlock/v1` key and a test refuses a rename.
- [ ] The reporter is registered, documented in `README.md` and `SUPPORT.md`, and covered by a golden file.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/report/sarif.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/sarif.py) and [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`RENDERERS`)
- [`src/airlock/fingerprint.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/fingerprint.py) (`evidence_key`, the fingerprint the key must stay compatible with)
- [`tests/unit/test_report.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_report.py)
- The SARIF 2.1.0 specification, read for the fields actually required

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
