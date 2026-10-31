---
slug: full-mode-ignores-base-and-before-without-saying
title: `--base` and `--before` are silently ignored when the mode does not use them
labels: bug, good first issue, complexity: trivial, area: engine
roadmap: 2.10, 2.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `_mode_for` already refuses a `--event` that contradicts `--mode`, so the precedent, the helper and the test file all exist; this is the same rule applied to the two remaining flags.

## Problem

[`cli._mode_for`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) is strict about a contradiction it can see: an `--event` with no trust
model is a usage error, and an `--event` whose implied mode differs from `--mode` is a usage error. It
is silent about the contradiction one level down.

`run_scan` passes `base` and `before` straight through to
[`policy.resolve_policy`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py), and the first thing that function does with them is
[`if mode is Mode.FULL: return _from_working_tree(...)`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py). In `full` mode both arguments
are discarded without a word. `pr` mode ignores `--before`; `push` mode ignores `--base`.

A caller that gets this wrong is telling the truth about a scan it did not run. The shape that worries
me is the one a maintainer wires by hand: a workflow step that passes `base: ${{ github.event.pull_request.base.sha }}`
with `--event workflow_dispatch`, or `--mode full` set by a default while a caller also passes a base
because it expected a diff-against-base scan. The scan runs, exits on what it found, and the base it
was given decided nothing. `ScanReport.base` is `None` in the JSON output, which is accurate, but
nothing points the reader at the flag they passed and did not get.

The inconsistency is also visible inside one function: the contradiction that argparse can see is an
error, and the contradiction one hop further is not.

## What to build

1. **Refuse the combination, or say what won.** The cheapest correct answer is to mirror `_mode_for`'s
   rule: a flag the resolved mode cannot use is a `UsageError` naming the mode and the flag. The softer
   answer is an INFO finding that records the ignored value, which is defensible if you can argue that
   a caller passes one fixed command line in several modes. Pick one and write the reason.
2. **Keep `--event` and `--mode` behaving the same way**, so a reader learns one rule rather than two.
3. **Cover both directions in tests**: `--mode full --base <sha>` and `--mode pr --before <sha>` each
   produce the chosen outcome, and the already-passing combinations still pass.
4. **Update the flag help** so `--base` and `--before` say which mode consumes them.

**Out of scope:** changing what any mode reads policy from. `full` reading the working tree is 2.7's
settled design and this issue does not touch it.

## Acceptance criteria

- [ ] Passing `--base` or `--before` to a mode that discards it either exits 2 with a message naming the mode, or produces a finding that names the discarded value.
- [ ] `--event` combined with a contradicting `--mode` keeps its existing exit-2 behaviour.
- [ ] Tests in `tests/unit/test_cli.py` cover the two ignored-flag cases and one accepted combination.
- [ ] `airlock scan --help` states which mode reads which flag.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_mode_for`, `_scan_command`, `UsageError`).
- Reference: [`src/airlock/policy.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/policy.py) (`resolve_policy` early return for `Mode.FULL`, `_trusted_ref` for `pr` and `push`).
- Tests: [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py) already exercises the `--event` contradiction path, which is the pattern to copy.
- The strictness argument lives in `AGENTS.md` section 4: a scan should never quietly mean something other than what the caller asked for.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
