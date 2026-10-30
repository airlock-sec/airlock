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
`YYYY-MM-DD-HHMM-<slug>.md`, a date that disagrees with its own name or sits in the
future, a record in a subdirectory the render does not walk, an empty or over-long
summary, a summary carrying a bare `|` or a stray `\` (the `\|` shape would have rendered
a four-cell row), an empty task list or one carrying a pipe, an unknown or repeated front
matter key, a source file with CRLF endings, a document with two `Last updated:` lines, a
roadmap whose markers are missing, doubled or in the wrong order, records with no block,
and a block with no records. A row whose count is zero out of zero renders as `0%`
instead of raising. `--check` now names the region that went stale and prints the diff
against what the sources say.

`scripts/check_roadmap_touched.sh` was broadened with it. A diff that touches anything
other than `ROADMAP.md` must add a record directly under `docs/changes/` and carry the
regenerated file; a record that exists on the base and is gone here fails the run, which
is the only thing standing between a pull request and deleting the changelog's source
whole; and a diff whose only file is `ROADMAP.md` is a planning edit and stays allowed.
The `Last updated` string comparison left the shell script for `--check`, which
regenerates the line from the newest record: the comparison could not prove the line was
right, and it rejected a backfill record for work that landed before the newest one. A
pull request that used to pass by editing a row in place now fails, which task 1.9's row
records as a strengthening rather than a change of subject.

Verified locally: the 36 rows that existed before this change are the first 36 files in
this directory, and the check that ran was containment rather than identity. Each old
row's text appears, whitespace-normalized, inside its own record body, all 36 of them,
which is why the detail is lossless. The rendered cells are summaries: 2 are the old row
whole, 27 are its opening cut at a word boundary, and 7 were written by hand because the
first sentence described the change badly. Every row's date and task list survives; 5
rows sit in a different position, all inside the 2026-10-27 cluster, because 3 records
carry only a date and now order by slug and one pair the hand-written table had
oldest-first is now newest-first.
`python scripts/roadmap_progress.py --check` exits 0 on the committed document;
`tests/unit/test_roadmap_gate.py` is 48 cases, up from 10, and the two that read this
repository's own commit tie every row to a record and every record to the order the
generator produces; `ruff check`, `ruff format --check`, `mypy src` and the full
self-scan run green over the tree with the new directory in it.

Not covered: the hosted runs of `roadmap-check.yml` and CI, which are the evidence that
the gate still fails a real pull request; the open pull requests, whose hand-written rows
become records on their own branches before they merge; and the collision argument
itself, which only a second branch can test.
