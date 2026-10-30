"""`PRD.md` Appendix B case 1: a `.wasm` file of any content (task 3.9).

The old script treated the Wasm magic as a binary marker and skipped the file, so a committed
artifact rode in unread. Airlock identifies it by magic too, but reports it as an artifact the
manifest does not list, which is a finding rather than a skip.

The scan runs in `--mode full`; `conftest.py` says why.
"""

from __future__ import annotations

from airlock.model import EXIT_FINDINGS


def test_any_wasm_content_is_an_unlisted_artifact(scan, verdict) -> None:
    report = scan(1)

    assert report.exit_code == EXIT_FINDINGS
    assert verdict(report) == [("wasm-unlisted", "HIGH")]
