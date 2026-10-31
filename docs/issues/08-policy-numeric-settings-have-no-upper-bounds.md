---
slug: policy-numeric-settings-have-no-upper-bounds
title: Policy numbers are checked for positivity only, so one typo removes a limit that exists to bound the scan
labels: bug, complexity: medium, area: engine
roadmap: 2.1, 2.7, 2.12
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `Policy.__post_init__` is shipped and already validates, so the work is a small set of bounds, the finding each refusal produces, and tests for both sides of each bound.

## Problem

[`Policy.__post_init__`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) rejects `max_file_bytes <= 0`, `line_cap <= 0` and
`tail_max_len <= 0`, and it validates that `policy.submodules` entries are non-empty strings without
whitespace. It puts no ceiling on anything.

`line_cap` is the interesting one because it is not a preference, it is the control that keeps the
regex engine away from unbounded input. `AGENTS.md` section 4 states the rule as: a pattern is only ever
applied to a line at or below the cap, and the over-cap case becomes `cfg-long-line` instead of a regex
run. The cap is read from the policy, which is a trusted file, but the trusted file is written by a
human with a text editor, and `line_cap = 200_000_000` is a plausible typo for `20_000`. With it, the
ReDoS harness in [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) keeps measuring at the
default, and the run that reads the typo'd policy has no bound at all. The suite cannot see the
difference, because it tests the patterns, not the policy that a repository ships.

`max_file_bytes` has the same shape from the other side: `collect` reads `size_bytes + 1` into memory at
[`collector.py:336`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py), so a large ceiling is a memory ceiling for the job, and a
5 MB default exists partly so a runner cannot be OOM-killed by one tracked file. `tail_entropy` is
validated not at all, and an entropy threshold below zero or above 8 makes `cfg-appended-tail` fire on
every config file or on none.

None of this is reachable by the scanned repository, which is the point of the trust model. It is
reachable by the person who writes the config, and a tool whose safety constant can be typo'd away with
no message is one that will eventually be typo'd away.

## What to build

1. **Give each numeric setting a documented band**, not a magic ceiling pulled from the air. A useful
   way to choose: the default multiplied by the largest value that still keeps the scan inside the
   runtime budget the harness measures, and a floor that still scans real files.
2. **Refuse outside the band** with the same plain-message path as every other config error, and name
   the accepted range in the message so the fix is obvious from the output.
3. **Decide whether a refusal is a load error or a finding.** `pr` mode reads the base policy, so a
   base policy outside the band needs the fallback treatment `_policy_at_base` already gives a bad
   version. Make the two consistent.
4. **Bound `tail_entropy` to its real range** (it is bits per character over a window, so the honest
   band is 0 to 8) and say what an unusable value would have done.
5. **Tests** on both sides of every band, plus one test that the documented defaults sit inside them.
6. **Write the bands into** `ARCHITECTURE.md` 7.6 and the README policy snippet, and note them where a
   contributor adds a setting to `airlock.toml`.

**Out of scope:** tuning `tail_max_len` and `tail_entropy` values against a corpus, which is 3.3 and
needs 0.10, and any change to how the ReDoS harness measures patterns.

## Acceptance criteria

- [ ] Every numeric policy setting has a documented accepted band, and a value outside it is refused with a message naming the band.
- [ ] `line_cap` cannot be raised past a bound that would let a pattern meet input the harness never measured, and the record says how the bound was chosen.
- [ ] `tail_entropy` is validated against the range entropy can actually take.
- [ ] The dogfood `airlock.toml` in this repository still loads, and `tests/unit/test_policy.py` plus `tests/unit/test_model.py` cover each refusal and each accepted boundary.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`Policy`, `BOOTSTRAP_POLICY`), [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`policy_from_toml`, `_policy_at_base`).
- Related: [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) measures at the default cap, and [`rules.apply_patterns`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) is where the cap keeps a regex off a line.
- The validation belongs in the model, per 2.1: a model is never built from something that failed to parse.
- Do not solve this by clamping a value silently. A clamp is the same class of defect as the missing-policy message.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
