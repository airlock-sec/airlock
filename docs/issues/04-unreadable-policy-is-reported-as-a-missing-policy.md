---
slug: unreadable-policy-is-reported-as-a-missing-policy
title: A policy file that exists but cannot be read is reported as absent
labels: bug, good first issue, complexity: trivial, area: engine
roadmap: 2.7, G7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `_working_text` and `_untrusted_source` are shipped (2.7) and the two messages they emit are already covered by tests in `tests/unit/test_policy.py`, so this is a fork in one function plus one new case.

## Problem

[`policy._working_text`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) reads the config file and folds every failure into `None`:

```python
try:
    data = target.read_bytes()
except OSError:
    return None
```

The only failure it distinguishes is the size limit, which raises `ValueError` a few lines below.
Everything else, including a directory in place of the file, a permission refusal, an I/O error, and a
path that stops resolving mid-scan, returns `None`, and `None` means "absent" to the caller.

[`_from_working_tree`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) then asks only `policy_text is None`, so a file the scanner could
not open produces the finding `no airlock.toml in the working tree, so the shipped defaults apply`, at
INFO ([`_untrusted_source`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py)).

The direction is fail-closed and that is the important part: bootstrap defaults carry no suppressions,
so a maintainer who cannot read their own policy gets a stricter scan, not a laxer one. The defect is
the diagnosis. The message asserts a fact the scanner does not know, and the operator who runs the scan
after `chmod 000 airlock.toml`, or inside a container where the mount is not what they think, is told
the file is missing. `README.md` and `SUPPORT.md` both explain the absent-policy case as normal, so the
wrong advice is one search away.

The same fold exists on the `pr` and `push` path with different mechanics: `_blob_at` returns `None`
when the base does not carry the file, and a git failure there raises, so that half is already honest.
This is the working-tree half.

## What to build

1. **Separate the two states.** Have `_working_text` distinguish absent from unreadable, keeping the
   bootstrap fallback for both. A `Path.read_bytes` failure carries `errno` and `type(exc).__name__`;
   put the short version of it in the finding.
2. **Say which it is in the finding text** and choose the severity deliberately: absent is INFO the way
   it is today, and an unreadable policy file the repository does track is worth at least a WARN,
   because the maintainer's suppressions are not being applied and they may not know.
3. **Keep the wording of the absent case unchanged**, since `README.md` quotes it, and add the new
   message to `ARCHITECTURE_ESSENTIALS.md`'s finding-id list if the new id needs one.
4. **Test it with a real unreadable file**, and if you must skip on a platform where a permission
   refusal cannot be produced, name the platform in the skip reason rather than losing the case.

**Out of scope:** whether a scan should stop when its policy is unreadable. That is a bigger question
than this one, and today's answer (fall back and say so) is defensible; if you think it is wrong, say
so in the record rather than changing it here.

## Acceptance criteria

- [ ] A tracked `airlock.toml` that cannot be read produces a finding that does not claim the file is missing, and names the failure it saw.
- [ ] The absent case still emits today's INFO message with the same text.
- [ ] Severity for the unreadable case is chosen and justified in the record, and the fail-closed fallback to `BOOTSTRAP_POLICY` still applies.
- [ ] Tests cover absent, unreadable and over-cap for the policy file and, wherever it is cheap, the same three for the manifest file.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_working_text`, `_from_working_tree`, `_untrusted_source`).
- Tests: [`tests/unit/test_policy.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_policy.py) already asserts both `untrusted-policy-source` message halves.
- `AGENTS.md` section 4 forbids a silent skip, and this is the config-file instance of that rule: a fallback is allowed, an invented explanation is not.
- Keep `type(exc).__name__` in the message rather than `str(exc)`, which is the convention the collector already uses for `skipped-unreadable`.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
