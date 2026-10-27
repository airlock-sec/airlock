"""Console reporter (task 2.9, `ARCHITECTURE.md` 6.6).

One finding per line: severity, rule id, `path:line`, message, then a summary line a human
reading CI logs can scan in one pass. Paths arrive from the repository, so a file named with a
newline cannot be allowed to split one finding across two lines, and nothing here renders a
message as anything but text.

No color and no terminal detection: the same bytes go to a pipe, a log file and a TTY, which
keeps the output golden-testable.
"""

from __future__ import annotations

from ..model import Finding, ScanReport, Severity


def flatten(text: str) -> str:
    """One line, whatever the input held."""
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


def location(finding: Finding) -> str:
    """`path:line`, or the bare path for a file-level finding (line 0)."""
    path = flatten(finding.path)
    return f"{path}:{finding.line}" if finding.line else path


def render(report: ScanReport) -> str:
    """The whole report as console text, ending with the summary line."""
    lines = [
        f"{finding.severity.label.upper():<5}  {finding.rule_id:<28}  {location(finding):<48}"
        f"  {flatten(finding.message)}"
        for finding in report.findings
    ]
    lines.append(summary_line(report))
    return "\n".join(lines) + "\n"


def counts_by_severity(report: ScanReport) -> dict[Severity, int]:
    counts = {severity: 0 for severity in Severity}
    for finding in report.findings:
        counts[finding.severity] += 1
    return counts


def skipped_phrase(report: ScanReport) -> str:
    """`3 skipped-oversize, 1 submodule-present`, or `nothing skipped`."""
    if not report.files_skipped:
        return "nothing skipped"
    return ", ".join(f"{count} {reason}" for reason, count in sorted(report.files_skipped.items()))


def summary_line(report: ScanReport) -> str:
    counts = counts_by_severity(report)
    tally = " · ".join(
        f"{counts[severity]} {severity.label.upper()}" for severity in reversed(list(Severity))
    )
    hidden = f", {len(report.suppressed)} suppressed" if report.suppressed else ""
    return (
        f"airlock: {tally}{hidden} · {report.files_scanned} file(s) scanned, "
        f"{skipped_phrase(report)}"
    )
