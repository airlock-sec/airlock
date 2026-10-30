---
slug: collector-opens-each-file-twice
title: The collector stats and opens every file twice, and only detects the file that grew between the reads
labels: bug, complexity: medium, area: engine
roadmap: 2.2, 7.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** 2.2 is complete and its tests build real repositories, so this is a restructure of one function with a fixture pair for each new case.

## Problem

[`collector._collect_one`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) reads a regular file in two separate openings:

```python
size_bytes = os.path.getsize(target)
with target.open("rb") as handle:
    head = handle.read(HEAD_BYTES)
...
data = head
if size_bytes > len(head):
    with target.open("rb") as handle:
        data = handle.read(size_bytes + 1)
    if len(data) > size_bytes:
        ... skipped-unreadable: file changed size while being read
```

The first open gets the magic bytes, which is what the role resolution needs before deciding whether to
decode. The second gets the content. Between them the file is opened twice, stat'd once, and the size
that decides the oversize branch is a snapshot from the first instant.

Two consequences:

1. **Cost.** Two syscalls per file plus a `getsize`, on the path that 7.7 will measure. On a checkout of
   tens of thousands of small files that is the scanner's fixed overhead, and it is avoidable.
2. **A blind spot.** The mismatch check is one-directional. `len(data) > size_bytes` catches a file that
   grew, and the code says so. A file that *shrank* between the stat and the read yields fewer bytes
   than `size_bytes`, passes no check, and gets a `sha256` of content whose length the finding text and
   the oversize decision both described differently. The scanner then reports a hash of something that is
   not what the size said. It is a small window, but the working tree during a scan is not the attacker's
   least-controlled input, it is the one place a build step can still be running.

The role question and the read question can be answered in one opening, and the size the scanner reports
should be the size of the bytes it actually hashed.

## What to build

1. **Read once.** Open the file, read `size limit + 1` bytes in one pass, and derive the head, the
   oversize decision, the hash and the decode from that buffer. Keep the head-only read for the oversize
   case, since the point of the limit is to avoid holding the file.
2. **Report the size you saw**, so the `skipped-oversize` message describes the read rather than the
   earlier stat, and the mismatch case says which way it went.
3. **Decide the shrink case explicitly** and make it symmetric with growth: a buffer shorter than the
   stat is a file that changed under the scan, and either it is reported or the record says why it
   cannot be.
4. **Keep the ordering of the fail-closed branches** (unmerged, submodule, symlink, then the read) so
   2.14 and 7.2's behaviour does not move.
5. **Measure the difference** on a synthetic tree in the same shape 7.7 will use, and put the number in
   the record even if the answer is "under 1 percent, not why we did it".

**Out of scope:** the memory ceiling for `max_file_bytes` itself (the adjacent policy-bounds issue owns
that), and streaming decode of oversized files, which the design refuses on purpose.

## Acceptance criteria

- [ ] One `open` per regular file in `_collect_one`, with the oversize decision, the roles, the hash and the decode all derived from the same read.
- [ ] A file that shrinks between the stat and the read is either reported with a named skip reason or refused with a documented reason for not caring.
- [ ] Existing collector tests for oversize, unreadable, symlink, submodule and unmerged paths still pass unchanged, which is the proof the branch order did not move.
- [ ] A before-and-after wall-clock number for a synthetic tree of small files is in the record.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`_collect_one`, `HEAD_BYTES`, `SKIP_*` constants).
- Tests: [`tests/unit/test_collector.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_collector.py).
- `os.lstat` plus one read is enough for everything the module needs; `AGENTS.md` section 4 says a tracked path is opened for reading only and never followed, and one open makes that easier to review.
- Do not add a second helper that duplicates the read path; the module's own docstring names it as one of only two modules allowed to call `subprocess`, and it should stay as legible as that promise.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
