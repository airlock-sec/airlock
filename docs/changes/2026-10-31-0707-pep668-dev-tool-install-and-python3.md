---
date: 2026-10-31 07:07 UTC
tasks: 1.19
summary: Contributor setup docs now install dev tools through `uv run --group dev` (PEP 668 safe), say `python3` everywhere, and name ci.yml's installed-console-script self-scan (1.19).
---

Issue #103: the documented contributor setup failed on a current Debian or Ubuntu Python in two
ways. `CONTRIBUTING.md` and `SUPPORT.md` told a contributor to have `ruff` and `mypy` available,
and a direct `pip install` into a PEP 668 "externally managed" interpreter refuses to run; the
venv alternative needs the distro's `python3-venv` package before it works at all. Separately,
`AGENTS.md`, `CONTRIBUTING.md` and `SUPPORT.md` wrote the bare `python` interpreter, which that
same base does not have, and `AGENTS.md` prescribed `python -m airlock scan --mode full` for the
self-scan while `SUPPORT.md` and `ci.yml` run the installed console script `airlock scan --mode
full .`, which is the form that actually exercises a wheel's bundled rule data.

Reproduced first rather than assumed: on this environment's own Debian 13, `pip install --dry-run
--group dev .` fails with "externally-managed-environment" before even reaching dependency
resolution, which is exactly the failure the issue describes.

`AGENTS.md` section 5, `CONTRIBUTING.md` step 4 and `SUPPORT.md`'s "Commands CI runs" now document
`uv run --group dev -- <command>` as the primary install path: `uv` provisions its own virtual
environment and interpreter, reads the pinned versions straight out of `pyproject.toml`'s `dev`
dependency group (a one-line comment was added there pointing back at this), and never touches the
system Python, so there is nothing for PEP 668 to refuse. Each of the three documents also states
the fallback the issue asked for: `pipx install "ruff>=0.17.3"` and `pipx install "mypy>=2.4.0"` for
the two standalone tools, with the `pipx ensurepath` note for `~/.local/bin` on `PATH`, and a venv
for the package plus `pytest` (which needs `airlock` importable alongside it), with the
`python3-venv` apt-package note attached. Every bare `python` in the three documents became
`python3`; `AGENTS.md`'s self-scan line became `airlock scan --mode full .`, with the
wheel-and-rule-data reason written next to it rather than left as an unexplained style choice, and
`CONTRIBUTING.md`, which previously had no self-scan line at all, now names the same command.

`tests/unit/test_contributor_docs.py` is the guard this adds: it pulls the self-scan command out of
`ci.yml`'s own "Self-scan" step and asserts `AGENTS.md`, `CONTRIBUTING.md` and `SUPPORT.md` each
name it, and separately scans the three documents for a bare `python` that is not `python3` and
not the capitalized prose name "Python 3.11". Run against the pre-fix text, two of the three cases
failed: the self-scan command was missing from two documents, and `AGENTS.md` alone had five bare
`python` hits (the roadmap-rule banner twice, the gates block three times). A fourth case checks
that every `pytest`, `ruff` and `mypy` floor the fallback pins by hand equals the one in
`pyproject.toml`'s dev group, since Dependabot bumps the group (#118) and the fallback must follow;
it failed on the fallback's first draft, which still carried the older floors. All four pass after
the edits.

Left alone, and noted here rather than silently dropped: the identical roadmap-rule banner
sentence that also writes `python scripts/roadmap_progress.py` repeats in `CLAUDE.md`, `PRD.md`,
`ARCHITECTURE.md`, `project_structure.md`, `README.md` and `.github/pull_request_template.md`.
The issue's Tech stack section names only `AGENTS.md`, `CONTRIBUTING.md`, `SUPPORT.md`,
`pyproject.toml` and `ci.yml`, and touching six more documents for one word is outside that scope,
so those files were not changed here.

Verified on a clean environment. No Docker was available in this sandbox, so the acceptance
test's "clean container" became a fresh `uv`-managed virtual environment under `/tmp`, built from
a copy of this repository with no pre-existing `.venv`, following only the documented commands:
Debian GNU/Linux 13 (trixie), kernel `6.12.94+`, `uv 0.13.6`, Python `3.14.10` (uv's own
provisioned interpreter; `requires-python` only pins `>=3.11`, so uv did not need to match CI's
3.11 exactly), `pytest 9.2.0`, `ruff 0.17.3`, `mypy 2.4.1`. `uv run --group dev -- python3 -m
pytest -q` reached `841 passed, 2 skipped`; `ruff check .` and `ruff format --check .` were clean;
`mypy src` reported no issues on 25 source files; the self-scan reported `0 HIGH · 0 WARN · 2 INFO
· 238 file(s) scanned, nothing skipped`. The two `untrusted-policy-source` INFO findings are
pre-existing and about `airlock.toml`/`wasm-manifest.toml` being read from a working tree with no
trusted base in `full` mode, unrelated to this change. Not verified: the `pipx` fallback path,
because `pipx` is not installed in this sandbox; it is documented from the pinned package names
pyproject.toml already carries, not from a run.
