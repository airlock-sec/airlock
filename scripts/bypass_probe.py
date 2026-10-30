#!/usr/bin/env python3
"""Roadmap 0.4: prove or refute the seven bypass cases in `PRD.md` Appendix B.

This runs the *existing* in-repo gate (`.github/scripts/malware_scan.py`, copied into a scratch
repository the way a real repository holds it) against each case and reports the exit code. Exit
code 0 on a case that should fail is a confirmed bypass, which is what section 2.3 claims.

Nothing here is an Airlock test. Airlock's own fail-closed regressions for the same seven shapes
live in `tests/bypass/` (task 3.9), and those are the ones that run in CI. This probe exists
because the claim about somebody else's scanner should be measured, not reviewed: section 2.3 was
written from reading the script, and the difference between a confirmed and a suspected weakness
decides how much of the P0 rule set is actually new ground.

The script under test is never copied into this repository, so the trigger strings it is fed stay
in memory under a temporary directory. The payloads are assembled from fragments at run time for
the same reason `tests/fixtures/` assembles them (task 3.2).

Usage:

    python3 scripts/bypass_probe.py --script /path/to/malware_scan.py

Stdlib only, Python 3.11+, no network. The scanner is run with the current interpreter from the
repository root, which is how the workflow runs it.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _join(*parts: str) -> str:
    return "".join(parts)


EVAL = _join("ev", "al")
BUFFER_FROM = _join("Buffer", ".from")
B64_PAYLOAD = f"{EVAL}({BUFFER_FROM}(a,'base64'))"

ALLOW_MARKER = "malware-scan: allow"

WASM_MAGIC = b"\x00asm\x01\x00\x00\x00"


@dataclass(frozen=True, slots=True)
class Case:
    """One Appendix B shape, with the line of the old script that lets it through."""

    num: int
    name: str
    claim: str
    files: dict[str, bytes]


CASES: tuple[Case, ...] = (
    Case(
        1,
        "wasm-any-content",
        "a `.wasm` file of any content",
        {"contract.wasm": WASM_MAGIC + B64_PAYLOAD.encode() + b"\n"},
    ),
    Case(
        2,
        "nul-in-text",
        "a NUL byte in the first 4 KB of a text file",
        {"next.config.mjs": b"// \x00\n" + f"{EVAL}(x)\n".encode()},
    ),
    Case(
        3,
        "inline-allow-marker",
        f"a payload line ending in `{ALLOW_MARKER}`",
        {"loader.js": f"{B64_PAYLOAD} // {ALLOW_MARKER} reviewed\n".encode()},
    ),
    Case(
        4,
        "allowlist-wildcard",
        "an allowlist file containing a single `*`",
        {
            ".github/malware-scan-allow.txt": b"*\n",
            "loader.js": f"{B64_PAYLOAD}\n".encode(),
        },
    ),
    Case(
        5,
        "decode-then-eval",
        f"`{EVAL}(decrypted)` inside a tooling config",
        {
            "postcss.config.mjs": (
                f"const decoder = globalThis[{EVAL}];\n{EVAL}(decrypted);\n"
            ).encode()
        },
    ),
    Case(
        6,
        "cargo-runner",
        "a `.cargo/config.toml` with a `runner` that invokes a shell",
        {".cargo/config.toml": b'[build]\nrunner = ["sh", "-c", "cargo run -- $@"]\n'},
    ),
    Case(
        7,
        "skipped-directory",
        "a payload under a directory the script skips by name",
        {"vendor/thing/loader.js": f"{B64_PAYLOAD}\n".encode()},
    ),
)


def build(repo: Path, files: dict[str, bytes]) -> None:
    """Create a committed scratch repository holding one payload.

    The scanner under test is not part of the repository this builds: this is the shared half, and
    `install_script` is the probe's own step (`tests/bypass/` points the same shapes at this
    package instead).
    """
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "bypass-probe"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "bypass-probe@localhost"], cwd=repo, check=True)

    (repo / "index.js").write_text("module.exports = {};\n", encoding="utf-8")
    commit(repo, "base: clean tree")

    for name, data in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    commit(repo, "case under test")


def install_script(repo: Path, script: Path) -> None:
    """Copy the external scanner in the way a real repository holds it, then commit it."""
    destination = repo / ".github" / "scripts" / "malware_scan.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(script.read_bytes())
    commit(repo, "vendor: the scanner under test")


def commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=repo, check=True)


def scan(repo: Path) -> tuple[int, str]:
    """Run the script the way the workflow does: from the root, no arguments."""
    result = subprocess.run(
        [sys.executable, "-I", ".github/scripts/malware_scan.py"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def still_parses(repo: Path, name: str) -> str:
    """Appendix B case 2 claims the file Node still accepts. Check, do not execute.

    `node --check` parses without running anything, which is the whole point: Airlock never
    executes scanned content, and this probe does not start.
    """
    node = shutil.which("node")
    if node is None:
        return "node not available: parse check skipped"
    result = subprocess.run([node, "--check", name], cwd=repo, capture_output=True, text=True)
    if result.returncode == 0:
        return "node --check accepts it"
    return f"node --check rejects it: {result.stderr.strip().splitlines()[:1]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--script",
        type=Path,
        required=True,
        help="path to the malware_scan.py under test (never committed here)",
    )
    args = parser.parse_args(argv)

    script: Path = args.script.resolve()
    if not script.is_file():
        print(f"bypass probe: no script at {script}", file=sys.stderr)
        return 2

    confirmed = 0
    for case in CASES:
        with tempfile.TemporaryDirectory(prefix="airlock-bypass-") as tmp:
            repo = Path(tmp)
            build(repo, case.files)
            install_script(repo, script)
            code, output = scan(repo)
            note = ""
            if case.num == 2:
                note = " | " + still_parses(repo, "next.config.mjs")
        bypassed = code == 0
        confirmed += bypassed
        verdict = "BYPASS CONFIRMED" if bypassed else "caught"
        tail = output.splitlines()[-1] if output else "no output"
        print(f"B{case.num} {verdict:17} exit={code}  {case.claim}{note}")
        print(f"   | {tail}")

    print()
    print(f"{confirmed} of {len(CASES)} cases bypass the existing gate (exit 0).")
    print(
        "PRD.md 2.3 is confirmed where all seven are bypassed; a caught case refutes that line "
        "and should be corrected rather than rounded up."
    )
    return 0 if confirmed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
