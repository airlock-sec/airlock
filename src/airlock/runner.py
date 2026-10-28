"""Detector orchestration. Task 2.11 (`ARCHITECTURE.md` 6.3).

Two passes make up a scan:

1. The engine pass, over every file the collector returned text for. It runs the `pattern` rules
   and reports the lines `line_cap` withheld from any regex. It is code, not a detector, because
   a withheld line must be accounted for whatever else is registered: an empty or partial
   detector list may reduce what is matched, never what is reported.
2. The registered detectors, in registry order. Each yields pending findings; a detector that
   raises becomes one HIGH `detector-error` and the remaining detectors still run.

`number_occurrences` then assigns occurrence indices and sorts, so the same set of findings
always produces the same fingerprints and the same report order.

Suppression is applied by the caller (`cli.run_scan`), because it needs the trusted policy,
which is not part of this module.
"""

from __future__ import annotations

from .detectors import DETECTORS, Detector
from .fingerprint import PendingFinding, number_occurrences
from .model import MAX_MESSAGE_CHARS, REPO_PATH, Finding, ScanContext, Severity
from .rules import apply_patterns, cap_findings

DETECTOR_ERROR_RULE_ID = "detector-error"


def engine_findings(ctx: ScanContext) -> tuple[PendingFinding, ...]:
    """Run the pattern rules and the line-cap account over every entry with text."""
    pending: list[PendingFinding] = []
    for entry in ctx.entries:
        pending.extend(apply_patterns(ctx.rules, entry, ctx.policy.line_cap))
        pending.extend(cap_findings(ctx.rules, entry, ctx.policy.line_cap))
    return tuple(pending)


def _detector_error(detector: Detector, error: BaseException) -> PendingFinding:
    """A detector that raised is a HIGH finding, never a silent gap in coverage."""
    name = getattr(detector, "__module__", repr(detector))
    detail = f"{name}: {type(error).__name__}: {error}"
    return PendingFinding(
        rule_id=DETECTOR_ERROR_RULE_ID,
        severity=Severity.HIGH,
        path=REPO_PATH,
        line=0,
        roles=(),
        message=(
            "A detector raised and its coverage is missing from this scan: "
            + detail[:MAX_MESSAGE_CHARS]
        ),
        # The detail is the evidence, so two failures of one detector on one commit collapse to
        # one fingerprint while a different exception stays a new finding.
        evidence=detail[:MAX_MESSAGE_CHARS],
        suppressible=False,
    )


def _run_one(detector: Detector, ctx: ScanContext) -> tuple[PendingFinding, ...]:
    """Run one detector and catch anything it raises.

    Findings yielded before the failure are kept: a scan that reports the coverage gap and the
    partial result is more useful than one that throws away both. The loop is inside the `try`,
    because a generator that fails on its tenth file would otherwise escape the wrapper.
    """
    collected: list[PendingFinding] = []
    try:
        for item in detector(ctx):
            collected.append(item)
    except Exception as error:
        collected.append(_detector_error(detector, error))
    return tuple(collected)


def collect(ctx: ScanContext) -> tuple[PendingFinding, ...]:
    """Every pending finding from the engine pass and the detectors, in dispatch order."""
    pending: list[PendingFinding] = list(engine_findings(ctx))
    for detector in DETECTORS:
        pending.extend(_run_one(detector, ctx))
    return tuple(pending)


def scan(ctx: ScanContext) -> list[Finding]:
    """Run the scan and return findings in report order (HIGH first)."""
    return number_occurrences(collect(ctx))
