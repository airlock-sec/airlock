---
date: 2026-10-30 22:22 UTC
tasks: 1.16
summary: Second issue intake: fifty-six standalone issues under `docs/issues/`, each grounded in a shipped file and a probe or audit finding, plus a README and a publisher that skips it.
---

The repository had one funded issue batch, the fifteen issues in `docs/wave/issues/`
published as #20 to #34, and a backlog of unticked roadmap rows with no issue behind
them. This change adds a second batch in a directory of its own so the funded set stays
curated and its numbering stays stable.

`docs/issues/` holds 56 files, `01` to `56`, in the template task 1.14 established. Each
names a file that exists and most cite a line, and the work behind each one is either a
probe run against the shipped code or a read of the file it accuses. The batch covers
engine and CLI defects, rule families that never reach the file they should, evasion
paths such as padding a line past `line_cap` or encoding Wasm as base64, missing
commands and reporters, test and CI gaps, and governance and documentation drift.

The front matter was checked instead of trusted. All 42 distinct `roadmap:` ids parse
out of `ROADMAP.md`'s task lines, and all 13 distinct labels exist in `gh label list`
for this repository. An earlier draft used three labels the repository does not define,
`complexity: low`, `area: reporting` and `area: detectors`, and those were corrected
rather than left for the publish step to fail on.

There are no cross references between the issues, so no issue waits on another and the
filename order is publish order rather than a dependency order. The batch re-files
nothing from open issues #23, #26, #28, #29 and #34 or from the open pull requests. No
`Stellar Wave` label is attached, because this is backlog work and the funded batch is
the curated fifteen.

`scripts/create_wave_issues.sh` now skips a `README.md` in the target directory. The
glob picked it up and the title check refused it, so a directory that documents its own
batch could not be staged at all. `docs/issues/README.md` records the themes and the
publish commands. A dry run over the directory printed `56 issue(s) staged, nothing
created`, and the apply run then created #52 to #107 in filename order. Each body's
`{{issue:self}}` was patched immediately after creation; the first and the last were
checked and read `Closes #52` and `Closes #107`.
