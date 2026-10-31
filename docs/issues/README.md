# The second issue intake

This directory holds a batch of 56 standalone issues drafted on 2026-10-30, numbered `01` to `56`. Each one names a file that exists in this repository, states what is wrong or missing, and proposes work that can be finished on its own. None of them blocks another: there are no `{{issue:slug}}` references, so they can be picked up, published and merged in any order.

The format is the one `docs/wave/issues/` uses: front matter with `slug`, `title`, `labels` and `roadmap`, then a repository-context banner, an unblocked banner, `## Problem`, `## What to build` with an out-of-scope line where it matters, `## Acceptance criteria` ending in the commands CI runs, `## Tech stack`, and the contact footer. The difference is the label set: these issues carry no `Stellar Wave` label, because they are ordinary backlog work rather than the curated funded batch, which stays at the fifteen issues in `docs/wave/issues/` published as #20 to #34.

## What is in the batch

| Files | Theme |
| --- | --- |
| `01` to `12` | Engine and CLI defects found by probing the shipped code |
| `13` to `19` | Rule coverage gaps where a shipped detector or rule family does not reach the file it should |
| `20` to `25` | Evasion and blind spots: cap padding, native binaries, archives, LFS pointers, base64 Wasm, Cargo runners |
| `26` to `39` | Features and reporting: SARIF, `explain`, `manifest remove`, `suppress`, inventory, `init`, `--dry-run`, and three performance items |
| `40` to `48` | Tests and CI: fixtures for state findings, golden reporters, shared temporary repositories, end-to-end fail-closed paths, version floors |
| `49` to `56` | Governance, audit and documentation: ownership, rulesets, documentation drift, setup commands, change-record truth, stale published bodies |

Every `roadmap:` id was checked against `ROADMAP.md` rather than trusted as written, and every `labels:` entry was checked against `gh label list` for this repository. A label the repository does not define is a publish-time failure, so adding one means creating it first.

## Publishing

`scripts/create_wave_issues.sh` takes a `--dir` argument and skips `README.md` in that directory:

```
sh scripts/create_wave_issues.sh --dir docs/issues           # dry run, prints every issue
sh scripts/create_wave_issues.sh --dir docs/issues --apply   # creates them, in filename order
```

The dry run is the default and makes no network call. `--apply` still requires the repository to have a `Stellar Wave` label, for the reason `docs/wave/settings.md` gives: on a repository Drips has not approved, that label is stripped and an issue created without it scores nothing. This batch was published as #52 to #107. Creating issues is an external, visible action, so it stays a maintainer's decision rather than a side effect of merging this directory.

Files are created in filename order, and `{{issue:self}}` is replaced with each issue's own number immediately after creation so the `Closes #N` line is correct. Keep the numeric prefixes when adding to the batch: they are the publish order, not a ranking.
