---
slug: codeowners-misses-the-trust-model-modules
title: `.github/CODEOWNERS` protects the rules and the collectors and leaves the fingerprint, model and reporter layers open
labels: documentation, complexity: trivial, area: ci
roadmap: 1.3
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The file exists, works and is self-owning (`/.github/CODEOWNERS @Gabbydunkk`), so this is adding path lines to a mechanism that is already enforcing review on the paths it names.

## Problem

`AGENTS.md` 12 says changes to protected paths need owner review, and CODEOWNERS names the scripts directory, the rules, the detectors, `policy.py`, `collector.py`, `runner.py`, both trusted files, the workflows and `pyproject.toml`, with the header comment giving the rule: these paths "carry the trust model, the detection logic and the gates, so a small edit there can disable a check".

Four of the modules that carry the same property are not listed:

- `src/airlock/fingerprint.py`. Its `truncate_evidence` runs before the evidence is hashed (lines 37-44), which is why a fingerprint is a prefix comparison; a one-constant edit there changes what every existing suppression matches.
- `src/airlock/model.py`. `STATE_RULE_IDS` (lines 45-66) is the set that makes findings non-suppressible (2.15), and `Severity`, `Mode` and `EXIT_*` constants are the exit-code contract.
- `src/airlock/roles.py`. `SENSITIVE_ROLES` decides when an unreadable file is a HIGH rather than a WARN, and `resolve_roles` is the coverage claim every rule depends on.
- `src/airlock/report/` and `src/airlock/cli.py`. The reporters are the escaping boundary (B11) and the CLI is where `run_scan` decides which policy was trusted (2.7).

## What to build

1. **Add the four paths** with a comment each saying the property the module holds, in the voice the existing lines use, rather than leaving the list to be remembered.
2. **Check the ordering rule.** The header notes that later rules win, so the additions have to sit where they do not silently narrow an existing line; `src/airlock/policy.py` and `src/airlock/detectors/` are already owned at a finer granularity than the directory would be.
3. **Decide about `tests/`.** A bypass regression is a security assertion in the same sense as a rule; say whether it belongs under owner review and give the reason either way.
4. **Confirm enforcement, not just the file.** The ruleset that makes CODEOWNERS meaningful is 1.3's other half and is configured separately (51 in this batch); record which part this change proves and leave the rest named rather than implied.

**Out of scope:** Configuring branch protection or required reviews, which the separate governance issue owns, and any change to who the owners are.

## Acceptance criteria

- [ ] `fingerprint.py`, `model.py`, `roles.py`, `report/` and `cli.py` are covered by CODEOWNERS lines.
- [ ] Each added line carries a one-sentence reason naming the property the path protects.
- [ ] A read of the file shows no path that was owned becoming unowned through the ordering rule.
- [ ] 1.3's status in `ROADMAP.md` says which half of it this change settled.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`.github/CODEOWNERS`](https://github.com/airlock-sec/airlock/blob/main/.github/CODEOWNERS)
- [`src/airlock/fingerprint.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/fingerprint.py), [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py), [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py)
- [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) (section 12)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
