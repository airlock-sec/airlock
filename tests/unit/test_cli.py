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


def test_detector_registry_is_empty_and_immutable() -> None:
    # Populated by tasks 3.1, 3.4 and 3.6. A scan over an empty registry is a config error.
    assert detectors.DETECTORS == ()
    assert isinstance(detectors.DETECTORS, tuple)


@pytest.mark.parametrize(
    "module",
    ["cli", "model", "collector", "roles", "rules", "fingerprint", "policy", "runner", "strkey"],
)
def test_every_core_module_is_importable(module: str) -> None:
    __import__(f"airlock.{module}")
