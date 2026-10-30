"""`PRD.md` Appendix B case 3: a payload line ending in the old scanner's allow marker (task 3.9).

The old script checked `malware-scan: allow` before its rule table, so a line could exempt itself
from every rule. Airlock has no inline marker to honour and never should (`AGENTS.md` 4), which
makes this case a differential: the same payload with and without the marker must produce the same
findings. A test that only ran the marked file would pass on a marker that was merely ignored by
accident; this one fails if the marker ever starts to matter.

The scan runs in `--mode full`; `conftest.py` says why.
"""

from __future__ import annotations

from scripts.bypass_probe import ALLOW_MARKER

from airlock.model import EXIT_FINDINGS


def test_the_inline_marker_changes_nothing(
    scan, scan_shape, appendix_case, verdict, strip_marker
) -> None:
    marked_files = appendix_case(3).files
    plain_files = strip_marker(marked_files)
    assert plain_files != marked_files
    assert ALLOW_MARKER.encode() not in plain_files["loader.js"]

    marked = scan(3)
    plain = scan_shape(plain_files, "plain")

    assert verdict(marked) == verdict(plain) == [("pat-decode-eval", "HIGH")]
    assert marked.exit_code == plain.exit_code == EXIT_FINDINGS
