---
date: 2026-10-30 17:36 UTC
tasks: 1.15, 1.9
summary: Take the changelog out of `ROADMAP.md`: one record per change under `docs/changes/`, the section 9 block and `Last updated` generated from them, and the roadmap gate asking for a record instead of an edit to the shared file.
---

Two branches that both landed a change rewrote the same lines of `ROADMAP.md`: the
`Last updated` line, the head of the changelog table, and the row each of them wanted at
the top. The progress table had been generated from the task lines since 1.9, so the
changelog was the last hand-maintained derived data in the repository, and it was the
widest merge conflict a pull request could carry.

Each change now owns a file. `docs/changes/YYYY-MM-DD-HHMM-<slug>.md` carries three
front matter keys, `date:`, `tasks:` and `summary:`, and the record itself below them.
Section 9 of `ROADMAP.md` renders one row per file, newest first, each row linking to
the file it came from, so the table cell stays short and the detail lives somewhere a
reviewer can read. Two records never occupy the same path, and a conflict inside the
generated block is resolved by keeping either side and running the generator again.

`scripts/roadmap_progress.py` renders three regions from their sources: the progress
table from the task lines, the changelog from the records, and `Last updated` from the
newest record. It refuses a record rather than rendering it: a name that is not
`YYYY-MM-DD-HHMM-<slug>.md`, a date that disagrees with its own name, an empty,
over-long or pipe-bearing summary, an empty task list or one carrying a pipe, an unknown
or repeated front matter key, a roadmap whose markers are missing, doubled or in the
wrong order, records with no block, and a block with no records. `--check` now names the
region that went stale and prints the diff against what the sources say.

`scripts/check_roadmap_touched.sh` was broadened with it. A diff that touches anything
other than `ROADMAP.md` must add a record and carry the regenerated file; a diff whose
only file is `ROADMAP.md` is a planning edit and stays allowed. The `Last updated` check
kept its place and changed meaning, because that line is now generated: one that did not
move means the newest record predates the change being merged. A pull request that used
to pass by editing a row in place now fails, which task 1.9's row records as a
strengthening rather than a change of subject.

Verified locally: the 36 rows that existed before this change are the first 36 files in
this directory, checked by comparing the multiset of (date, whitespace-normalized body,
tasks) read back out of the generated block against the rows parsed from the pre-change
file;
`python scripts/roadmap_progress.py --check` exits 0 on the committed document;
`tests/unit/test_roadmap_gate.py` is 38 cases, up from 10, and the two that read this
repository's own commit tie every row to a record and every record to the order the
generator produces; `ruff check`, `ruff format --check`, `mypy src` and the full
self-scan run green over the tree with the new directory in it.

Not covered: the hosted runs of `roadmap-check.yml` and CI, which are the evidence that
the gate still fails a real pull request; the open pull requests, whose hand-written rows
become records on their own branches before they merge; and the collision argument
itself, which only a second branch can test.
