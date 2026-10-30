---
date: 2026-10-28 11:23 UTC
tasks: 1.5, 1.9, G2, G4, G5, G10
summary: The CI skeleton and the roadmap gate are written, and both are marked `[~]` rather than done because neither has been observed on GitHub yet.
---

The CI skeleton and the roadmap gate are written, and both are marked `[~]` rather than
done because neither has been observed on GitHub yet. `.github/workflows/ci.yml` runs
pytest, `ruff check`, `ruff format --check`, `mypy src` and the self-scan through the
installed `airlock` console script on python 3.11, with `permissions: contents: read` at
the top level. The two actions are pinned to the commit each tag resolves to, read from
the GitHub API and not guessed
(`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` for v7.0.1,
`actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` for v7.1.0, both
confirmed to be commit objects), and the pin is annotated with the tag so a future bump
can be compared against a named version; AGENTS.md 9 still requires reading the diff
before moving either. `.github/workflows/roadmap-check.yml` runs the two gate scripts on
every pull request, with the base branch name reaching the shell through `env:` because
a value a fork can influence does not belong interpolated into a command line.
`scripts/roadmap_progress.py` renders the progress table from the task lines into the
`PROGRESS:START/END` block: `[~]` counts as unfinished, phase 9 stays out of the
readiness sum and appears as `9 (backlog)`, and the gates row comes from section 3, so
the table cannot drift from the checklist again. It disagrees with the committed table
on the first run and the disagreement was the script dropping its own closing marker,
not the document being wrong. `scripts/check_roadmap_touched.sh` refuses a diff that
touches files but not `ROADMAP.md`, and a `ROADMAP.md` edit that left `Last updated`
where it was. `tests/unit/test_roadmap_gate.py` runs both as subprocesses over temporary
roadmaps and temporary git repositories, ten cases including this branch passing the
gate it adds, a missing progress block being an error rather than a traceback, and a
phase heading with no tasks refused instead of dividing by zero. AGENTS.md section 5 no
longer says the commands exist "once task 1.4 is done", and `project_structure.md` names
the two workflows that now exist. Verified: every CI step run locally in a python
3.11.16 virtualenv built the way the workflow builds one (`uv venv --python 3.11`, `pip
install . pytest ruff mypy`): 475 tests passed, `ruff check` clean, `ruff format
--check` clean on 45 files, `mypy src` clean on 24 files, `airlock scan --mode full .`
exit 0 over 72 files; both workflows parse as YAML; `roadmap_progress.py --check` exits
0 against this file. Not verified: any run on GitHub, which is the remaining half of 1.5
and 1.9 and waits on write access, and whether the check can be made required on this
org plan (0.13)
