"""`PRD.md` Appendix B case 5: `eval(decrypted)` inside a tooling config (task 3.9).

This is the PolinRider shape: a payload appended to a build config that joins and evaluates a
decoded string. The old script scored it one WARN where only HIGH affects its exit code, so the
gate passed with the payload running. Airlock's `cfg-dynamic-code` is HIGH and not suppressible,
and this case pins both the id and the tier.

The scan runs in `--mode full`; `conftest.py` says why.
"""

from __future__ import annotations

from airlock.model import EXIT_FINDINGS


def test_eval_in_a_tooling_config_is_a_high(scan, verdict) -> None:
    report = scan(5)

    assert report.exit_code == EXIT_FINDINGS
    assert verdict(report) == [("cfg-dynamic-code", "HIGH")]
