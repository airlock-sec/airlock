---
date: 2026-10-27 19:07 UTC
tasks: 1.4, 1.8, 1.10, 1.11, 2.1, 1.12, 2.13, 7.12
summary: Scaffold committed on branch `feat/1.4-scaffold` (not yet merged): the package tree per `project_structure.md` with behavior documented in each stub and nothing implemented, `cli.py` exiting 2 so an unbuilt tool cannot pass.
---

Scaffold committed on branch `feat/1.4-scaffold` (not yet merged): package tree per
`project_structure.md` with behavior documented in each stub and nothing implemented
(`cli.py` exits 2 so an unbuilt tool cannot read as a pass), `model.py` data models with
67 unit tests, `pyproject.toml` (hatchling, ruff, mypy, pytest), `rules/roles.toml`,
dogfood `airlock.toml` and `wasm-manifest.toml`, `README.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `.github/CODEOWNERS` and the PR template, `.gitignore`, and the doc set
copied to the repo root. `project_structure.md` renamed from repo-guard to airlock.
Added 1.12 (rename sweep in the four remaining docs, 37 stale references), 2.13
(`FileEntry` and `ScanContext` drafts to confirm) and 7.12 (SARIF fingerprint key
spelling). 1.3, 1.8, 1.10 and 1.11 stay open until merge
