---
date: 2026-10-31 08:36 UTC
tasks: 3.5, 3.12
summary: Close #86 (task 3.12): `manifest add --dry-run` prints the entry a write would produce and writes nothing, exiting 0 either way.
---

`manifest add` wrote `wasm-manifest.toml` the moment it ran, so a CI job that only wants to tell a maintainer "this artifact is unlisted" had no way to show the entry without writing the protected file. `--dry-run` now prints the same `change.text` that a real run would write and skips the `write_text` call, exiting `EXIT_PASS` whether it wrote or not: the flag is advice, not a gate.

`manifest_add` in `policy.py` already validated every target and rendered the complete new text before `_manifest_add` touched the filesystem, so there is no second render for the preview to drift from and a bad path among several targets raises before either a write or a preview happens, naming the failed target. Both the preview and a real write now print the same `PROVENANCE_NOTE`: `--origin` and `--source` are read from the flags given, not checked against the artifact, so a machine-filled entry is a suggestion for the reviewer rather than an attestation.

Four new tests in `tests/unit/test_cli.py::TestManifestCommands` cover the dry run (nothing written, exit 0, the printed text), that the dry-run output and the written file come from the same `change.text`, and that the provenance note appears on both the preview and the real write. A fifth asserts a bad target in a multi-target add already wrote nothing and named the target before this change, documenting that contract rather than treating it as new behavior. `README.md`, `site/usage.html` and `ARCHITECTURE.md` 7.7 describe the flag in the CI-advice position; `PRD.md`'s `manifest add` paragraph and command-line usage grid gained it too.

Verified: stashed `src/airlock/cli.py` only (keeping the test changes) and re-ran the five new tests; four failed for the right reason (`unrecognized arguments: --dry-run`, then `module 'airlock.cli' has no attribute 'PROVENANCE_NOTE'`) and the bad-target test already passed, confirming it was pre-existing behavior. After restoring the change: `pytest` 843 passed, 2 skipped (pre-existing skips, unrelated); `ruff check .` and `ruff format --check .` clean; `mypy src` clean on 25 files; `python scripts/build_site.py --check` clean.
