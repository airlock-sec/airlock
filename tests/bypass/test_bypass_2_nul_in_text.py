"""`PRD.md` Appendix B case 2: a NUL byte in the first 4 KB of a text file (task 3.9).

This is the case worth reading twice. The old script lost the whole file to its own binary test, so
the NUL cost the scan and not the payload, and `node --check` still accepts the result. Airlock
reports the NUL itself and the `eval` on the next line, which is the fail-closed split
`ARCHITECTURE_ESSENTIALS.md` asks for: a file it cannot treat as text is a finding, and the line
that is text is judged.

Both findings are asserted, so a change that turns the NUL back into a silent skip fails this test
rather than passing on the `cfg-dynamic-code` line alone. The scan runs in `--mode full`;
`conftest.py` says why.
"""

from __future__ import annotations

from airlock.model import EXIT_FINDINGS


def test_the_nul_and_the_payload_are_both_reported(scan, verdict) -> None:
    report = scan(2)

    assert report.exit_code == EXIT_FINDINGS
    assert verdict(report) == [("cfg-dynamic-code", "HIGH"), ("nul-in-text", "HIGH")]


def test_both_findings_name_the_file_that_holds_them(scan) -> None:
    report = scan(2)

    found = {finding.rule_id: finding for finding in report.findings}
    assert found["nul-in-text"].path == "next.config.mjs"
    assert found["cfg-dynamic-code"].path == "next.config.mjs"
    assert found["cfg-dynamic-code"].line == 2
