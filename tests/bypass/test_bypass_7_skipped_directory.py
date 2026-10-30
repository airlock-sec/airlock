"""`PRD.md` Appendix B case 7: a payload under a directory the old script skips by name (task 3.9).

The old script matched `vendor/` against its own skip list, so the file was never opened. Airlock
has no default directory skips: it opens `vendor/thing/loader.js`, resolves it to role `source`, and
the text-side family reads it. `tests/unit/test_builtin_patterns.py` carries the same shape through
the engine; this case is the probe's data driven all the way to an exit code, which is what gate G2
asks for.

The scan runs in `--mode full`; `conftest.py` says why.
"""

from __future__ import annotations

from airlock.model import EXIT_FINDINGS


def test_a_payload_under_vendor_is_reported(scan, verdict) -> None:
    report = scan(7)

    assert report.exit_code == EXIT_FINDINGS
    assert verdict(report) == [("pat-decode-eval", "HIGH")]
