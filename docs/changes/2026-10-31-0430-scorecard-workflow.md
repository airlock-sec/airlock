---
date: 2026-10-31 04:30 UTC
tasks: 1.7
summary: Install the OpenSSF Scorecard workflow and README badge (1.7): pinned actions, published results with OIDC, weekly and push-to-main runs.
---

Task 1.7 asked for a Scorecard workflow so the repository's own score is measured and
its Branch-Protection check can be read. This change adds the workflow and the badge the
published result feeds.

`.github/workflows/scorecard.yml` runs `ossf/scorecard-action` on every push to `main`
and weekly on Saturdays, with `publish_results: true` and SARIF uploaded to code
scanning. The workflow is shaped by the publishing API rather than by preference: it
carries no top-level or job-level `env` or `defaults`, holds `permissions: read-all` at
the workflow level, and gives only the analysis job `security-events: write` and
`id-token: write`. The OIDC token signs the result the badge reads.

All four actions are pinned by commit SHA with the tag they were resolved from, matching
the upstream example for scorecard-action v2.5.0 as it stood on 2026-10-31: checkout
v7.0.1, scorecard-action v2.5.0, upload-artifact v7.0.2 and codeql-action v4.39.1.

`README.md` gains the badge next to CI, pointing at the scorecard.dev viewer for
`airlock-sec/airlock`. `project_structure.md` no longer says the scorecard workflow is
missing.

The fine-grained token 1.7 names is not needed for Repository Rules, which Scorecard
reads with the default token; it is only needed for classic branch protection, which
this repository does not use. Rulesets themselves are task 1.3 and are still open, so
the Branch-Protection check cannot return a meaningful score yet and 1.7 stays
unticked. Its `Done when` clause is unchanged.

Verified locally: the workflow parses as YAML, both new and changed files pass the
repository's own scan, and the full gate set (pytest, ruff check, ruff format, mypy,
self-scan, roadmap gate and generated-region check) is green on the branch. Not
verified: the first hosted run, which needs a push to `main`, and the Branch-Protection
score, which needs 1.3.
