"""Contributor-facing command consistency (issue #103).

AGENTS.md, CONTRIBUTING.md and SUPPORT.md are what a contributor reads before opening a pull
request (SUPPORT.md section "Read before you open a pull request"). Two properties broke on a
current Debian or Ubuntu Python: the self-scan line in AGENTS.md named the module form
(`python -m airlock scan`) while `ci.yml` runs the installed console script, and several commands
across all three documents named the bare `python` interpreter, which does not exist there (only
`python3` does). Both are guarded here against `ci.yml` and against each other, so a future edit
that reintroduces either drifts in a test rather than in a contributor's terminal.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
CONTRIBUTOR_DOCS = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / "SUPPORT.md",
)

# A bare `python` command: not `python3`, and not the capitalized prose name ("Python 3.11").
BARE_PYTHON = re.compile(r"(?<![A-Za-z3])python(?![A-Za-z3])")


def _self_scan_command() -> str:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"Self-scan\n\s*run:\s*(.+)", text)
    assert match, "ci.yml has no 'Self-scan' step to read the authoritative command from"
    return match.group(1).strip()


def test_ci_self_scan_command_is_the_installed_console_script() -> None:
    # The wheel-and-rule-data reason this must be the console script and not `python3 -m airlock`
    # is the comment directly above the step in ci.yml; this test only pins the command string.
    assert _self_scan_command() == "airlock scan --mode full ."


def test_contributor_docs_name_the_same_self_scan_command_as_ci() -> None:
    command = _self_scan_command()
    for doc in CONTRIBUTOR_DOCS:
        text = doc.read_text(encoding="utf-8")
        assert command in text, (
            f"{doc.name} does not name ci.yml's self-scan command ({command!r} not found)"
        )


def test_contributor_docs_use_python3_not_python() -> None:
    for doc in CONTRIBUTOR_DOCS:
        text = doc.read_text(encoding="utf-8")
        bare = BARE_PYTHON.findall(text)
        assert not bare, (
            f"{doc.name} names the bare `python` interpreter {len(bare)} time(s); "
            "a PEP 668 system may only have `python3`"
        )


def _dev_group_pins() -> dict[str, str]:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^dev = \[(.*?)\]", text, re.MULTILINE)
    assert match, "pyproject.toml has no [dependency-groups] dev list"
    pins = re.findall(r'"([A-Za-z0-9_-]+)>=([^"]+)"', match.group(1))
    return dict(pins)


def test_fallback_pins_match_the_dev_dependency_group() -> None:
    # The pipx/venv fallback pins by hand what `uv run --group dev` reads from pyproject.toml, so a
    # Dependabot bump of the group must not leave the documented fallback on an older floor.
    pins = _dev_group_pins()
    for doc in CONTRIBUTOR_DOCS:
        text = doc.read_text(encoding="utf-8")
        for name, version in re.findall(r'"(pytest|ruff|mypy)>=([^"]+)"', text):
            assert pins.get(name) == version, (
                f"{doc.name} pins {name}>={version} but pyproject.toml's dev group pins "
                f"{name}>={pins.get(name)}"
            )
