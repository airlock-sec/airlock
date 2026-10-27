"""The unbuilt CLI must not look like a passing scan (AGENTS.md 4: never exit 0 after an error)."""

from __future__ import annotations

import pytest

from airlock import detectors
from airlock.cli import main
from airlock.model import EXIT_CONFIG, EXIT_PASS


def test_scan_entry_point_exits_config_error_until_the_engine_exists() -> None:
    assert main([]) == EXIT_CONFIG
    assert main() == EXIT_CONFIG


def test_cli_exit_code_is_never_the_pass_code() -> None:
    assert main([]) != EXIT_PASS


def test_every_registered_detector_is_callable_and_named() -> None:
    # A rule file may only point at a name in DETECTOR_NAMES, so the two lists drifting is a
    # config error the loader catches, not a detector that silently never runs.
    assert isinstance(detectors.DETECTORS, tuple)
    assert detectors.DETECTORS
    assert all(callable(detector) for detector in detectors.DETECTORS)
    assert len(detectors.DETECTOR_NAMES) == len(detectors.DETECTORS)


@pytest.mark.parametrize(
    "module",
    ["cli", "model", "collector", "roles", "rules", "fingerprint", "policy", "runner", "strkey"],
)
def test_every_core_module_is_importable(module: str) -> None:
    __import__(f"airlock.{module}")
