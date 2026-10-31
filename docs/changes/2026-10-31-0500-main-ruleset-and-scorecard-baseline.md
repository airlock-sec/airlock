---
date: 2026-10-31 05:00 UTC
tasks: 1.3, 1.7
summary: Protect main with an active repository ruleset and record the Scorecard baseline: Branch-Protection 0 to 4 and overall 5.4 to 5.7.
---

Task 1.3 asked for rulesets on the default branch and task 1.7 asked for a Scorecard
workflow whose Branch-Protection check returns a score rather than an error. Both are
now in place.

The repository ruleset is `main protection`, id 26260923, targeting `~DEFAULT_BRANCH`
with enforcement `active` and no bypass actors. It blocks deletion and
non-fast-forward updates, requires a pull request, requires the `checks` and `roadmap`
status checks with a strict up-to-date policy, and requires review-thread resolution.
Administrators are not exempt.

Approvals are deliberately at 0. The organization has one member, so requiring one
approval would block every merge, and adding a bypass actor to get around that would
turn the setting off for the only person who can merge. A required-approver rule is
worth adding when a second maintainer exists, and it is the change that moves
Branch-Protection from 4 to 8 and Code-Review upward.

Scorecard is installed as `.github/workflows/scorecard.yml` from task 1.7 and the README
carries its badge. The run on `9a34dd2` succeeded. A rerun after the ruleset was created
published Branch-Protection at 4/10, up from 0, and the overall score at 5.7, up from
5.4. Scorecard reads the ruleset with the default token, so the fine-grained token named
in 1.7 was not needed.

The remaining check scores and the smallest honest way to move each one:

- Dependency-Update-Tool 0: add `.github/dependabot.yml` (task 1.6).
- SAST 0: enable CodeQL analysis for Python. The score rises as the last 30 commits
  receive a SAST run.
- Pinned-Dependencies 7: replace the unhashed `pip install` in CI with a
  `--require-hashes` requirements file.
- Branch-Protection 4 and Code-Review 5: add a second reviewer and require one
  approval plus code owner review. This cannot be done honestly with one member.
- CII-Best-Practices 0: register the project at bestpractices.dev and add the badge.
- Fuzzing 0: add a fuzzing integration such as OSS-Fuzz or ClusterFuzzLite.
- Packaging and Signed-Releases are -1 because there are no releases. A PyPI publish
  workflow (5.7, 9.9) and signed release artifacts (5.x) would score them.
- Maintained is 0 because the repository is under 90 days old; it resolves with time.
- Contributors needs contributions from more than one organization.

Verified: `GET /repos/airlock-sec/airlock/rules/branches/main` returns the four active
rules, the ruleset read reports no bypass actors, and the Scorecard rerun independent of
that read reports PRs required, force pushes and deletion disabled, up-to-date branches
and a status check required. Not verified: a direct push to `main` was not attempted,
because a rule failure would have written to the branch; the pull-request rule is the
thing that rejects it. The merge of this pull request is the first live run through the
ruleset.
