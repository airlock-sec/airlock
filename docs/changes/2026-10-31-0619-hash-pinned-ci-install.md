---
date: 2026-10-31 06:19 UTC
tasks: 1.18
summary: Hash-pin the CI toolchain and build backend, install with --require-hashes, and install the project from a wheel so every pip command in CI is pinned.
---

Scorecard's Pinned-Dependencies check scored 7 because the one `pip install` in `ci.yml`
named `pytest`, `ruff` and `mypy` without hashes. The tools are dev-only, but the build step
also let pip fetch a build backend unpinned, so the gap was real and not only a score artifact.

`requirements-ci.txt` is now a hash-pinned lock generated from the `dev` group in
`pyproject.toml`:

```
uv pip compile pyproject.toml --group dev --generate-hashes \
  --python-version 3.11 --python-platform x86_64-unknown-linux-gnu -o requirements-ci.txt
```

The group now lists `hatchling` as well as the three test tools. That makes the build backend
part of the same lock, which lets the wheel build run with `--no-build-isolation` and never
download anything after the hashed install. The lock is resolved for the CI platform and
Python version, so it is not meant to be installed elsewhere; the file header carries the
command that regenerates it.

`ci.yml` now has three steps in place of the one install line:

1. `python -m pip install --quiet --require-hashes -r requirements-ci.txt`
2. `python -m pip wheel --quiet --no-build-isolation --no-deps --wheel-dir dist .`
3. `python -m pip install --quiet --no-deps dist/*.whl`

Scorecard reads the `run` text, treats `--require-hashes` as pinned, and treats an install
whose only package is a `.whl` as pinned, so both install commands score. The wheel install
keeps the 5.7 check that the built wheel carries `rules/`.

Verified in a clean Python 3.11 venv built with `uv venv --seed`: real pip accepted the lock
with `--require-hashes`, the wheel built and installed, the suite reported 836 passed and 2
skipped with the known load-sensitive ReDoS timing failure that passes in isolation, ruff check
and format were clean, mypy was clean, and the installed console script scanned 237 files with
0 HIGH and nothing skipped.

Not verified at the time of this record: the workflow on a hosted runner and the next
Scorecard run. Task 1.18 stays started until Pinned-Dependencies reports 10.
