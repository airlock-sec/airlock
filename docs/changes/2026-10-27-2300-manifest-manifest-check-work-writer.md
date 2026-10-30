---
date: 2026-10-27 23:00 UTC
tasks: 3.5, 7.7, FR-06, FR-12
summary: `manifest add` and `manifest check` work.
---

`manifest add` and `manifest check` work. The writer is the interesting half, because
`tomllib` reads TOML and nothing in the standard library writes it, and a writer for a
protected path is a place where a tool can quietly rewrite the trusted base. It is
therefore canonical rather than an editor: header emitted verbatim, entries sorted by
`sha256`, each entry's `paths` sorted, so `parse(render(x)) == x` and a repeated run
writes byte-identical content and reports "already lists every target". Where the model
cannot carry something the file has, the command refuses instead of dropping it, which
is why an entry-block comment and an unknown key in the entry region both abort before
the rewrite: the first has no field to live in (`note =` does), and the second would be
erased by a writer that emits from parsed data. An artifact has to look like an
artifact: `\0asm` magic, inside the repo, under `max_file_bytes`, with a stated `source`
and, for `origin = "built"`, a stated `build`. A second path for a known hash joins the
existing entry and keeps the reviewed provenance, since re-declaring it is not what the
operator approved. Nothing is staged or committed and the test checks that with git
plumbing, because a tool that auto-commits the trusted base is the bypass this file
exists to prevent. `manifest check` deliberately is not a second implementation of
artifact accounting: `run_scan` gained a `keep` predicate, so numbering, suppression,
fingerprints and the `fail_on` threshold all stay the scan's, and the check is the same
pipeline with the report narrowed to the `wasm-` rules. The consequence is a decision
rather than an accident, so it is written down in 7.7: an unlisted or swapped artifact
exits 1, while `wasm-manifest-stale` and `wasm-path-moved` are named at WARN and exit 0,
because the artifact that has left the tree is not the one that would ship. README
quickstart, `ARCHITECTURE.md` 7.7 and the FR-12 wording follow the verbs. Verified:
`pytest` 455 passed (22 more than at 2.13: 24 new tests, against one usage test that
replaces the three parametrized `manifest remove` cases it used to run), `ruff check`
and `ruff format --check` clean, `mypy src` clean on 24 files, self-scan exit 0 over 70
files with nothing skipped, plus a manual round trip in a temporary repository where one
globbed command recorded two artifacts, left the manifest modified-unstaged, and `check`
exited 0 both before and after the manifest commit. Not verified: no compiled contract
has been through `add`, only generated Wasm-shaped bytes, and the two-step flow (FR-06)
is still asserted by what the command prints rather than enforced by a required check,
since 1.9 is open
