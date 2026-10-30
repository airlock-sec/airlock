"""`PRD.md` Appendix B case 4: an allowlist file containing a single `*` (task 3.9).

The old script's allowlist was a file in the scanned tree, so a change could add `*` and exempt
itself. Airlock has no such file: suppressions are fingerprint-keyed, carry a reason and are read
from the trusted base. The case commits the allowlist next to the payload, and the payload is still
reported, which is the shape that matters. The file itself is data, not a source of exemptions.

The scan runs in `--mode full`; `conftest.py` says why.
"""

from __future__ import annotations

from airlock.model import EXIT_FINDINGS


def test_a_wildcard_allowlist_exempts_nothing(scan, verdict) -> None:
    report = scan(4)

    assert report.exit_code == EXIT_FINDINGS
    assert verdict(report) == [("pat-decode-eval", "HIGH")]
