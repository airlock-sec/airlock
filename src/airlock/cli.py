"""Argument parsing, command dispatch and exit codes. Implemented by task 2.10.

Commands planned: `scan` and `manifest add|check` (ARCHITECTURE.md 8 and 6.5). There is no
`init` command and no `rules test` command; both were cut (ARCHITECTURE.md 16.4).
"""

from __future__ import annotations

import sys

from .model import EXIT_CONFIG


def main(argv: list[str] | None = None) -> int:
    """Exit non-zero until the engine exists, so no caller can read a green run."""
    del argv
    print(
        "airlock: the scan engine is not implemented yet (see ROADMAP.md Phase 2)",
        file=sys.stderr,
    )
    return EXIT_CONFIG
