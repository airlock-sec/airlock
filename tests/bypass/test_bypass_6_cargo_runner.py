"""`PRD.md` Appendix B case 6: a `.cargo/config.toml` with a shell `runner` (task 3.9).

The shape is invisible to this build, and the test says so rather than turning the gap into a green
check. `.cargo/config.toml` has no role and `cargo_vectors` is still a docstring, so nothing reads
the `runner` line. Task 6.4 closes that; when it does, delete the skip and keep the assertion it
already makes. It names no rule id on purpose: the rule that closes this does not exist yet, and
inventing its name here would be a claim about 6.4 rather than about today.
"""

from __future__ import annotations

import pytest

from airlock.model import EXIT_FINDINGS, Severity


@pytest.mark.skip(
    reason="blocked by 6.4: `.cargo/config.toml` has no role and `cargo_vectors` is not written"
)
def test_a_shell_cargo_runner_fails_closed(scan) -> None:
    report = scan(6)

    assert report.exit_code == EXIT_FINDINGS
    highs = [finding for finding in report.findings if finding.severity is Severity.HIGH]
    assert [finding.path for finding in highs] == [".cargo/config.toml"]
