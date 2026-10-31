---
date: 2026-10-31 06:31 UTC
tasks: 1.18
summary: Tick 1.18 after Scorecard on main reports Pinned-Dependencies 10 and the overall score moves from 6.9 to 7.0.
---

Task 1.18's done condition was Scorecard's Pinned-Dependencies reporting 10, not the merge
of #120. The `checks` job on that pull request passed on the hosted runner in 51 seconds
([run `41176464491`](https://github.com/airlock-sec/airlock/actions/runs/41176464491)), and
the Scorecard run on `main` for merge commit `30b809e`
([run `41176617992`](https://github.com/airlock-sec/airlock/actions/runs/41176617992))
reports:

- Pinned-Dependencies 10, "all dependencies are pinned", with "14 out of 14 GitHub-owned
  GitHubAction dependencies pinned", "1 out of 1 third-party GitHubAction dependencies
  pinned" and "2 out of 2 pipCommand dependencies pinned".
- Overall score 7.0, up from 6.9 before the change.
- SAST 8, up from 7, because 13 of the last 30 commits have now received a CodeQL analysis.

No other check moved. The change record for the install itself
(`docs/changes/2026-10-31-0619-hash-pinned-ci-install.md`) now carries the same evidence in
place of its "not verified" paragraph, and the 1.18 row is `[x]` with the two run links.
