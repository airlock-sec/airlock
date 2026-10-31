---
slug: suppress-verb
title: Writing a suppression is hand-edited TOML, and the CLI that produced the finding can help least
labels: enhancement, complexity: high, area: engine
roadmap: 2.8, 2.10
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** Everything a suppression needs is already on a finding and already printed in the JSON report: `fingerprint`, `file_sha256`, `rule_id`, `path` and `suppressible` (`model.Finding`, `report/jsonout.finding_to_dict`), and the validation that a hand-written entry has to pass exists in `policy._entry_problem`.

## Problem

A suppression entry requires rule id, path, and either a fingerprint or a file hash, plus a reason and an expiry, and `policy.py` rejects an entry that omits a required field (2.8). The workflow today is: read the JSON output, copy four values into `airlock.toml` by hand, and run the scan again to find out whether the entry parsed and matched.

That is the worst possible direction for the file that decides what the scanner stays quiet about. Three failure modes are live. An entry with a mistyped fingerprint parses and suppresses nothing, so the maintainer thinks the finding is explained and it is not. An entry against a non-suppressible rule (one of the 18 in `model.STATE_RULE_IDS`, or a rule with `suppressible = false` such as `cfg-dynamic-code`) is rejected with a message the maintainer reads only after the edit. And the truncated-evidence fingerprint behaviour in `fingerprint.py:37-44` means an entry written from a *displayed* value can match more findings than intended, which is a question a verb can answer and a hand edit cannot.

2.8 built suppression application and `cli._manifest_add` shows the project already ships a command that edits a trusted file through the hand-written writer.

## What to build

1. **Add `airlock suppress` reading a JSON report.** Take the report on stdin or by path, select a finding by rule id and path (refusing an ambiguous selection, and listing the candidates when it happens), and append the entry with the reason and expiry supplied as flags.
2. **Validate before writing.** Run the candidate entry through the same `policy._entry_problem` the loader uses, and refuse to write an entry that the scanner would reject, so the feedback loop closes before the file changes.
3. **Answer the blast radius question.** Before writing, report how many findings in the report the entry would suppress. An entry that silences eight findings because two lines share a truncated-evidence fingerprint is the mistake this verb exists to prevent, and the number costs nothing to compute at the point the report is already in hand.
4. **Write to the right file and nowhere else.** The policy path is `--config`-resolved and repo-relative (`require_repo_path` in `model.py:119-123`); the verb must not create a second policy location, and must refuse to edit a policy whose trusted base the run did not read.
5. **Say plainly what it cannot do.** A suppression is reviewed content: the entry the verb writes is authored by the person running it, and the scanner's own rule that the working tree is untrusted (`untrusted-policy-source`) still applies to it in `pr` mode. The command's help text and the docs must carry that sentence.

**Out of scope:** Any change to suppression semantics, expiry windows, or which rules are suppressible, and the fingerprint truncation behaviour itself. This verb reads the rules as they are.

## Acceptance criteria

- [ ] `airlock suppress` writes a valid entry from a JSON report and refuses an ambiguous or invalid selection with a message naming the candidates.
- [ ] The verb prints how many findings in that report the entry would suppress.
- [ ] A test proves an entry against a non-suppressible rule is refused before any file is written.
- [ ] The written file reloads through `resolve_policy` with no `suppression-invalid` finding.
- [ ] `README.md` and the usage docs give the verb, and state that a suppression a contributor adds in a pull request is still working-tree content.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_entry_problem`, `Suppression`, the TOML writer)
- [`src/airlock/fingerprint.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/fingerprint.py) (`truncate_evidence`, `evidence_key`)
- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_manifest_add` as the shape, `run_scan` for the report)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
