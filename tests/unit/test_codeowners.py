"""CODEOWNERS coverage of the trust-model modules (issue #100).

`.github/CODEOWNERS` is hand-written, not generated, so nothing else checks that a module
carrying the trust model stays listed there. This asserts the coverage directly: the four
modules named in the issue plus the report package, the bypass regressions that the issue
asks for a decision on, and that adding those lines did not shadow a path that was already
owned (`later rules win over earlier ones`, per the file's own header).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CODEOWNERS_PATH = REPO_ROOT / ".github" / "CODEOWNERS"

Entry = tuple[str, tuple[str, ...]]


def _entries() -> list[Entry]:
    entries: list[Entry] = []
    for raw in CODEOWNERS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *owners = line.split()
        entries.append((pattern, tuple(owners)))
    return entries


def _owner_of(entries: list[Entry], path: str) -> tuple[str, ...] | None:
    """The owners of `path` under GitHub's rule: the last matching line wins."""
    owner: tuple[str, ...] | None = None
    for pattern, owners in entries:
        matches = path.startswith(pattern) if pattern.endswith("/") else path == pattern
        if matches:
            owner = owners
    return owner


class TestTrustModulesAreCovered:
    """Acceptance criterion 1 and 2: the four modules and `report/` are owned."""

    def test_fingerprint_module_is_owned(self) -> None:
        assert _owner_of(_entries(), "/src/airlock/fingerprint.py") == ("@Gabbydunkk",)

    def test_model_module_is_owned(self) -> None:
        assert _owner_of(_entries(), "/src/airlock/model.py") == ("@Gabbydunkk",)

    def test_roles_module_is_owned(self) -> None:
        assert _owner_of(_entries(), "/src/airlock/roles.py") == ("@Gabbydunkk",)

    def test_report_package_is_owned(self) -> None:
        assert _owner_of(_entries(), "/src/airlock/report/github.py") == ("@Gabbydunkk",)

    def test_cli_module_is_owned(self) -> None:
        assert _owner_of(_entries(), "/src/airlock/cli.py") == ("@Gabbydunkk",)


class TestOrderingDidNotUnseatAnExistingLine:
    """Acceptance criterion 3: no path that was owned became unowned."""

    def test_previously_owned_specific_files_are_still_owned(self) -> None:
        entries = _entries()
        previously_owned = [
            "/scripts/roadmap_progress.py",
            "/rules/roles.toml",
            "/src/airlock/detectors/__init__.py",
            "/src/airlock/policy.py",
            "/src/airlock/collector.py",
            "/src/airlock/runner.py",
            "/airlock.toml",
            "/wasm-manifest.toml",
            "/action.yml",
            "/.github/workflows/ci.yml",
            "/pyproject.toml",
            "/.github/CODEOWNERS",
        ]
        for path in previously_owned:
            assert _owner_of(entries, path) == ("@Gabbydunkk",), path

    def test_new_module_lines_do_not_widen_into_a_directory(self) -> None:
        """A bare `/src/airlock/` line would also satisfy criterion 1; the issue rules it out
        because `policy.py` and `detectors/` are already owned at finer granularity."""
        entries = _entries()
        assert ("/src/airlock/", ("@Gabbydunkk",)) not in entries


class TestBypassRegressionsDecision:
    """Acceptance criterion 4: `tests/` gets a decision, not silence.

    A bypass regression under `tests/bypass/` is the test that a confirmed supply-chain
    bypass stays closed; weakening or deleting one is as security-relevant as weakening a
    rule, so it is owner-reviewed. Ordinary unit tests and fixtures are not swept in: the
    normal "one positive and one negative fixture per rule" workflow (`AGENTS.md` 7) would
    otherwise need owner review on every rule PR in addition to the `rules/` line it already
    triggers.
    """

    def test_a_bypass_regression_is_owner_reviewed(self) -> None:
        entries = _entries()
        owner = _owner_of(entries, "/tests/bypass/test_bypass_6_cargo_runner.py")
        assert owner == ("@Gabbydunkk",)

    def test_ordinary_unit_tests_are_not_owner_reviewed(self) -> None:
        entries = _entries()
        assert _owner_of(entries, "/tests/unit/test_cli.py") is None

    def test_fixtures_are_not_owner_reviewed(self) -> None:
        entries = _entries()
        assert _owner_of(entries, "/tests/fixtures/__init__.py") is None
