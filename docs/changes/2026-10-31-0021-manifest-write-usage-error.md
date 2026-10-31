---
date: 2026-10-31 00:21 UTC
tasks: 2.10, 3.5
summary: A manifest or report write that fails is reported as a usage error (exit 2) naming the path, not as an internal error (exit 3).
---

`manifest add` wrote the manifest with a bare `write_text`, and `_emit` wrote `--output` the same way. An `OSError` from either path fell through to `main`'s catch-all, so a read-only manifest, an unwritable destination, or a directory in place of the file was reported as `internal error` with exit 3. Exit 3 is reserved for failures the operator cannot fix; this is an ordinary path or permission problem.

Both writes now convert `OSError` into `UsageError` with the path and the operating-system reason (`strerror`), so `main` prints one line and exits 2. The write stays a single `write_text` call, so a manifest is never left half-written.

Tests drive both cases through `cli.main`. The manifest case chmods the file to `0o444` and is skipped on Windows, where `write_text` does not honour the read-only bit; the directory-as-`--output` case runs on every platform and asserts the same exit code and message shape.

Verified locally on Windows: `pytest tests/unit/test_cli.py::TestWriteFailures` (1 passed, 1 skipped; the POSIX permission case is skipped because Windows does not honour the read-only bit), `ruff check .`, `ruff format --check .`, `mypy src` and `python scripts/roadmap_progress.py --check` pass. The full suite is not runnable on Windows: `tests/unit/test_collector.py` imports `os.geteuid`, and four `TestManifestCommands` cases already fail there on a TOML newline issue. CI runs the full suite and the POSIX permission case on Linux.
