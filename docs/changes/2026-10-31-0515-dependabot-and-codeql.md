---
date: 2026-10-31 05:15 UTC
tasks: 1.6, 1.17
summary: Add weekly grouped Dependabot updates and a pinned CodeQL workflow for Python, the two largest quick gains in the Scorecard report.
---

Task 1.6 asked for Dependabot and the Scorecard report scored
Dependency-Update-Tool at 0 because no update tool was configured. `.github/dependabot.yml`
now declares the `github-actions` and `pip` ecosystems, both weekly, each grouped behind
`patterns: ["*"]` so a normal week is one pull request rather than one per action or
package. Both use a `chore(deps)` commit prefix, which keeps the pull request titles in
the Conventional Commits shape AGENTS.md 9 asks for, and both limit themselves to five
open pull requests.

The pip ecosystem reads the `dev` group in `pyproject.toml` (`pytest`, `ruff`, `mypy`);
the runtime dependency list stays empty. The comments in the file restate that
Dependabot pull requests still need a `docs/changes/` record, because the roadmap gate
does not exempt bots.

Task 1.17 covers the SAST check, which scored 0 because no static analysis ran on any
of the last 30 commits. `.github/workflows/codeql.yml` runs
`github/codeql-action/init` and `github/codeql-action/analyze` at v4.39.1, the same pin
the Scorecard workflow already uses for `upload-sarif`. It runs on pushes to `main`, on
a weekly schedule and on pull requests whose head is a branch of this repository.
Pull requests from forks are skipped because `security-events: write` is not granted to
them and the upload would fail; their code is analyzed on `main` after it merges. The
job holds only `contents: read` and `security-events: write`, and the workflow does not
gate a merge.

Expected effect once the workflows have run: Dependency-Update-Tool moves from 0 to 10,
and SAST rises from 0 as the last 30 commits on `main` receive a CodeQL analysis. The
overall score should move from 5.7 toward the 6.5 to 7 range without changing any other
check.

`project_structure.md` records `dependabot.yml` and the fifth workflow.

The first CodeQL run on the pull request that added the workflow succeeded: the
`Analyze Python` job passed in 57 seconds and analysis `2067326533` appeared in code
scanning for merge commit `e24f588`, category `/language:python`, 43 rules and 0 results.

Not verified at the time of this record: the first analysis on `main` itself, which
follows the merge, and the first Dependabot pull requests, which GitHub opens on its
next weekly schedule.
