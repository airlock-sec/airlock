---
slug: policy-blobs-are-read-through-a-stripping-text-decode
title: Policy and manifest blobs from git are decoded as text and stripped before they are compared
labels: bug, complexity: trivial, area: engine
roadmap: 2.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `collector.git_bytes` already exists as the byte-exact git call (2.14 added it for exactly this reason on the listing path), so this is a change of which helper `_blob_at` uses and a test on the comparison it feeds.

## Problem

[`policy._blob_at`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) fetches a config file at a ref in two steps: it runs
`git ls-tree --name-only` to see whether the ref carries the path, then `git show <ref>:<path>`. Both
calls go through [`collector.git_text`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py), which decodes with `errors="replace"` and
returns `.strip()`.

Two losses follow, and both land on the trust path:

1. **`policy-changed` can be avoided by whitespace.** `_change_summary` compares the base copy against
   the head copy, and both arrive stripped. A change whose policy diff is only a trailing newline, or
   leading or trailing blank lines, compares equal, so the WARN that tells a reviewer "this pull request
   edits the policy it is being judged by" does not fire. It is a low-value edit to make deliberately,
   but the whole point of `policy-changed` (2.7, B1) is that a reviewer sees policy movement.
2. **Invalid bytes are rewritten before parsing.** `errors="replace"` puts U+FFFD where the file had
   something undecodable, and `tomllib` then parses a document that is not the bytes in the object
   store. That is usually a parse error anyway, but it is a parse error about text the scanner invented,
   and the message will not match what `git show` prints.

`git_bytes` already exists and is byte-exact; the module's own docstring says the listing needs it for
that reason. The reading half of the same module was left on the text helper.

## What to build

1. **Read config blobs as bytes** and decode them once, explicitly, at the point where a failure can
   become a finding or a `ValueError` with the path in it. Do not silently replace: an undecodable
   `airlock.toml` should be refused, not repaired.
2. **Compare the two copies byte-exactly**, so a whitespace-only policy edit is reported. Keep
   `_change_summary`'s line-count shape for the message; the equality test is what needs the change.
3. **Keep `git ls-tree` as a text call** if you want, since a name is not content, or route it through
   `-z` while you are here. Say which.
4. **Add the test that pins it**: a base commit whose policy ends in a newline and a head commit whose
   policy does not, with everything else identical, must produce `policy-changed`.
5. **Check the other `git_text` callers** in the same pass and record which of them are content rather
   than plumbing (`rev-parse`, `cat-file`, `merge-base`, `cat-file -e` are fine as text).

**Out of scope:** any change to which ref the policy is read from, and to how unknown keys are
reported. Both are settled in 2.7 and covered by tests.

## Acceptance criteria

- [ ] `_blob_at` returns bytes, or text decoded with a failure that surfaces as a config error naming the file.
- [ ] A trailing-newline-only change to `airlock.toml` between base and head produces `policy-changed`.
- [ ] A policy blob containing invalid UTF-8 produces a message that matches the bytes in the object store rather than a replacement-character document.
- [ ] `tests/unit/test_policy.py` covers both cases over real temporary repositories, and every remaining `git_text` call site is named in the record as content or plumbing.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`_blob_at`, `_policy_at_base`, `_manifest_at_base`, `_change_summary`).
- Code: [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`git_bytes` versus `git_text`, and the docstring that explains why the listing needed bytes).
- Tests: [`tests/unit/test_policy.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_policy.py) builds real repositories for the B1 case already.
- This touches a protected path (`policy.py`), so `AGENTS.md` section 12 applies: owner review, and the change must not weaken a check. It cannot: bytes are a superset of what text gave.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
