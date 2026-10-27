"""Fingerprint and occurrence-numbering tests (task 2.6)."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from airlock.fingerprint import (
    MAX_EVIDENCE_CHARS,
    PendingFinding,
    fingerprint,
    normalize_evidence,
    number_occurrences,
    truncate_evidence,
)
from airlock.model import FINGERPRINT_PREFIX, Severity

SAME_LINE = "eval(Buffer.from(payload, 'base64'))"


def pending(
    rule_id: str = "cfg-dynamic-code",
    path: str = "postcss.config.mjs",
    line: int = 7,
    evidence: str | None = SAME_LINE,
    file_sha256: str | None = None,
    severity: Severity = Severity.HIGH,
    suppressible: bool = False,
) -> PendingFinding:
    return PendingFinding(
        rule_id=rule_id,
        severity=severity,
        path=path,
        line=line,
        roles=("tooling-config",),
        message="remote code execution capability in a tooling config",
        evidence=evidence,
        suppressible=suppressible,
        file_sha256=file_sha256,
    )


class TestNormalization:
    def test_whitespace_runs_collapse_and_edges_are_stripped(self) -> None:
        assert normalize_evidence("  eval(  x )\t\n") == "eval( x )"
        assert normalize_evidence(None) == ""

    def test_indentation_alone_does_not_change_a_fingerprint(self) -> None:
        assert (
            pending(evidence="    eval(x)").evidence_key()
            == pending(evidence="eval(x)").evidence_key()
        )

    def test_evidence_is_capped_before_storage(self) -> None:
        capped = truncate_evidence("a" * 5000)
        assert capped is not None
        assert len(capped) == MAX_EVIDENCE_CHARS + 3
        assert capped.endswith("...")

    def test_truncation_only_removes_line_endings(self) -> None:
        # Display text keeps its indentation; normalization for the key is a separate step.
        assert truncate_evidence("  eval(x)\r\n") == "  eval(x)"
        assert truncate_evidence(None) is None


class TestFingerprintFormula:
    def test_matches_the_documented_formula(self) -> None:
        expected = hashlib.sha256(
            b"cfg-dynamic-code\x00postcss.config.mjs\x00eval(x)\x000"
        ).hexdigest()
        assert fingerprint("cfg-dynamic-code", "postcss.config.mjs", "eval(x)", 0) == (
            FINGERPRINT_PREFIX + expected
        )

    def test_line_numbers_do_not_enter_the_fingerprint(self) -> None:
        first = number_occurrences([pending(line=7)])[0]
        moved = number_occurrences([pending(line=41)])[0]
        assert first.fingerprint == moved.fingerprint

    def test_a_different_rule_on_the_same_line_is_a_different_fingerprint(self) -> None:
        a = number_occurrences([pending(rule_id="cfg-dynamic-code")])[0]
        b = number_occurrences([pending(rule_id="cfg-network")])[0]
        assert a.fingerprint != b.fingerprint

    def test_a_different_file_is_a_different_fingerprint(self) -> None:
        a = number_occurrences([pending(path="postcss.config.mjs")])[0]
        b = number_occurrences([pending(path="tailwind.config.mjs")])[0]
        assert a.fingerprint != b.fingerprint


class TestEvidenceKey:
    def test_file_level_findings_hash_on_the_file(self) -> None:
        digest = "ab" * 32
        item = pending(evidence=None, file_sha256=digest)
        assert item.evidence_key() == digest

    def test_a_state_finding_keys_on_its_message(self) -> None:
        item = pending(evidence=None, file_sha256=None)
        assert item.evidence_key() == normalize_evidence(item.message)

    def test_a_state_finding_with_a_different_message_keys_differently(self) -> None:
        # Two `policy-changed` states in one file must not collapse onto one fingerprint, or one
        # occurrence index would cover both.
        base = pending(rule_id="policy-changed", evidence=None)
        other = replace(base, message="wasm-manifest.toml was added by this change")
        assert base.evidence_key() != other.evidence_key()

    def test_nothing_to_key_on_is_an_error(self) -> None:
        item = pending(evidence=None, file_sha256=None)
        empty = replace(item, message="   ")
        with pytest.raises(ValueError, match="no evidence, no file sha256 and no message"):
            empty.evidence_key()


class TestOccurrences:
    def test_a_repeated_line_gets_the_next_index(self) -> None:
        findings = number_occurrences([pending(), pending()])
        assert [f.occurrence for f in findings] == [0, 1]
        assert findings[0].fingerprint != findings[1].fingerprint

    def test_numbering_is_independent_of_detector_order(self) -> None:
        a, b = pending(line=3), pending(line=9)
        assert number_occurrences([a, b]) == number_occurrences([b, a])

    def test_distinct_evidence_in_the_same_file_never_collides(self) -> None:
        findings = number_occurrences(
            [pending(line=1, evidence="eval(x)"), pending(line=2, evidence="eval(y)")]
        )
        assert [f.occurrence for f in findings] == [0, 0]

    def test_output_is_severity_descending_then_path_line_rule(self) -> None:
        findings = number_occurrences(
            [
                pending(rule_id="cfg-network", severity=Severity.WARN, suppressible=True, line=2),
                pending(rule_id="cfg-dynamic-code", line=1),
                pending(rule_id="cfg-nul", path="z.config.mjs", severity=Severity.INFO, line=1),
            ]
        )
        assert [(f.severity, f.path, f.line) for f in findings] == [
            (Severity.HIGH, "postcss.config.mjs", 1),
            (Severity.WARN, "postcss.config.mjs", 2),
            (Severity.INFO, "z.config.mjs", 1),
        ]


class TestFindingShape:
    def test_to_finding_carries_every_detectors_field(self) -> None:
        finding = pending().to_finding(0)
        assert finding.rule_id == "cfg-dynamic-code"
        assert finding.roles == ("tooling-config",)
        assert finding.suppressible is False
        assert finding.suppressed_by is None
        assert finding.evidence == SAME_LINE

    def test_with_evidence_returns_a_copy_and_truncates(self) -> None:
        original = pending(evidence="eval(x)")
        copy = original.with_evidence("y" * 400)
        assert copy.evidence is not None
        assert len(copy.evidence) == MAX_EVIDENCE_CHARS + 3
        assert original.evidence == "eval(x)"
        assert copy.rule_id == original.rule_id
        assert copy.file_sha256 == original.file_sha256
