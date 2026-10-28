---
slug: settle-sarif-fingerprint-key
title: Settle the SARIF partialFingerprints key spelling after the rename
labels: Stellar Wave, complexity: trivial, area: docs, enhancement, good first issue
roadmap: 7.12
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** Its only dependency, the 1.12 rename sweep, merged on 2026-10-28. This is a bounded decision with a grep-verified target and no runtime code to change.

## Problem

The rename sweep replaced 37 stale `repo-guard` spellings across the four design documents, and one
survivor sits in a place the sweep deliberately did not touch: the SARIF row of
[`ARCHITECTURE.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE.md) 6.6 still
specifies `partialFingerprints["repoGuard/v1"]`.

That is not a cosmetic leftover. `partialFingerprints` is the field code scanning uses to correlate
a result across commits, so the key name is the identifier an external consumer stores. Once SARIF
output exists (task 7.6), changing it means every previously recorded finding looks like it moved.
[`src/airlock/report/sarif.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/report/sarif.py)
knows this and says so in its docstring, which is the only reason the module is still six lines
long.

Deciding it now costs one line in three files. Deciding it in 7.6 costs a migration note for
consumers who stored the old key.

## What to build

Choose the spelling, write it down where the next reader will look, and leave a check behind so it
cannot silently revert.

1. **Decide.** The package is `airlock`, the CLI is `airlock`, the policy file is `airlock.toml` and
   the Action environment prefix is `AIRLOCK_`. `airlock/v1` is the consistent choice, and the
   `v1` suffix is what lets a future fingerprint change be a new key rather than a broken consumer.
   If you disagree, say why in the pull request; the decision matters less than it being recorded.
2. **Apply it** in `ARCHITECTURE.md` 6.6 and in the `sarif.py` docstring, which currently describes
   the old name as an open question rather than as history.
3. **Record the decision** as a row in the `ROADMAP.md` section 7 decision log. The next free id is
   D-09. The roadmap rule requires a decision to appear there, not only in a changelog row.
4. **Make it checkable.** `tests/unit/test_model.py` already asserts a documented set of rule ids
   verbatim against `STATE_RULE_IDS`, which is the pattern to follow: a small test that reads
   `ARCHITECTURE.md` and fails if the SARIF row names a key that is not the decided one. A grep in a
   CI step would also work; pick one and explain the choice.

**Out of scope:** implementing the SARIF reporter. It stays a stub until 7.6, and this issue is done
when the name it will use is settled and documented.

## Acceptance criteria

- [ ] `git grep -n "repoGuard"` over the tracked tree returns only `ROADMAP.md` rows that record the rename history, and no design document.
- [ ] `ARCHITECTURE.md` 6.6 names the decided key, and `sarif.py`'s docstring states it as settled rather than as an open question.
- [ ] A D-09 row exists in the `ROADMAP.md` decision log with the date and the spelling.
- [ ] The new test fails when the documented key is changed in the document but not in the test, and passes otherwise.
- [ ] `ROADMAP.md` is updated in the same pull request: 7.12 ticked, a changelog row with a UTC date, `Last updated` moved, and `python scripts/roadmap_progress.py --check` passing.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Runtime: Python 3.11, standard library only. [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 forbids adding a runtime dependency, and a scan never touches the network, so a helper library is not an option here.
- Where the stale spelling lives: [`ARCHITECTURE.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE.md) 6.6, in the `sarif (P1)` row of the reporter table.
- What it must agree with: [`src/airlock/fingerprint.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/fingerprint.py), which computes the digest, and the verbatim-assertion style already used in [`tests/unit/test_model.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_model.py).
- The deliverable is one decision plus one test that fails when the document and the code drift again, and a decision-log row in [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) section 7.
- Out of scope: writing `sarif.py`. SARIF output is 7.6 and stays deferred; this issue only settles the key that issue will use.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md) — where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md) — private disclosure only; never open an issue about a bypass
