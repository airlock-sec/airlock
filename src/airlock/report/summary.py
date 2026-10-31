"""Step-summary reporter (task 2.9, 7.13, `ARCHITECTURE.md` 6.6).

Markdown for `$GITHUB_STEP_SUMMARY`: the counts, the skip accounting, every HIGH finding and the
evidence under each one. Every HIGH is listed because this is the output a reviewer actually
reads, and B8 is the failure it prevents: a flood of WARNs must not push a HIGH out of sight, so
WARNs are counted here and never enumerated.

Evidence and paths are attacker-controlled text (B11). Evidence only ever appears inside a fenced
block whose fence is longer than the longest backtick run anywhere in the rendered text, which is
what stops ``` inside a filename or a line of code from closing the block and handing the rest of
the summary to markdown. Everything outside a fence is flattened and has its markup characters
escaped, so a file called `**Deploy** [x](https://…)` renders as that string and nothing else.

The whole document is also budgeted (task 7.13): GitHub drops a step summary over 1 MiB without
failing the step, so a HIGH count large enough to pass that ceiling used to delete the reviewer's
copy of the findings silently. `SUMMARY_BYTE_BUDGET` keeps the rendered document under that, and
`render` degrades in a fixed order when it would not otherwise fit: every HIGH's row (severity,
rule, path and line) is kept first, evidence blocks are added from what budget is left and are the
first thing dropped, and only a row count that alone exceeds the budget caps the list itself, each
loss named in a note rather than left silent.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..model import Finding, ScanReport, Severity

#: The summary is size-limited by GitHub, so evidence is shorter here than in the JSON.
SUMMARY_EVIDENCE_CHARS = 200

#: Half of GitHub's documented 1 MiB step-summary ceiling (`ARCHITECTURE.md` 6.6, task 0.9).
#: The hosted probe found a 1,048,577-byte summary rejected outright and a 1,048,000-byte one
#: hang past a 10-minute timeout before being cancelled, which 6.6 calls the worse of the two
#: failures, so the margin clears both observed failure points rather than only the documented
#: figure.
SUMMARY_BYTE_BUDGET = 1024 * 1024 // 2

#: Reserved out of the budget for the withheld-row and withheld-evidence notes, so adding either
#: one never pushes the finished document over `SUMMARY_BYTE_BUDGET`. Generous for the longest
#: realistic finding count; see `_withheld_rows_note` and `_withheld_evidence_note`.
_NOTE_RESERVE_BYTES = 600

#: `#` and `-` are deliberately absent: they only take effect at the start of a line, and no
#: attacker-controlled text is ever placed there (rows start with a pipe, bullets with a dash).
#: Escaping them would turn every rule id into `cfg\-dynamic\-code` for no safety gain.
_MARKUP_RE = re.compile(r"([\\`*_\[\]|<>])")
_BACKTICK_RUN_RE = re.compile(r"`+")


def flatten(text: str) -> str:
    """No newline survives: one finding must not become two rows or a stray heading."""
    return " ".join(text.split())


def inline(text: str) -> str:
    """Render attacker-controlled text as escaped inline content, not as markup."""
    return _MARKUP_RE.sub(r"\\\1", flatten(text))


def truncated(evidence: str | None) -> str:
    if evidence is None:
        return ""
    cleaned = flatten(evidence)
    if len(cleaned) <= SUMMARY_EVIDENCE_CHARS:
        return cleaned
    return cleaned[:SUMMARY_EVIDENCE_CHARS] + " ..."


def fence_for(texts: Iterable[str]) -> str:
    """A fence longer than any backtick run in the texts, so nothing can break out of it.

    Three is the ordinary markdown fence; the length is computed over the content that goes
    inside, so a payload of twelve backticks gets thirteen.
    """
    longest = max(
        (len(run) for text in texts for run in _BACKTICK_RUN_RE.findall(text)),
        default=0,
    )
    return "`" * max(3, longest + 1)


def location(finding: Finding) -> str:
    path = inline(finding.path)
    return f"{path}:{finding.line}" if finding.line else path


def count_phrase(report: ScanReport) -> str:
    counts = {severity: 0 for severity in Severity}
    for finding in report.findings:
        counts[finding.severity] += 1
    parts = [
        f"{counts[severity]} {severity.label.upper()}" for severity in reversed(list(Severity))
    ]
    if report.suppressed:
        parts.append(f"{len(report.suppressed)} suppressed")
    return " · ".join(parts)


def skipped_section(report: ScanReport) -> list[str]:
    if not report.files_skipped:
        return ["No file was skipped."]
    rows = [
        f"| {inline(reason)} | {count} |" for reason, count in sorted(report.files_skipped.items())
    ]
    return ["| Skip reason | Files |", "|---|---|", *rows]


def finding_rows(findings: tuple[Finding, ...]) -> list[str]:
    rows = [
        f"| {finding.severity.label.upper()} | {inline(finding.rule_id)} | {location(finding)}"
        f" | {inline(finding.message)} |"
        for finding in findings
    ]
    if not rows:
        return ["No HIGH finding."]
    return rows


def _line_bytes(line: str) -> int:
    """Bytes `line` adds to the final document: its UTF-8 length plus its line separator.

    Summed over every line this equals ``len(("\\n".join(lines) + "\\n").encode("utf-8"))``, so a
    running total tracked with this is exactly the size of the document that total belongs to.
    """
    return len(line.encode("utf-8")) + 1


def _lines_bytes(lines: Iterable[str]) -> int:
    return sum(_line_bytes(line) for line in lines)


def _budget_rows(rows: list[str], budget: int) -> tuple[list[str], int]:
    """Keep as many rows as fit in `budget`; every later one is counted, not rendered."""
    kept: list[str] = []
    used = 0
    for row in rows:
        cost = _line_bytes(row)
        if used + cost > budget:
            break
        kept.append(row)
        used += cost
    return kept, len(rows) - len(kept)


def _withheld_rows_note(count: int) -> str:
    return (
        f"{count} more HIGH finding(s) are not listed above; "
        "run `airlock scan --format json` for the complete list."
    )


def _withheld_evidence_note(count: int) -> str:
    return (
        f"Evidence for {count} HIGH finding(s) above is not shown to stay inside the step "
        "summary's size budget; run `airlock scan --format json` for the complete list "
        "with evidence."
    )


def _budgeted_evidence_blocks(findings: tuple[Finding, ...], budget: int) -> tuple[list[str], int]:
    """Evidence blocks for `findings` that fit in `budget`; the rest are counted, not rendered.

    Blocks are added whole or not at all, never cut mid-block, so a truncated document still
    closes every fence it opens.
    """
    excerpted = [(finding, truncated(finding.evidence)) for finding in findings if finding.evidence]
    if not excerpted:
        return [], 0
    fence = fence_for([excerpt for _, excerpt in excerpted])
    header = ["", "### Evidence", ""]
    lines = list(header)
    used = _lines_bytes(header)
    kept = 0
    for finding, excerpt in excerpted:
        block = [f"- {location(finding)}", fence, excerpt, fence, ""]
        cost = _lines_bytes(block)
        if used + cost > budget:
            break
        lines += block
        used += cost
        kept += 1
    return (lines if kept else []), len(excerpted) - kept


def render(report: ScanReport) -> str:
    """The whole summary as one Markdown document, kept under `SUMMARY_BYTE_BUDGET`.

    Every HIGH's row is prioritised over its evidence: evidence is added from whatever budget
    remains after every row is kept, and is the first thing dropped when the budget runs out.
    Only a row count that alone exceeds the budget caps the list itself.
    """
    highs = tuple(finding for finding in report.findings if finding.severity is Severity.HIGH)
    header = [
        "# Airlock",
        "",
        f"{count_phrase(report)} · {report.files_scanned} file(s) scanned",
        "",
        "## Skipped files",
        "",
        *skipped_section(report),
        "",
        "## HIGH findings",
        "",
        "| Severity | Rule | Location | Message |",
        "|---|---|---|---|",
    ]
    footer = [
        "",
        f"Mode `{inline(report.mode.value)}` · exit {report.exit_code}"
        f" · airlock {inline(report.tool_version)}",
    ]
    content_budget = (
        SUMMARY_BYTE_BUDGET - _lines_bytes(header) - _lines_bytes(footer) - _NOTE_RESERVE_BYTES
    )

    kept_rows, dropped_rows = _budget_rows(finding_rows(highs), content_budget)
    content_budget -= _lines_bytes(kept_rows)
    shown = highs[: len(kept_rows)] if dropped_rows else highs

    evidence_lines, withheld_evidence = _budgeted_evidence_blocks(shown, max(content_budget, 0))

    notes: list[str] = []
    if dropped_rows:
        notes += ["", _withheld_rows_note(dropped_rows)]
    if withheld_evidence:
        notes += ["", _withheld_evidence_note(withheld_evidence)]

    lines = [*header, *kept_rows, *evidence_lines, *notes, *footer]
    return "\n".join(lines) + "\n"
