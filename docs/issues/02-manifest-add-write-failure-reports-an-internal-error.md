---
slug: manifest-add-write-failure-reports-an-internal-error
title: A failed write in `manifest add` surfaces as exit 3 instead of a plain usage error
labels: bug, good first issue, complexity: trivial, area: engine
roadmap: 2.10, 3.5
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `manifest add` shipped in 3.5 and its write path is four lines in `cli.py`; the fix is a classification and a test, with no dependency on anything else in the roadmap.

## Problem

`main` maps outcomes onto exit codes in one place: [`cli.main`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) turns a `ValueError` into
`2` with a one-line message and every other exception into `3` with `internal error:` prefixed to it.
`_manifest_add` builds the new manifest text with `policy.manifest_add`, then writes it with a bare
`(repo / args.manifest).write_text(...)` at [`cli.py:297`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py).

That call is the one part of the command that touches the filesystem outside the reader, and nothing
in the path converts its failure. A read-only `wasm-manifest.toml`, a directory the user cannot write,
a path that is a directory, and a filesystem that is full all raise `OSError`, which is not a
`ValueError`, so the operator is told `airlock: internal error: PermissionError: ...` and exit 3.

The distinction matters because the two codes mean different things to the people who read them. Exit 2
says the operator can fix this with a `chmod` or a different path. Exit 3 says the tool broke, which is
a bug report against Airlock, and it is the wrong call: nothing here is an unexpected internal failure,
it is the ordinary case of a file you are not allowed to write. The same asymmetry is worth one look at
`--output`, which is also a `write_text` on a caller-supplied path ([`cli._emit`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py)).

Note also that the unchanged short-circuit returns before the write, so an unwritable manifest is only
discovered on a run that actually changes something. That is the right order of work, and the issue is
only about how the failure is described.

## What to build

1. **Convert the write failures where they happen.** Wrap the manifest write, and the `--output` write
   in `_emit`, so an `OSError` becomes a `UsageError` naming the path and the reason. Keep the
   distinction honest: this is a config or operator problem, exit 2, never a silent success.
2. **Prove the classification with a test.** Build a repository with a manifest that needs a change,
   make it unwritable, and assert exit 2 and that the message names the file. Use `pytest.mark.skipif`
   only if a platform genuinely cannot produce the failure, and say which in the skip reason.
3. **Do not lose the partial state.** The command writes one file in one call today. If you touch this
   path at all, keep it that way or make it atomic; do not introduce a state where the manifest is
   half-written, because a manifest that parses but lists the wrong hash is worse than an old one.

**Out of scope:** adding a `--dry-run`, an overwrite prompt or a `manifest remove` verb; each is its own
issue and none of them change how a failed write is reported.

## Acceptance criteria

- [ ] `airlock manifest add` on an unwritable manifest exits 2 and prints a message naming the path and the operating-system reason.
- [ ] The same classification covers `--output` on an unwritable destination.
- [ ] A test drives the failure end to end through `cli.main` rather than calling the helper, so the exit code it asserts is the one a user gets.
- [ ] Exit 3 remains reserved for failures the operator cannot fix, and `README.md` or `SUPPORT.md` says so in the exit-code table.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`_manifest_add`, `_emit`, `main`, `UsageError`).
- Tests: [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py) is where the CLI's exit codes are already asserted.
- `OSError` covers `PermissionError`, `IsADirectoryError` and `OSError(ENOSPC)`; catching it broadly here is the point.
- The standard library only: no retry, no prompt, no new dependency.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
