---
slug: docs-describe-behaviour-the-code-does-not-have
title: A named rule, a policy key and a suppression expiry window exist only in the prose
labels: bug, documentation, complexity: medium, area: engine
roadmap: G7, 8.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** Every instance is a documented claim that can be checked against a shipped constant, and the documents and the code are both in this repository, so the work is a comparison plus an edit to the prose rather than a feature.

## Problem

G7 asks that the documents agree with the code. Four claims currently do not, and each is a caller-facing promise:

- **A rule that does not exist.** `ARCHITECTURE_ESSENTIALS.md:79`, `ARCHITECTURE.md:460` and `PRD.md:176` name `cfg-nul`. No rule file declares it; the collector emits `nul-in-text` (`src/airlock/collector.py:375`). A reviewer who greps for the documented id concludes the control is missing.
- **A policy key with no loader.** `ARCHITECTURE.md:115` says policy may list `low_priority_dirs`. It is not in `model.POLICY_SETTINGS_KEYS` (lines 28-30), so a repository that follows the document gets a `policy-unknown-key` finding on every scan (2.1's refusal to ignore a key it does not know is the correct behaviour, and the document is the thing that is wrong).
- **A base-scoped `pr` mode that is not implemented.** `PRD.md:133` (FR-01) describes `pr` as HIGH findings over the whole tree with WARN only on changed files. `ScanContext` carries rules, entries, policy and mode (`model.py:391-404`), and `cli.run_scan` never passes a base to the detectors, so no rule is scoped to a diff.
- **An expiry window that is a warning, not a limit.** `README.md:150-151` says suppressions expire within 30 days at the latest. `SUPPRESSION_EXPIRY_DAYS = 30` (`model.py:37`) drives `suppression-expiring`, a warning that an entry is near its date; `expires` is optional and unbounded in the loader (`policy.py:478-491`), so an entry without a date never expires and one dated next year is valid.

## What to build

1. **Decide per claim: implement, or remove the promise.** For `cfg-nul`, rename the prose to `nul-in-text` and say that the emitter is the collector rather than a rule file. For `low_priority_dirs`, delete the sentence, since `AGENTS.md` 4 forbids default directory skips and a policy key that enables them is a claim to remove rather than build. For FR-01, either scope the `pr` detectors to the diff or rewrite the requirement to what the build does; the second is the smaller change and the first is the better product, and the record has to say which was chosen. For the expiry text, state the truth: an entry without `expires` stays, and 30 days is when the scanner starts complaining.
2. **Sweep for the class, not the four.** Grep every document for rule ids, policy key names, severity constants and exit codes, and check each against `src/`, `rules/` and `model.py`. Report the count of claims checked and the list that failed, which is the form `ROADMAP.md` rows use elsewhere.
3. **Note the sibling problem rather than fixing it here.** Several documents also carry counts that drift (rules, tests, readiness percentage); those are generated or verified elsewhere in this batch, and duplicating that work here would produce two records for one change.

**Out of scope:** Implementing base-scoped `pr` detection as a feature (which needs its own design of which rules scope and which do not), and any change to policy key semantics.

## Acceptance criteria

- [ ] Every rule id named in a document exists in a rule file or in `STATE_RULE_IDS`, with the check performed across the document set and the count recorded.
- [ ] Every policy key named in a document is in `POLICY_SETTINGS_KEYS`, or the sentence is gone.
- [ ] `PRD.md` FR-01 and `README.md`'s expiry sentence describe what this build does.
- [ ] G7's status in `ROADMAP.md` names the four decisions rather than claiming the document set is broadly accurate.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`ARCHITECTURE.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE.md), [`ARCHITECTURE_ESSENTIALS.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE_ESSENTIALS.md) and [`PRD.md`](https://github.com/airlock-sec/airlock/blob/main/PRD.md)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`POLICY_SETTINGS_KEYS`, `SUPPRESSION_EXPIRY_DAYS`, `ScanContext`)
- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_unknown_keys`, the suppression date parsing)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
