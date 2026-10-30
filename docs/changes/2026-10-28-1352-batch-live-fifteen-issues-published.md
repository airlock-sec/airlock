---
date: 2026-10-28 13:52 UTC
tasks: 1.13, 1.14, G10, 8.4
summary: The batch is live: fifteen issues published as #20 to #34, and the thirteen labels they need created first (`Stellar Wave`, three `complexity: *`, seven `area: *`, `type: test`, `blocked`).
---

The batch is live: fifteen issues published as #20 to #34, and the thirteen labels they
need created first (`Stellar Wave`, three `complexity: *`, seven `area: *`, `type:
test`, `blocked`). Each body gained a `## Tech stack` block naming the files the work
touches, the test command for that area and the protected paths in the way, which is
what makes an issue pickable without a tour of the repository. 1.13 and 1.14 tick on the
evidence in their own rows. Publishing found two defects in
`scripts/create_wave_issues.sh`, both fixed here rather than papered over: the
front-matter extractor treated the opening `---` as the closing one, so the first pass
published each file's `slug:` and `labels:` header as part of the description, and the
documented `--repo owner/name` form was rejected by a parser that only accepted
`--repo=value`. Every body was re-sent from the corrected source, and the refusal path
was exercised against a repository with no `Stellar Wave` label (exits 1, writes
nothing). Verified after publishing: no `{{issue:` token and no leaked header remains in
any of the fifteen bodies, #33 names #30 and #34 names #20 as their blockers, each
`Closes #N` points at itself, all labels landed on all fifteen, and every `blob/main`
link in the batch resolves to a tracked path. Also corrected: #34 no longer claims
decision D-09, which #22 is the one proposing, and one structural defect in this file
itself, where the earlier commit today left a blank line and a bare `|---|---|---|` in
the middle of the changelog and cut the two newest rows off from their own table header.
Not verified: whether Drips counts the `Stellar Wave` label on a repository it has not
approved. The expectation, stated in `docs/wave/settings.md` before this happened, is
that the label is stripped until the application succeeds, so these fifteen are ordinary
GitHub issues until then and roll into the next Wave once it does. `SUPPORT.md` and
`docs/wave/settings.md` are linked from every body and do not exist on `main` until #19
merges. Verified locally: 475 tests, ruff clean, format clean on 45 files, mypy clean on
24, self-scan 0 HIGH over 96 files, both gates green on #19's CI run
