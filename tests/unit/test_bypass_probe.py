"""The `--script` contract of `scripts/bypass_probe.py` (task 3.9).

The probe exists to measure the external scanner, and the Appendix B regressions reuse its case
data and its repository builder. This module keeps both halves honest after the split: `build`
must leave the scanner to `main`, so the shared builder stays usable by tests that run this
package instead, and `main` must still walk all seven cases and decide on the exit codes it
observes from whatever it was pointed at.

The scanner here is a stub whose only job is to exit. The real script is never committed, so the
stub proves the plumbing rather than the historical result; the historical result is in
`PRD.md` Appendix B and in the probe's own docstring.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import bypass_probe

STUB = "import sys\n\nsys.exit({code})\n"


def stub_scanner(tmp_path: Path, code: int) -> Path:
    path = tmp_path / f"scanner-{code}.py"
    path.write_text(STUB.format(code=code), encoding="utf-8")
    return path


def test_build_leaves_the_scanner_to_the_probe(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    bypass_probe.build(repo, bypass_probe.CASES[0].files)

    assert not (repo / ".github").exists()
    tracked = subprocess.run(
        ["git", "-C", str(repo), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split()
    assert sorted(tracked) == ["contract.wasm", "index.js"]


def test_a_permissive_scanner_confirms_every_case(tmp_path: Path, capsys) -> None:
    assert bypass_probe.main(["--script", str(stub_scanner(tmp_path, 0))]) == 0
    assert "7 of 7 cases bypass" in capsys.readouterr().out


def test_a_strict_scanner_refutes_every_case(tmp_path: Path, capsys) -> None:
    assert bypass_probe.main(["--script", str(stub_scanner(tmp_path, 1))]) == 1
    assert "0 of 7 cases bypass" in capsys.readouterr().out


def test_a_missing_script_is_a_usage_error(tmp_path: Path, capsys) -> None:
    assert bypass_probe.main(["--script", str(tmp_path / "absent.py")]) == 2
    assert "no script at" in capsys.readouterr().err
